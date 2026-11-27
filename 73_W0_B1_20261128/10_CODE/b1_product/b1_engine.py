#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B1 native engine — r5 CODEX_FINAL product implementation (SOURCE_READ only).

Bound to:
  spec manifest 2e4db2d2c2bd6d52316f7e634587888441b5425b7c68902c00b36ded47960d6c
  (B1 24e4f17a..., B2 1a11f0cf..., two appendices)

Trusted context is loaded from FIXED absolute paths held by this module.
A caller cannot supply, extend or override context, roots, purpose or consumers.
No write API exists in this module: EFFECT is SOURCE_READ, write_set=[], preimage=N/A,
fin_order=DENY. Nothing under SQS-THC / FHS is written, fetched, checked out or imported.

Honest ceiling: the trust root is an owner-authored configuration file plus the
pre-existing owner directive in 00_PREFLIGHT/b1_source_allowlist.json. It is NOT a
hardware/OS-token attestation, so ReadyExecute-level host binding stays HOLD.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys

SPEC_VERSION = "2026-11-27_r7_Native-first_CODEX_FINAL"
SPEC_MANIFEST_SHA = "2e4db2d2c2bd6d52316f7e634587888441b5425b7c68902c00b36ded47960d6c"
SUBJECT = "SST/SQS-THC/PH01/E00"
ORIGINAL_WAVE = "P1-W00M"
BID = 1

# ---- fixed, non-caller-settable context (engineering trust root) -------------
W_ROOT = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace"
R_ROOT = os.path.join(W_ROOT, "71_W0_B0-B3_R7_20261127")
SPEC_DIR = os.path.join(W_ROOT, "W0_B0-B3_GEN3_CODEX_FINAL_2026-11-27_r7")
ALLOWLIST = os.path.join(R_ROOT, "00_PREFLIGHT", "b1_source_allowlist.json")
LOCATORS = os.path.join(R_ROOT, "00_PREFLIGHT", "b1_locator_bindings.json")
SPEC_B1 = os.path.join(SPEC_DIR,
    "SST_PLP_PH01_W0_B1_執行控制小包_實質正文_2026-11-27_r7_Native-first_CODEX_FINAL.md")

REPO_ROOT_ALLOWED = [r"C:\Projects\Agent_Workspace\SQS-THC"]
EXTERNAL_ROOTS_ALLOWED = [r"C:\Projects\Agent_Workspace\FHS\Fabric\FABRIC\fabric-desktop-automation"]

ERR_CONTEXT = "TRUST_CONTEXT_UNBOUND"
ERR_OVERRIDE = "CALLER_CONTEXT_OVERRIDE_FORBIDDEN"
ERR_ROOT = "REPO_ROOT_NOT_AUTHORIZED"
ERR_COMMIT = "COMMIT_UNRESOLVED"
ERR_PATH = "PATH_NOT_IN_COMMIT"
ERR_CHANGED = "SOURCE_CHANGED"


class EngineFault(Exception):
    def __init__(self, code, first_fail, detail="", exit_code=2):
        super().__init__(f"{code}: {first_fail}")
        self.code = code
        self.first_fail = first_fail
        self.detail = detail
        self.exit_code = exit_code


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo: str, *args: str, binary: bool = False):
    """argv-only git call; cwd pinned to the authorised repo root."""
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    if proc.returncode != 0:
        return None, proc.stderr.decode("utf-8", "replace").strip()
    return (proc.stdout if binary else proc.stdout.decode("utf-8", "replace")), None


