"""Wave 2 Native OFF cold-start and dependency-boundary checks for N08.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED

These tests can prove the observable engineering boundary: production imports
are stdlib/internal, the CLI starts with a reduced environment, forged caller
inputs do not bind trust, and the only child process in the direct source tree
is the explicit OS ACL query. They do not prove the absence of every dynamic
or transitive route, so the true Native/OPS run remains NOT_VERIFIED here.
"""

from __future__ import annotations

import ast
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from b0_reader import cli
from tests.trust_fixture import IsolatedProductHarness, raw_baseline


DEV_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = DEV_ROOT.parent
PACKAGE_ROOT = DEV_ROOT / "b0_reader"
TEST_TEMP_ROOT = DEV_ROOT / ".tmp_tests"
DESCRIPTOR_PATH = (
    WORKSPACE_ROOT / "00_PREFLIGHT" / "B0_READ_CONTEXT_2026-11-25_r4.json"
)
EXPECTED_DESCRIPTOR_SHA = (
    "b8759ca7f5c213024c4046db07494cabb355d39d051b0082ff043845e9fb45e0"
)
EXPECTED_DESCRIPTOR_BYTES = 3612
NETWORK_MODULES = {
    "aiohttp",
    "asyncio",
    "ftplib",
    "http",
    "requests",
    "smtplib",
    "socket",
    "ssl",
    "urllib",
    "websocket",
    "xmlrpc",
}
FORBIDDEN_TRUST_ENTRY_FRAGMENTS = (
    "environ",
    "getenv",
    "getcwd",
    "cwd",
    "request",
    "--context",
    "--allowed-root",
    "--source",
)


