"""Native OFF probe v2 (engineering recorder, not product code).

Fixes the three gaps recorded against the v1 recorder:

1. v1 compared two reduced-environment runs. This version runs a normal baseline
   (full ambient environment) and an isolated OFF run and compares those.
2. v1 swallowed observation failures. Every sampler now reports sampler health
   (observation_ok), and a self-test proves the samplers can see a known child
   process and a known TCP connection before their silence is trusted.
3. Product writes are checked with the same tree snapshot the OPS recorder uses
   (W, recorder outputs excluded, contents hashed) around each run.

What this still cannot prove is listed in not_proven and is never reported as PASS.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

W = Path(r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace")
DEV = W / "20_DEV"
REQ = W / "40_OPS" / "b0_read_request_2026-11-25.json"
OUT = W / "40_OPS"
STRIP_PREFIXES = ("HGK_", "FHS_", "HERMES_", "CODEX_", "OPENAI_", "OPENCODE", "PYTHONPATH")
KEEP_ENV = {
    "SystemRoot", "SYSTEMROOT", "COMSPEC", "PATHEXT", "NUMBER_OF_PROCESSORS",
    "PROCESSOR_ARCHITECTURE", "USERNAME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH",
    "LOCALAPPDATA", "APPDATA", "ProgramData", "windir",
}
ALLOWED_CHILDREN = {"icacls.exe", "icacls", "attrib.exe", "whoami.exe"}


def load_ops_recorder():
    spec = importlib.util.spec_from_file_location("run_ops_r4", OUT / "run_ops_r4.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def normal_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k != "TMPDIR"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["TEMP"] = env["TMP"] = str(DEV / ".tmp_tests")
    return env


def reduced_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k in KEEP_ENV}
    env["PATH"] = str(Path(sys.executable).parent)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["TEMP"] = env["TMP"] = str(DEV / ".tmp_tests")
    return env


class Sampler:
    """Poll child processes and TCP endpoints of one pid and record sampler health."""

    def __init__(self, pid: int, include_loopback: bool = False) -> None:
        self.pid = pid
        self.include_loopback = include_loopback
        self.children: dict[str, str] = {}
        self.tcp: list[str] = []
        self.samples = 0
        self.child_errors = 0
        self.tcp_errors = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _poll_children(self) -> None:
        try:
            out = subprocess.run(
                ["wmic", "process", "where", f"ParentProcessId={self.pid}",
                 "get", "Name,ProcessId", "/format:csv"],
                capture_output=True, encoding="utf-8", errors="replace", timeout=15,
            ).stdout
        except Exception:
            self.child_errors += 1
            return
        for line in out.splitlines():
            parts = [x.strip() for x in line.split(",")]
            if len(parts) >= 3 and parts[2] and parts[2] != "Name":
                self.children[parts[1]] = parts[2]

    def _poll_tcp(self) -> None:
        try:
            raw = subprocess.run(["netstat", "-ano"], capture_output=True, timeout=20).stdout
        except Exception:
            self.tcp_errors += 1
            return
        for line in raw.decode("utf-8", "replace").splitlines():
            stripped = line.strip()
            if not stripped.endswith(str(self.pid)):
                continue
            if not stripped.startswith(("TCP", "UDP")):
                continue
            if not self.include_loopback and ("127.0.0.1" in stripped or "[::1]" in stripped):
                continue
            if stripped not in self.tcp:
                self.tcp.append(stripped)

    def _run(self) -> None:
        while not self._stop.is_set():
            self._poll_children()
            self._poll_tcp()
            self.samples += 1
            time.sleep(0.05)

    def __enter__(self) -> "Sampler":
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    @property
    def observation_ok(self) -> bool:
        return self.samples > 0 and self.child_errors == 0 and self.tcp_errors == 0


def projection(payload: bytes) -> dict:
    try:
        doc = json.loads(payload.decode("utf-8"))
    except Exception:
        return {"error": "unparsable"}
    return {
        "wire_version": doc.get("wire_version"),
        "candidate_digest": doc.get("candidate_digest"),
        "entries": [
            {
                "sid": e["source_ref"]["source_id"],
                "sha": e["sha"],
                "clause": e["clause_sha"],
                "R": e["required_fields"],
                "P": sorted(e["observed"]),
                "M": sorted(m["field"] for m in e["missing"]),
                "value_shas": sorted(v["value_sha"] for v in e["observed"].values()),
            }
            for e in doc.get("entries", [])
        ],
        "errors": [e.get("code") for e in doc.get("errors", [])],
    }


def observer_self_test() -> dict:
    """Prove the samplers can see a known child process and a known connection."""

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]
    probe = (
        "import socket,subprocess,sys,time;"
        "subprocess.Popen([sys.executable,'-c','import time;time.sleep(1.2)']);"
        "time.sleep(0.2);"
        "s=socket.create_connection(('127.0.0.1',{0}),timeout=3);time.sleep(1.0);s.close();"
        "print('PROBE_DONE')"
    ).format(port)
    proc = subprocess.Popen([sys.executable, "-c", probe], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=normal_env())
    try:
        with Sampler(proc.pid, include_loopback=True) as sampler:
            out, _ = proc.communicate()
    finally:
        listener.close()
    return {
        "child_observed": sorted(sampler.children.values()),
        "tcp_observed": len(sampler.tcp),
        "tcp_sample": sampler.tcp[:2],
        "samples": sampler.samples,
        "observation_ok": sampler.observation_ok,
        "sees_child": len(sampler.children) >= 1,
        "sees_tcp": len(sampler.tcp) >= 1,
        "probe_done": b"PROBE_DONE" in out,
    }


def run_cli(env: dict[str, str], request: bytes):
    proc = subprocess.Popen(
        [sys.executable, "-B", "-m", "b0_reader.cli", "read", "--request-json", "-"],
        cwd=str(DEV), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
    )
    with Sampler(proc.pid) as sampler:
        out, err = proc.communicate(request)
    return proc.returncode, out, err, sampler


def main() -> int:
    ops = load_ops_recorder()
    request = REQ.read_bytes()
    (DEV / ".tmp_tests").mkdir(exist_ok=True)

    self_test = observer_self_test()
    observer_trusted = bool(
        self_test["sees_child"] and self_test["sees_tcp"] and self_test["observation_ok"]
    )

    before = ops.tree_snapshot(W, ops.RECORDER_EXCLUDES, hash_contents=True)
    base_exit, base_out, base_err, base_sampler = run_cli(normal_env(), request)
    mid = ops.tree_snapshot(W, ops.RECORDER_EXCLUDES, hash_contents=True)
    off_exit, off_out, off_err, off_sampler = run_cli(reduced_env(), request)
    after = ops.tree_snapshot(W, ops.RECORDER_EXCLUDES, hash_contents=True)

    base_proj, off_proj = projection(base_out), projection(off_out)
    base_writes = ops.diff_snapshots(before, mid)
    off_writes = ops.diff_snapshots(mid, after)
    foreign = {pid: name for pid, name in off_sampler.children.items()
               if name.lower() not in ALLOWED_CHILDREN}

    verified = bool(
        observer_trusted
        and base_sampler.observation_ok and off_sampler.observation_ok
        and base_proj == off_proj and base_proj.get("entries")
        and base_exit == 0 and off_exit == 0
        and not off_sampler.children and not off_sampler.tcp
        and base_writes["clean"] and off_writes["clean"]
    )

    record = {
        "schema": "SST-B0-NATIVE-OFF/2",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "command": {
            "argv": [sys.executable, "-B", "-m", "b0_reader.cli", "read", "--request-json", "-"],
            "cwd": str(DEV),
            "request_sha256": hashlib.sha256(request).hexdigest(),
        },
        "observer_self_test": self_test,
        "observer_trusted": observer_trusted,
        "normal_baseline": {
            "environment_keys": len(normal_env()),
            "exit": base_exit,
            "stdout_bytes": len(base_out),
            "stdout_sha256": hashlib.sha256(base_out).hexdigest(),
            "stderr": base_err.decode("utf-8", "replace")[:300],
            "stable_projection": base_proj,
            "sampler": {"samples": base_sampler.samples, "observation_ok": base_sampler.observation_ok,
                        "children": base_sampler.children, "tcp": base_sampler.tcp},
            "writes": base_writes,
        },
        "native_off": {
            "environment_keys": len(reduced_env()),
            "keys_visible_to_child": sorted(reduced_env()),
            "stripped_prefixes": list(STRIP_PREFIXES),
            "exit": off_exit,
            "stdout_bytes": len(off_out),
            "stdout_sha256": hashlib.sha256(off_out).hexdigest(),
            "stderr": off_err.decode("utf-8", "replace")[:300],
            "stable_projection": off_proj,
            "sampler": {"samples": off_sampler.samples, "observation_ok": off_sampler.observation_ok,
                        "children": off_sampler.children, "tcp": off_sampler.tcp},
            "writes": off_writes,
        },
        "comparison": {
            "same_stable_projection": base_proj == off_proj,
            "same_exit": base_exit == off_exit,
            "product_writes_observed": not (base_writes["clean"] and off_writes["clean"]),
            "foreign_children": foreign,
        },
        "not_proven": [
            "transitive imports of packages that happen to be installed (runtime behaviour only)",
            "kernel-level registry writes and file writes outside the watched roots",
            "network activity after the sampling window closes",
        ],
        "verdict": ("NATIVE_OFF_EQUIVALENT_NO_DEPENDENCY" if verified
                    else "NATIVE_OFF_NOT_VERIFIED_OR_DEPENDENCY_OBSERVED"),
    }
    (OUT / "native_off_r4.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"observer_trusted": observer_trusted, "self_test": self_test,
                      "comparison": record["comparison"], "verdict": record["verdict"],
                      "baseline_exit": base_exit, "off_exit": off_exit}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