# ---------------------------------------------------------------------------
# trusted context
# ---------------------------------------------------------------------------
def load_trusted_context(argv: list[str]) -> dict:
    for a in argv:
        if a in ("--context", "--trusted-context", "--root", "--acl-epoch", "--rights-epoch"):
            raise EngineFault(ERR_OVERRIDE, a, "caller may not supply or override trusted context",
                              exit_code=64)
    try:
        with open(os.path.join(SPEC_DIR, "FINAL_SPEC_MANIFEST.tsv"), "rb") as f:
            manifest_bytes = f.read()
    except OSError as e:
        raise EngineFault(ERR_CONTEXT, "SPEC_MANIFEST_UNREADABLE", str(e), exit_code=64)
    got = sha256_bytes(manifest_bytes)
    if got != SPEC_MANIFEST_SHA:
        raise EngineFault(ERR_CONTEXT, "SPEC_MANIFEST_DIGEST_MISMATCH",
                          f"observed {got}", exit_code=64)
    for path, label in ((ALLOWLIST, "ALLOWLIST"), (LOCATORS, "LOCATORS")):
        if not os.path.exists(path):
            raise EngineFault(ERR_CONTEXT, f"{label}_MISSING", path, exit_code=64)
    allow = json.load(open(ALLOWLIST, encoding="utf-8"))
    loc = json.load(open(LOCATORS, encoding="utf-8"))
    if allow.get("effect") != "SOURCE_READ" or allow.get("write_set") != []:
        raise EngineFault(ERR_CONTEXT, "ALLOWLIST_EFFECT_NOT_SOURCE_READ", "", exit_code=64)
    if not allow.get("owner_directive"):
        raise EngineFault(ERR_CONTEXT, "OWNER_DIRECTIVE_ABSENT", "", exit_code=64)
    if not str(allow.get("root", "")).lower().startswith("c:\\projects\\agent_workspace\\fhs\\fabric"):
        raise EngineFault(ERR_CONTEXT, "ALLOWLIST_ROOT_UNEXPECTED", allow.get("root", ""), exit_code=64)
    return {
        "spec_version": SPEC_VERSION,
        "spec_manifest_sha256": got,
        "spec_manifest_bytes": len(manifest_bytes),
        "spec_b1_sha256": sha256_file(SPEC_B1),
        "allowlist_ref": {"path": ALLOWLIST, "sha256": sha256_file(ALLOWLIST),
                          "owner_directive": allow["owner_directive"],
                          "scope_ceiling": allow.get("scope_ceiling", "")},
        "locator_ref": {"path": LOCATORS, "sha256": sha256_file(LOCATORS),
                        "claim_ceiling": loc.get("claim_ceiling", "")},
        "external_root": allow["root"],
        "purpose": allow["purpose"],
        "consumer_ids": allow["consumer_ids"],
        "effect": "SOURCE_READ",
        "write_set": [],
        "preimage": "N/A",
        "fin_order": "DENY",
        "os_principal": os.environ.get("USERNAME", ""),
        "trust_root_kind": "OWNER_AUTHORED_CONFIG_FILE",
        "trust_root_residual": "no OS-token attestation; ReadyExecute host binding stays HOLD",
    }


# ---------------------------------------------------------------------------
# repo identity (REPO op)
# ---------------------------------------------------------------------------
def op_repo(repo: str, ctx: dict) -> dict:
    if os.path.normcase(os.path.abspath(repo)) not in [os.path.normcase(r) for r in REPO_ROOT_ALLOWED]:
        raise EngineFault(ERR_ROOT, "REPO_ROOT_NOT_IN_ALLOWLIST", repo, exit_code=64)
    is_wt, err = git(repo, "rev-parse", "--is-inside-work-tree")
    if is_wt is None or is_wt.strip() != "true":
        raise EngineFault(ERR_ROOT, "NOT_A_GIT_WORK_TREE", err or "", exit_code=64)
    head, _ = git(repo, "rev-parse", "HEAD")
    symref, _ = git(repo, "symbolic-ref", "--short", "-q", "HEAD")
    remote, rerr = git(repo, "remote", "get-url", "origin")
    porcelain, _ = git(repo, "status", "--porcelain", "--untracked-files=no")
    return {
        "repo_root": repo,
        "is_work_tree": True,
        "local_head": (head or "").strip(),
        "local_branch": (symref or "(detached)").strip(),
        "remote_url": (remote or "").strip() or None,
        "remote_error": rerr,
        "dirty_tracked_files": len([l for l in (porcelain or "").splitlines() if l.strip()]),
        "columns": "remote_commit / local_head / index / worktree are separate fields; "
                   "a remote URL is never used as a local commit",
        "git_version": subprocess.run(["git", "--version"], capture_output=True
                                      ).stdout.decode().strip(),
    }