def _valid_request() -> bytes:
    return json.dumps(
        {
            "request_version": "B0ReadRequest/2",
            "subject": "SST/SQS-THC/PH01/E00",
            "original_wave": "P1-W00M",
            "bid": 0,
            "effect": "SOURCE_READ",
            "write_set": [],
            "scope_id": "SQS-THC-PH01-E00-B0-SOURCE-READ",
            "sources": [
                {
                    "source_id": "SST.ALL.W0.BLUEPRINT",
                    "expected_sha": "0" * 64,
                    "clause_span": [572, 579],
                }
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _reduced_environment() -> dict[str, str]:
    environment = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "TEMP": str(TEST_TEMP_ROOT),
        "TMP": str(TEST_TEMP_ROOT),
    }
    for key in ("SystemRoot", "WINDIR"):
        value = os.environ.get(key)
        if value:
            environment[key] = value
    return environment


def _run_cli(
    arguments: list[str],
    *,
    cwd: Path,
    payload: bytes | None = None,
    environment: dict[str, str] | None = None,
    isolated_c_entry: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    if isolated_c_entry:
        boot = (
            "import sys;"
            f"sys.path.insert(0, {str(DEV_ROOT)!r});"
            "from b0_reader.cli import main;"
            "raise SystemExit(main())"
        )
        command = [sys.executable, "-I", "-B", "-c", boot, *arguments]
    else:
        command = [sys.executable, "-B", "-m", "b0_reader.cli", *arguments]
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment or _reduced_environment(),
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
        shell=False,
    )


def _production_import_roots() -> list[str]:
    roots: list[str] = []
    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                roots.append(node.module or "")
    return roots


class NativeOffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertNotIn(
            "TMPDIR",
            os.environ,
            "the bounded suite requires TMPDIR to be unset",
        )
        TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT)
        self.addCleanup(self.temp.cleanup)
        self.forged_cwd = Path(self.temp.name) / "forged-cwd"
        self.forged_cwd.mkdir()
        (self.forged_cwd / "b0_config.json").write_text(
            json.dumps(
                {
                    "allowed_root": str(self.temp.name),
                    "authorized": True,
                    "principal": "forged",
                    "source": str(self.temp.name),
                    "verified": True,
                },
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

    def test_N08_production_import_closure_is_stdlib_or_internal(self) -> None:
        stdlib = set(sys.stdlib_module_names)
        roots = _production_import_roots()
        self.assertTrue(roots)
        rejected = {
            name
            for name in roots
            if name.split(".", 1)[0] not in stdlib
            and name != "b0_reader"
            and not name.startswith("b0_reader.")
        }
        self.assertEqual(rejected, set())
        network = {
            name
            for name in roots
            if name.split(".", 1)[0] in NETWORK_MODULES
        }
        self.assertEqual(network, set())

    def test_N08_help_cold_start_uses_reduced_environment(self) -> None:
        completed = _run_cli(["--help"], cwd=DEV_ROOT)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(b"python -B -m b0_reader.cli", completed.stdout)
        self.assertIn(b"read", completed.stdout)
        self.assertEqual(completed.stderr, b"")

    def test_N08_descriptor_pin_mismatch_fails_closed(self) -> None:
        boot = (
            "import sys;"
            f"sys.path.insert(0, {str(DEV_ROOT)!r});"
            "import b0_reader.native_entry as native_entry;"
            "native_entry.EXPECTED_DESCRIPTOR_SHA = '0' * 64;"
            "from b0_reader.cli import main;"
            "raise SystemExit(main())"
        )
        import os

        environment = os.environ.copy()
        environment.update(
            {
                "PYTHONDONTWRITEBYTECODE": "1",
                "TEMP": str(TEST_TEMP_ROOT),
                "TMP": str(TEST_TEMP_ROOT),
            }
        )
        environment.pop("TMPDIR", None)
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                boot,
                "read",
                "--request-json",
                "-",
            ],
            cwd=DEV_ROOT,
            env=environment,
            input=_valid_request(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
            shell=False,
        )
        self.assertEqual(completed.returncode, 64)
        self.assertEqual(completed.stdout, b"")
        self.assertEqual(completed.stderr, b"TRUST_CONTEXT_UNBOUND")

    def test_N08_forged_env_cwd_and_flags_cannot_authorize(self) -> None:
        harness = IsolatedProductHarness(self)
        harness.add_source("S1", raw_baseline())
        context = harness.resolve()
        payload = json.dumps(
            harness.request(context),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        forged_environment = _reduced_environment()
        forged_environment.update(
            {
                "B0_ALLOWED_ROOT": str(self.temp.name),
                "B0_CONTEXT": str(Path(self.temp.name) / "context.json"),
                "B0_SOURCE": str(Path(self.temp.name) / "source.txt"),
                "PYTHONPATH": str(DEV_ROOT),
            }
        )

        def invoke(environment: dict[str, str]) -> tuple[int, object, str]:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch.dict(os.environ, environment, clear=True), \
                redirect_stdout(stdout), redirect_stderr(stderr):
                code = cli.main(
                    ["read", "--request-json", "-"],
                    stdin=io.BytesIO(payload),
                )
            rendered = json.loads(stdout.getvalue())
            for entry in rendered["entries"]:
                entry["authority"]["checked_at"] = "<NORMALIZED>"
            return code, rendered, stderr.getvalue()

        original_cwd = os.getcwd()
        os.chdir(self.forged_cwd)
        self.addCleanup(os.chdir, original_cwd)
        trusted_invocation = invoke(_reduced_environment())
        forged_invocation = invoke(forged_environment)
        self.assertEqual(trusted_invocation[0], 0)
        self.assertEqual(forged_invocation, trusted_invocation)

        unsupported_flag_variants = (
            ["read", "--request-json", "-", "--context", "forged"],
            ["read", "--request-json", "-", "--allowed-root", str(self.temp.name)],
            ["read", "--request-json", "-", "--source", str(self.temp.name)],
        )
        for arguments in unsupported_flag_variants:
            with self.subTest(arguments=arguments):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    code = cli.main(arguments, stdin=io.BytesIO(payload))
                self.assertEqual(code, 64)
                self.assertEqual(stdout.getvalue(), "")
                self.assertEqual(stderr.getvalue(), "INVOCATION_INVALID")

    def test_N08_fixed_trust_entry_has_no_caller_authority_path(self) -> None:
        path = PACKAGE_ROOT / "native_entry.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        function = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name == "resolve_context_for_current_principal"
            ),
            None,
        )
        self.assertIsNotNone(function)
        source = ast.get_source_segment(
            path.read_text(encoding="utf-8"),
            function,
        )
        self.assertIsNotNone(source)
        for fragment in FORBIDDEN_TRUST_ENTRY_FRAGMENTS:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source.casefold())
        self.assertIn("_read_pinned_descriptor()", source)
        self.assertIn("current_principal()", source)
        self.assertNotIn("EXPECTED_DESCRIPTOR_SHA", source)
        self.assertNotIn("EXPECTED_DESCRIPTOR_BYTES", source)

    def test_N08_child_process_surface_is_explicit_os_acl_only(self) -> None:
        calls: list[ast.Call] = []
        for path in sorted(PACKAGE_ROOT.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "subprocess"
                ):
                    calls.append(node)
        self.assertEqual(len(calls), 1)
        call = calls[0]
        self.assertEqual(call.func.attr, "run")
        command = call.args[0]
        self.assertIsInstance(command, ast.List)
        self.assertEqual(len(command.elts), 2)
        first, second = command.elts
        self.assertIsInstance(first, ast.Constant)
        self.assertEqual(first.value, "icacls")
        self.assertIsInstance(second, ast.Name)
        self.assertEqual(second.id, "path")
        command_items = [first.value, second.id]
        self.assertEqual(command_items, ["icacls", "path"])
        keywords = {
            item.arg: item.value
            for item in call.keywords
            if item.arg is not None
        }
        self.assertIsInstance(keywords["shell"], ast.Constant)
        self.assertIs(keywords["shell"].value, False)


if __name__ == "__main__":
    unittest.main()