# ---------------------------------------------------------------------------
# declared-path resolution table for 18 BASE units + 5 KERNEL units
# declared strings are copied verbatim from the r5 spec; resolution is separate.
# ---------------------------------------------------------------------------
BASE_TARGETS = {
    "BASE-001": [("SQS-THC/src/kernel/fsdt/__init__.py", "repo:src/kernel/fsdt/__init__.py")],
    "BASE-002": [("src/kernel/temporal/__init__.py", "repo:src/kernel/temporal/__init__.py")],
    "BASE-003": [("src/kernel/knowledge/__init__.py", "repo:src/kernel/knowledge/__init__.py")],
    "BASE-004": [("src/kernel/harness/__init__.py", "repo:src/kernel/harness/__init__.py")],
    "BASE-005": [("src/kernel/capability/__init__.py", "repo:src/kernel/capability/__init__.py")],
    "BASE-006": [("agents/profiles/sqs-{orchestrator,data-analysis,risk}", "repo:agents/profiles/sqs-orchestrator"),
                 ("agents/profiles/sqs-{orchestrator,data-analysis,risk}", "repo:agents/profiles/sqs-data-analysis"),
                 ("agents/profiles/sqs-{orchestrator,data-analysis,risk}", "repo:agents/profiles/sqs-risk")],
    "BASE-007": [("SQS/TWICT_RUNTIME_PACK_MANIFEST.yaml", "repo:SQS/TWICT_RUNTIME_PACK_MANIFEST.yaml")],
    "BASE-008": [("SQS_ENGINEERING_BASE_DISPOSITION.yaml", "repo:SQS_ENGINEERING_BASE_DISPOSITION.yaml"),
                 ("SQS_STACK_MANIFEST.yaml", "repo:SQS_STACK_MANIFEST.yaml")],
    "BASE-009": [("data_plane/config/*.yaml", "glob:data_plane/config/*.yaml"),
                 ("src/backfill_daily.py", "repo:data_plane/src/backfill_daily.py"),
                 ("check_daily.py", "repo:data_plane/src/check_daily.py")],
    "BASE-010": [("adapters/xq-read-watch.yaml", "repo:adapters/xq-read-watch.yaml")],
    "BASE-011": [("adapters/fda-xq-globalwinner-route.yaml", "repo:adapters/fda-xq-globalwinner-route.yaml")],
    "BASE-012": [("FABRIC/fabric-desktop-automation/TEAM.md", "ext:TEAM.md"),
                 ("FABRIC/fabric-desktop-automation/AGENTS.md", "ext:AGENTS.md"),
                 ("FABRIC/fabric-desktop-automation/README.md", "ext:README.md")],
    "BASE-013": [("FABRIC/fabric-desktop-automation/FDA_DESKTOP_CAPABILITY_MATRIX.yaml",
                  "ext:FDA_DESKTOP_CAPABILITY_MATRIX.yaml")],
    "BASE-014": [("FABRIC/fabric-desktop-automation/fda_router.py", "ext:fda_router.py")],
    "BASE-015": [("FABRIC/fabric-desktop-automation/fda_lease.py", "ext:fda_lease.py")],
    "BASE-016": [("FABRIC/fabric-desktop-automation/xq_native_adapter.py", "ext:xq_native_adapter.py")],
    "BASE-017": [("FDA_EXECUTION_BINDING.json", "ext:FDA_EXECUTION_BINDING.json"),
                 ("governance/FDA_DEFERRED_SEMIAUTO_CONTRACT.yaml", "ext:governance/FDA_DEFERRED_SEMIAUTO_CONTRACT.yaml"),
                 ("FDA_INTEROP_DISPOSITION.yaml", "ext:governance/FDA_INTEROP_DISPOSITION.yaml")],
    "BASE-018": [("independent_checker.py", "ext:independent_checker.py"),
                 ("test_xq_build_drift.py", "ext:test_xq_build_drift.py"),
                 ("tests/test_fda_*", "extglob:tests/test_fda_*.py"),
                 ("docs/FDA_USER_GUIDE.md", "ext:docs/FDA_USER_GUIDE.md")],
}

KERNEL_TARGETS = {
    "KERNEL:fsdt": ("d34dc903cca203140a6cc7453ae2f6c78dfd2e5b", "src/kernel/fsdt/__init__.py",
                    "90a5f4d4e27aeafda82d15d439bbfa076cc4f55d70df6ee604b4602bad5598bb"),
    "KERNEL:temporal": ("d34dc903cca203140a6cc7453ae2f6c78dfd2e5b", "src/kernel/temporal/__init__.py",
                        "21e0150f8f97f1541e96b452b56571fa1518191a122fa5cf2f1af54ff9483a5d"),
    "KERNEL:knowledge": ("d34dc903cca203140a6cc7453ae2f6c78dfd2e5b", "src/kernel/knowledge/__init__.py",
                         "ea1e13cd7df0cf81059364c7606be4c6c317d78e4a91d3a847c7219465e33da6"),
    "KERNEL:harness": ("d34dc903cca203140a6cc7453ae2f6c78dfd2e5b", "src/kernel/harness/__init__.py",
                       "288a2a0e474a05fd38b992de5801b0f8f01668741a67c90c0d0e6f6b37ffc27e"),
    "KERNEL:capability": ("d34dc903cca203140a6cc7453ae2f6c78dfd2e5b", "src/kernel/capability/__init__.py",
                          "d2a143c5c970d8a5c2174f051871066fc04c0c9f5863ff4fac253f0cb9d68a41"),
}


def _tree_entry(repo: str, commit: str, rel: str) -> dict:
    out, err = git(repo, "ls-tree", "-r", "--full-tree", commit, "--", rel)
    if out is None:
        return {"status": "ERROR", "detail": err}
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) >= 3 and path == rel:
            return {"status": "FOUND", "mode": parts[0], "type": parts[1], "blob": parts[2]}
    return {"status": "NOT_IN_TREE"}


def resolve_target(ctx: dict, repo: str, commit: str, spec: str) -> dict:
    kind, _, rel = spec.partition(":")
    rel = rel.replace("/", os.sep)
    if kind == "repo":
        ent = _tree_entry(repo, commit, rel.replace(os.sep, "/"))
        if ent["status"] != "FOUND":
            disk = os.path.join(repo, rel)
            try:
                exists = os.path.exists(disk)
                isdir = os.path.isdir(disk)
            except OSError:
                exists, isdir = False, False
            out = {"resolution": "REPO_TREE", "path": rel.replace(os.sep, "/"),
                   "status": "ABSENT_TREE", "commit": None, "blob": None,
                   "raw_sha256": None, "bytes": None,
                   "note": "untracked disk bytes never become a commit/blob"}
            if exists and isdir:
                try:
                    children = sorted(os.listdir(disk))
                    out.update({"status": "DISK_DIRECTORY", "children": children,
                                "child_count": len(children),
                                "note": "declared target is a directory: no single raw SHA exists; "
                                        "profile identity must come from its own files, not a blob"})
                except PermissionError:
                    out.update({"status": "DIRECTORY_PERMISSION_DENIED",
                                "note": "directory exists but this OS principal cannot enumerate it; "
                                        "no identity, no content, nothing inferred"})
            elif exists:
                try:
                    out.update({"status": "DISK_BUT_UNTRACKED", "disk_sha256": sha256_file(disk),
                                "bytes": os.path.getsize(disk)})
                except (PermissionError, OSError) as ex:
                    out.update({"status": "FILE_PERMISSION_DENIED", "detail": str(ex)})
            return out
        data, err = git(repo, "cat-file", "blob", ent["blob"], binary=True)
        if data is None:
            return {"resolution": "REPO_TREE", "path": rel.replace(os.sep, "/"),
                    "status": "BLOB_UNREADABLE", "detail": err, "commit": commit,
                    "blob": ent["blob"], "raw_sha256": None, "bytes": None}
        return {"resolution": "REPO_TREE", "path": rel.replace(os.sep, "/"), "status": "TRACKED",
                "commit": commit, "blob": ent["blob"], "mode": ent["mode"],
                "raw_sha256": sha256_bytes(data), "bytes": len(data)}
    if kind == "glob":
        pattern = rel.replace(os.sep, "/")
        out, _ = git(repo, "ls-tree", "-r", "--full-tree", "--name-only", commit)
        import fnmatch
        hits = [p for p in (out or "").splitlines() if fnmatch.fnmatch(p, pattern)]
        return {"resolution": "REPO_TREE_GLOB", "path": pattern,
                "status": "TRACKED" if hits else "GLOB_NO_HIT", "commit": commit,
                "hits": hits, "hit_count": len(hits)}
    if kind == "extglob":
        import fnmatch
        root = ctx["external_root"]
        pattern = rel.replace(os.sep, "/")
        d, pat = os.path.split(pattern)
        base = os.path.join(root, d.replace("/", os.sep))
        names = sorted(os.listdir(base)) if os.path.isdir(base) else []
        hits = [f"{d}/{n}" for n in names if fnmatch.fnmatch(n, pat)]
        allowed = {a["path"] for a in json.load(open(ALLOWLIST, encoding="utf-8"))["artefacts"]}
        return {"resolution": "EXTERNAL_CARRIER_GLOB", "path": pattern,
                "status": "NOT_IN_OWNER_ALLOWLIST" if hits else "GLOB_NO_HIT",
                "names_observed": hits, "hit_count": len(hits),
                "in_allowlist": sorted(set(hits) & allowed),
                "note": "D-2: existence of these names is observable, their bytes are NOT read "
                        "without an owner-authorised read right"}
    if kind == "ext" or kind == "ext-tests":
        root = ctx["external_root"]
        target_rel = rel if kind == "ext" else rel.replace("ext-tests" + os.sep, "tests" + os.sep)
        fp = os.path.join(root, target_rel)
        allowed = {a["path"] for a in json.load(open(ALLOWLIST, encoding="utf-8"))["artefacts"]}
        norm = os.path.relpath(fp, root).replace(os.sep, "/")
        if norm not in allowed:
            return {"resolution": "EXTERNAL_CARRIER", "path": norm,
                    "status": "NOT_IN_OWNER_ALLOWLIST",
                    "note": "D-2: not in the owner-authorised 16-path read set; content not read"}
        if not os.path.exists(fp):
            return {"resolution": "EXTERNAL_CARRIER", "path": norm, "status": "ABSENT_ON_DISK"}
        data = open(fp, "rb").read()
        obs = sha256_bytes(data)
        pin = {a["path"]: a["raw_sha256"] for a in
               json.load(open(ALLOWLIST, encoding="utf-8"))["artefacts"]}[norm]
        return {"resolution": "EXTERNAL_CARRIER", "path": norm,
                "status": "ALLOWLIST_VERIFIED" if obs == pin else "ALLOWLIST_PIN_MISMATCH",
                "raw_sha256": obs, "pinned_sha256": pin, "pin_match": obs == pin,
                "bytes": len(data), "commit": None,
                "note": "external carrier has its own Git identity; not a repo commit"}
    raise EngineFault("UNKNOWN_RESOLUTION", spec, exit_code=70)


# ---------------------------------------------------------------------------
# BASE / KERNEL op
# ---------------------------------------------------------------------------
def _symbols_from_spec() -> dict:
    """Parse the §04.K2 KERNEL symbol table from the pinned spec (oracle != author memory)."""
    text = open(SPEC_B1, encoding="utf-8").read()
    rows = {}
    for line in text.splitlines():
        if not line.startswith("|") or line.count("|") < 6:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5 or cells[0] not in ("fsdt", "temporal", "knowledge", "harness", "capability"):
            continue
        if not cells[2].startswith("src/kernel/"):
            continue
        syms = []
        for item in cells[4].split("；"):
            item = item.strip()
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*L(\d+)[–\-](\d+)$", item)
            if m:
                syms.append({"name": m.group(1), "line_start": int(m.group(2)),
                             "line_end": int(m.group(3))})
        if syms:
            rows[cells[0]] = {"commit": cells[1], "path": cells[2], "raw_sha256": cells[3],
                              "symbols": syms}
    return rows


def _def_spans(src: bytes) -> dict:
    """name -> (lineno, end_lineno) for module-level defs/classes and class members."""
    tree = ast.parse(src.decode("utf-8"))
    spans = {}

    def visit(node, prefix=""):
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                spans[name] = (child.lineno, getattr(child, "end_lineno", child.lineno))
                if isinstance(child, ast.ClassDef):
                    visit(child, prefix=child.name + ".")
            elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                name = prefix + child.target.id
                spans.setdefault(name, (child.lineno, getattr(child, "end_lineno", child.lineno)))
            elif isinstance(child, ast.Assign):
                for t in child.targets:
                    if isinstance(t, ast.Name):
                        spans.setdefault(prefix + t.id, (child.lineno, getattr(child, "end_lineno", child.lineno)))

    visit(tree)
    return spans


def op_base(repo: str, ctx: dict, units: list[dict], commit: str) -> dict:
    entries, errors = [], []
    spec_syms = _symbols_from_spec()
    bindings = {}
    try:
        for b in json.load(open(LOCATORS, encoding="utf-8")).get("bindings", []):
            bindings.setdefault((b["unit"], b["declared_path"]), []).append(b)
    except OSError:
        bindings = {}
    for u in units:
        key, kind = u["key"], u["kind"]
        if kind not in ("BASE", "KERNEL"):
            continue
        entry = {"unit_id": u["unit_id"], "key": key, "kind": kind,
                 "owner": u.get("owner"), "consumer": u.get("consumer"),
                 "declared_verbatim": None, "targets": [], "missing": []}
        if kind == "BASE":
            for declared, spec in BASE_TARGETS.get(key, []):
                entry["declared_verbatim"] = declared
                r = resolve_target(ctx, repo, commit, spec)
                r["declared"] = declared
                entry["targets"].append(r)
        elif kind == "KERNEL":
            pin_commit, rel, expect_sha = KERNEL_TARGETS[key]
            pinned_exists, _ = git(repo, "rev-parse", "--verify", "--end-of-options", pin_commit + "^{commit}")
            ent = _tree_entry(repo, commit, rel)
            tgt = {"declared": f"commit {pin_commit}:{rel}", "resolution": "REPO_TREE",
                   "path": rel, "pinned_commit": pin_commit,
                   "pinned_commit_present_locally": pinned_exists is not None,
                   "observed_commit": commit, "content_expected_sha256": expect_sha,
                   "commit": commit if pinned_exists is not None else None}
            if ent["status"] == "FOUND":
                data, err = git(repo, "cat-file", "blob", ent["blob"], binary=True)
                obs = sha256_bytes(data)
                tgt.update({"blob": ent["blob"], "bytes": len(data), "raw_sha256": obs,
                            "content_identity": "RAW_SHA_MATCH_AT_LOCAL_HEAD" if obs == expect_sha
                                                else "RAW_SHA_MISMATCH",
                            "status": "TRACKED_CONTENT_MATCH" if obs == expect_sha
                                      else "TRACKED_CONTENT_MISMATCH"})
                # symbol-span verification against the pinned spec table
                spans = _def_spans(data)
                sym_res = []
                for s in spec_syms.get(key.split(":")[1], {}).get("symbols", []):
                    act = spans.get(s["name"])
                    ok = act == (s["line_start"], s["line_end"])
                    sym_res.append({"name": s["name"], "spec_span": [s["line_start"], s["line_end"]],
                                    "actual_span": list(act) if act else None,
                                    "match": bool(ok),
                                    "kind": "EXACT_SPAN_MATCH" if ok else
                                            ("PRESENT_SPAN_DIFFERS" if act else "SYMBOL_ABSENT")})
                tgt["symbols"] = sym_res
                tgt["symbols_ok"] = sum(1 for s in sym_res if s["match"])
                tgt["symbols_total"] = len(sym_res)
            else:
                tgt.update({"status": "NOT_IN_TREE", "raw_sha256": None, "bytes": None})
            if not pinned_exists:
                entry["missing"].append({"field": "pinned_commit",
                                         "reason": "UNVERIFIED",
                                         "detail": f"{pin_commit} is not in this repo's object database; "
                                                   f"content identity is carried by raw SHA at local HEAD only"})
            entry["targets"].append(tgt)
        if kind == "BASE" and not entry["targets"]:
            entry["missing"].append({"field": "declared_path", "reason": "AMBIGUOUS",
                                     "detail": "no resolution binding exists for this declared cell"})
            errors.append({"unit_id": u["unit_id"], "key": key, "code": "DECLARED_CELL_UNBOUND",
                           "first_fail": "BASE_ROW_MISSING", "retryable": False})
        for t in entry["targets"]:
            if t.get("disk_sha256"):
                for b in bindings.get((key, t["declared"]), []):
                    res = b["resolved_path"].replace("/", "\\")
                    rel = b["resolved_path"].split("data_plane\\")[-1] if "data_plane\\" in b["resolved_path"] else b["resolved_path"]
                    suffix_match = res.replace("\\", "/").endswith(t["path"])
                    t["locator_binding"] = {
                        "declared_path": b["declared_path"],
                        "resolved_path": b["resolved_path"],
                        "expected_raw_sha256": b["raw_sha256"],
                        "observed_disk_sha256": t["disk_sha256"],
                        "sha_match": t["disk_sha256"] == b["raw_sha256"],
                        "resolved_path_matches_observed": suffix_match,
                        "ratification": b.get("ratification", ""),
                        "binding_effect": ("D-1 evidence closed for content identity only; "
                                           "SPEC declared path is not amended and the binding "
                                           "stays CANDIDATE_NOT_RATIFIED until the Repo/Source "
                                           "Owner adopts it"),
                    }
        entries.append(entry)
    return {"entries": entries, "errors": errors,
            "read_set_summary": {
                "units": len(entries),
                "tracked_targets": sum(1 for e in entries for t in e["targets"]
                                       if t["status"] in ("TRACKED", "TRACKED_CONTENT_MATCH")),
                "external_verified": sum(1 for e in entries for t in e["targets"]
                                         if t["status"] == "ALLOWLIST_VERIFIED"),
                "missing_targets": sum(1 for e in entries for t in e["targets"]
                                       if t["status"] not in ("TRACKED", "TRACKED_CONTENT_MATCH", "ALLOWLIST_VERIFIED")),
            }}


# ---------------------------------------------------------------------------
# FDA op (static evidence + deny invariant, no GUI/broker/lease)
# ---------------------------------------------------------------------------
SLOTS = ["watch_ui", "radar_signal", "xs_compile", "xs_backtest",
         "at_simulated_order", "broker_external_event_read", "broker_live_submit"]


def fda_live_broker_policy() -> dict:
    """Read the live-broker policy out of the owner-authorised carrier bytes.

    The value is not a constant in this module: if the artefact bytes change, the
    digest check fails and the guard refuses to run.
    """
    allow = json.load(open(ALLOWLIST, encoding="utf-8"))
    for a in allow["artefacts"]:
        if a["path"] != "FDA_DESKTOP_CAPABILITY_MATRIX.yaml":
            continue
        fp = os.path.join(allow["root"], a["path"].replace("/", os.sep))
        raw = open(fp, "rb").read()
        if sha256_bytes(raw) != a["raw_sha256"]:
            raise EngineFault(ERR_CHANGED, "SOURCE_CHANGED",
                              "capability matrix does not match its pinned digest")
        for i, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            m = re.match(r"\s*live_broker:\s*(\S+)", line)
            if m:
                return {"value": m.group(1), "line": i, "artefact": a["path"],
                        "sha256": a["raw_sha256"], "bytes": len(raw)}
    raise EngineFault("FDA_LIVE_POLICY_MISSING", "FDA_EFFECT_UNAUTHORIZED", "", exit_code=2)


def fda_live_submit_guard(action: str, policy_value: str) -> dict:
    """Effect dispatcher for the live-submit slot.

    submit/replace/cancel are refused *because* the pinned policy says DENY_ALWAYS,
    and there is no connector/session in this process to reach even if it did not.
    A flipped policy value would take a different branch, which is what makes this a
    data-driven control rather than a constant.
    """
    base = {"action": action, "policy_value": policy_value, "order_path_reached": False,
            "effect": "NONE"}
    if action == "read":
        # the control is only admissible when the pinned artefact really reads back with its
        # pinned digest; a changed byte turns this into a refusal, so it is data-bound
        pol = fda_live_broker_policy()
        return {**base, "decision": "ALLOW_READ_CONTROL", "effect": "SOURCE_READ",
                "policy_value": pol["value"],
                "artefact": pol["artefact"], "artefact_sha256": pol["sha256"],
                "artefact_line": pol["line"], "artefact_bytes": pol["bytes"],
                "reason": "read-only observation control anchored to the pinned carrier digest; "
                          "does not reach any order path"}
    if action in ("submit", "replace", "cancel"):
        if policy_value == "DENY_ALWAYS":
            return {**base, "decision": "DENY", "first_fail": "FIN_ORDER_DENY_ALWAYS",
                    "reason": "pinned carrier policy live_broker=DENY_ALWAYS"}
        return {**base, "decision": "DENY", "first_fail": "NO_CONNECTOR_PRESENT",
                "reason": "policy would admit the effect but this process has no token, "
                          "session, lease or broker client, so it still cannot be reached"}
    return {**base, "decision": "DENY", "first_fail": "FIN_ORDER_DENY_ALWAYS",
            "reason": "action is not in the admissible set {read}"}


def op_fda(ctx: dict, units: list[dict] | None = None) -> dict:
    allow = json.load(open(ALLOWLIST, encoding="utf-8"))
    policy = fda_live_broker_policy()
    root = allow["root"]
    arts = []
    for a in allow["artefacts"]:
        fp = os.path.join(root, a["path"].replace("/", os.sep))
        if not os.path.exists(fp):
            arts.append({**a, "observed": "ABSENT_ON_DISK"})
            continue
        data = open(fp, "rb").read()
        obs = sha256_bytes(data)
        arts.append({**a, "observed": "RAW_SHA_MATCH" if obs == a["raw_sha256"] else "RAW_SHA_MISMATCH",
                     "observed_sha256": obs, "observed_bytes": len(data)})
    slot_hits = {}
    for slot in SLOTS:
        hits = []
        for a in arts:
            if a.get("observed") != "RAW_SHA_MATCH":
                continue
            fp = os.path.join(root, a["path"].replace("/", os.sep))
            try:
                txt = open(fp, encoding="utf-8").read()
            except UnicodeDecodeError:
                continue
            for i, line in enumerate(txt.splitlines(), 1):
                if slot in line:
                    hits.append({"artefact": a["path"], "line": i, "text": line.strip()[:160]})
        slot_hits[slot] = hits
    unit_by_key = {u["key"]: u for u in (units or []) if u.get("kind") == "FDA"}
    slot_entries = []
    for s in SLOTS:
        u = unit_by_key.get(f"FDA:{s}", {})
        ent = {"unit_id": u.get("unit_id"), "key": f"FDA:{s}", "kind": "FDA",
               "slot": s, "static_hits": slot_hits[s], "hit_count": len(slot_hits[s]),
               "evidence_class": "CARRIER_LEVEL_ONLY",
               "owner": u.get("owner"), "consumer": u.get("consumer"),
               "missing": [{"field": "slot_action_artefact_mapping", "reason": "UNVERIFIED",
                            "detail": "D-3 open: no original slot->action->artefact M:N, no original "
                                      "typed schema/Reader/fixture; static carrier evidence only"}],
               "note": "no GUI, no lease, no broker, no install"}
        if s == "broker_live_submit":
            pol = policy
            ents = {
                "pos_deny_invariant": fda_live_submit_guard("read", pol["value"]),
                "allowed_effect_pos": None,
                "neg_arms": [fda_live_submit_guard(a, pol["value"])
                             for a in ("submit", "replace", "cancel")],
                "unknown_action": fda_live_submit_guard("replace_all_orders", pol["value"]),
                "policy": pol,
                "policy_flip_probe": fda_live_submit_guard("submit", "ALLOW"),
            }
            ent["deny_control"] = ents
            ent["missing"].append({"field": "allowed_effect_pos", "reason": "ABSENT",
                                   "detail": "by design: live submission has no allowed-effect POS in W0"})
        slot_entries.append(ent)
    return {
        "carrier_root": root,
        "artefacts": arts,
        "artefacts_verified": sum(1 for a in arts if a.get("observed") == "RAW_SHA_MATCH"),
        "artefacts_total": len(arts),
        "slots": slot_entries,
        "live_broker_policy": {"value": policy["value"], "artefact": policy["artefact"],
                               "line": policy["line"], "sha256": policy["sha256"],
                               "effect": "submit/replace/cancel refused for this run"},
        "gui_started": False, "lease_acquired": False, "broker_contacted": False,
    }


# ---------------------------------------------------------------------------
# ROOTS op
# ---------------------------------------------------------------------------
def op_roots(repo: str, commit: str) -> dict:
    out, _ = git(repo, "ls-tree", "-r", "--full-tree", "--name-only", commit)
    paths = set((out or "").splitlines())
    probes = {
        "config": sorted(p for p in paths if p.endswith((".yaml", ".yml", ".toml", ".json")))[:40],
        "imports_top_level": sorted(p for p in paths if p.startswith("src/")),
        "aliases_symlinks": [],
        "env_files": sorted(p for p in paths if ".env" in p or p.endswith(".env")),
        "exec_entrypoints": sorted(p for p in paths if p.endswith(("__main__.py", "cli.py", "run.py"))),
    }
    return {
        "scope": {"repo": repo, "head": commit, "method": "static ls-tree inventory only"},
        "seven_roots": "UNKNOWN",
        "twenty_physical_edges": "UNKNOWN",
        "missing": [{"field": "seven_root_physical_chain", "reason": "UNVERIFIED",
                     "detail": "B6 owns the 20 Edge ID set and has not materialised it; "
                               "B1 must not invent the physical edge denominator"},
                    {"field": "runtime_consumer_call_chain", "reason": "UNVERIFIED",
                     "detail": "no running system, no trace; grep/empty-hit is never evidence of OFF"}],
        "evidence": probes,
        "note": "the 17 DAG edges of §03 are product dependencies, not the 7 roots / 20 physical edges",
    }


def run(op: str, repo: str, units: list[dict] | None = None, commit: str | None = None,
        argv: list[str] | None = None) -> dict:
    ctx = load_trusted_context(sys.argv[1:] if argv is None else argv)
    body = {"schema": "SST.PH01.W0.B1.TypedResult@5",
            "spec_version": SPEC_VERSION, "subject": SUBJECT, "original_wave": ORIGINAL_WAVE,
            "bid": BID, "op": op, "effect": "SOURCE_READ", "write_set": [], "preimage": "N/A",
            "fin_order": "DENY", "product_actual": "EXECUTED", "trusted_context": ctx}
    if op == "REPO":
        body["repo"] = op_repo(repo, ctx)
        return body
    if op in ("BASE", "ALL"):
        r = op_repo(repo, ctx)
        head = commit or r["local_head"]
        if not head:
            raise EngineFault(ERR_COMMIT, "HEAD_UNRESOLVED", "", exit_code=2)
        ok, _ = git(repo, "rev-parse", "--verify", "--end-of-options", head + "^{commit}")
        if ok is None:
            raise EngineFault(ERR_COMMIT, "COMMIT_UNRESOLVED", head, exit_code=2)
        body["repo"] = r
        body["base"] = op_base(repo, ctx, units or [], head)
        if op == "BASE":
            return body
    if op == "FDA":
        body["fda"] = op_fda(ctx, units)
        return body
    if op == "ROOTS":
        r = op_repo(repo, ctx)
        body["roots"] = op_roots(repo, r["local_head"])
        return body
    if op == "ALL":
        body["fda"] = op_fda(ctx, units)
        body["roots"] = op_roots(repo, body["repo"]["local_head"])
        return body
    raise EngineFault("UNKNOWN_OP", op, exit_code=64)
