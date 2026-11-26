#!/usr/bin/env python3
"""B1 reader — SOURCE_READ only, WriteSet=[], preimage=N/A.

Implements the four B1 ops against an authorized RepoRoot with git plumbing only
(rev-parse / ls-tree / cat-file); never checkout/fetch/import/executes repo code.

  b1.repo()   -> RepoReadSet (commit / tree / per-path blob / missing) + remote-vs-local split
  b1.base()   -> CommitPathSpan for the 18 BASE units + 5 KERNEL symbols (AST, no import)
  b1.fda()    -> 7 slot source/lease/raw status; live_submit stays DENY_INVARIANT
  b1.roots()  -> UnknownPhysicalEdgeSet (static only; unseen stays UNKNOWN, never "OFF")

Every unit reports declared_path / observed_path / classification / blob_sha / raw_sha256.
Absence is recorded as typed missing, never as "function does not exist".
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, field, asdict
from typing import Any

SCHEMA = "SST.PH01.W0.B1.RepoReadSet@1"
SUBJECT = "SST/SQS-THC/PH01/E00"
WAVE = "P1-W00M"
BID = 1


# ---------------------------------------------------------------- git plumbing
def _git(repo: str, *args: str, timeout: int = 120) -> tuple[int, bytes, bytes]:
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


@dataclass
class RepoIdentity:
    root: str
    commit: str
    tree: str
    branch: str
    dirty: bool
    status_entries: int
    remotes: list[str]
    remote_head: str | None
    remote_state: str
    git_version: str


def read_identity(repo: str) -> RepoIdentity:
    rc, out, err = _git(repo, "rev-parse", "--verify", "HEAD")
    if rc != 0:
        raise RuntimeError(f"REPO_UNBOUND: rev-parse failed: {err[:200]!r}")
    commit = out.decode().strip()
    _, out, _ = _git(repo, "rev-parse", "--verify", f"{commit}^{{tree}}")
    tree = out.decode().strip()
    _, out, _ = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    branch = out.decode().strip()
    _, out, _ = _git(repo, "status", "--porcelain=v1")
    st = [l for l in out.decode("utf-8", "replace").splitlines() if l.strip()]
    _, out, _ = _git(repo, "remote", "-v")
    remotes = sorted({l.split()[1] for l in out.decode().splitlines() if l.strip()})
    remote_head, remote_state = None, "NO_REMOTE_CONFIGURED"
    if remotes:
        rc2, out2, _ = _git(repo, "ls-remote", "--heads", remotes[0], "main", timeout=60)
        if rc2 == 0 and out2.strip():
            remote_head = out2.decode().split()[0]
            remote_state = "MEASURED"
        else:
            remote_state = "UNREACHABLE_OR_NO_MAIN"
    _, out, _ = _git(repo, "--version")
    return RepoIdentity(root=repo, commit=commit, tree=tree, branch=branch,
                        dirty=bool(st), status_entries=len(st), remotes=remotes,
                        remote_head=remote_head, remote_state=remote_state,
                        git_version=out.decode().strip())


def list_tree(repo: str, commit: str) -> dict[str, dict[str, str]]:
    """path -> {mode, type, sha, bytes} for every tracked entry at commit."""
    rc, out, err = _git(repo, "ls-tree", "-r", "-l", "-z", commit, timeout=300)
    if rc != 0:
        raise RuntimeError(f"ls-tree failed: {err[:200]!r}")
    entries: dict[str, dict[str, str]] = {}
    for rec in out.split(b"\0"):
        if not rec:
            continue
        meta, _, path = rec.partition(b"\t")
        parts = meta.split()
        if len(parts) < 4:
            continue
        mode, typ, sha, size = parts[0], parts[1], parts[2], parts[3]
        entries[path.decode("utf-8", "surrogateescape")] = {
            "mode": mode.decode(), "type": typ.decode(),
            "sha": sha.decode(), "bytes": size.decode() if size != b"-" else None,
        }
    return entries


def read_blob(repo: str, blob_sha: str) -> bytes:
    rc, out, err = _git(repo, "cat-file", "blob", blob_sha, timeout=120)
    if rc != 0:
        raise RuntimeError(f"cat-file failed for {blob_sha}: {err[:160]!r}")
    return out


# ------------------------------------------------------------- path resolving
def _norm(p: str) -> str:
    p = p.strip().strip("`").strip()
    p = p.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


_EXT = r"(?:py|yaml|yml|json|md|toml|txt|ts|js)"
_PATHTOK = re.compile(r"((?:SQS-THC/)?(?:[A-Za-z0-9_.\-\u4e00-\u9fff]+/)*"
                      r"[A-Za-z0-9_.\-\u4e00-\u9fff]+\*?\." + _EXT + r")")


def _expand_braces(s: str) -> list[str]:
    m = re.search(r"\{([^}]*)\}", s)
    if not m:
        return [s]
    out: list[str] = []
    for alt in m.group(1).split(","):
        out += _expand_braces(s[:m.start()] + alt.strip() + s[m.end():])
    return out


def declared_candidates(raw: str) -> list[str]:
    """Extract declared path tokens. Prose is rejected by shape, not by guessing:
    a token qualifies only if it carries a file extension or a directory separator."""
    raw = raw.split("；")[0]
    raw = re.split(r"[（(]", raw)[0]
    res: list[str] = []
    for chunk in re.split(r"[、，]", raw):
        for c in _expand_braces(chunk.strip()):
            c = _norm(c)
            if not c or " " in c or "→" in c:
                continue
            if c.startswith("SQS-THC/"):
                c = c[len("SQS-THC/"):]
            if _PATHTOK.search(c) or "/" in c:
                res.append(c)
    seen, uniq = set(), []
    for c in res:
        if c not in seen:
            seen.add(c); uniq.append(c)
    return uniq


def path_from_input_rule(rule: str) -> list[str]:
    out: list[str] = []
    for span in re.findall(r"`([^`]*)`", rule):
        for c in declared_candidates(span):
            if c not in out:
                out.append(c)
    return out


def kernel_path(key: str) -> list[str]:
    """W0M SHALL-53.1-01 / B1 §04.K2: the five kernel carriers are
    src/kernel/{fsdt,temporal,knowledge,harness,capability}/__init__.py."""
    name = key.split(":", 1)[1] if ":" in key else key
    return [f"src/kernel/{name}/__init__.py"]


def resolve(path: str, tree: dict[str, dict[str, str]], repo: str | None = None) -> tuple[str, list[str], str]:
    """Return (classification, matched_paths, note).

    Splits declared / tracked-at-HEAD / present-on-disk-but-untracked, because the SPEC
    requires local HEAD and working tree to be recorded in separate columns. A file that
    is absent from the tree but present on disk is NOT the same as absent."""
    if path.endswith("/"):
        path = path[:-1]
    if "*" in path:
        pre, _, suf = path.partition("*")
        hits = sorted(p for p in tree if p.startswith(pre) and p.endswith(suf))
        return ("TRACKED_GLOB" if hits else _disk_fallback(path, tree, repo), hits, f"glob {path}")
    if path in tree:
        return "TRACKED_PRESENT", [path], ""
    pref = path + "/"
    hits = sorted(p for p in tree if p.startswith(pref))
    if hits:
        return "TRACKED_DIR_PRESENT", hits, f"directory with {len(hits)} entries"
    base = os.path.basename(path)
    hits = sorted(p for p in tree if os.path.basename(p) == base)
    if hits:
        return "FOUND_ELSEWHERE", hits, f"declared path absent; same basename at {len(hits)} path(s)"
    return _disk_fallback(path, tree, repo), [], "not in HEAD tree"


def _disk_fallback(path: str, tree: dict[str, dict[str, str]], repo: str | None) -> str:
    if repo:
        ap = os.path.join(repo, path.replace("/", os.sep))
        if os.path.exists(ap):
            return "DISK_ONLY_UNTRACKED"
    return "ABSENT_IN_TREE"


def py_symbols(src: bytes) -> dict[str, Any]:
    try:
        mod = ast.parse(src.decode("utf-8", "strict"))
    except Exception as e:
        return {"ast": "PARSE_FAILED", "error": f"{type(e).__name__}: {e}"[:200]}
    defs, classes, assigns = [], [], []
    for node in mod.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defs.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigns.append(t.id)
    return {"ast": "PARSED", "functions": sorted(defs), "classes": sorted(classes),
            "assignments": sorted(assigns),
            "public": sorted(n for n in defs + classes + assigns if not n.startswith("_"))}


# ------------------------------------------------------------------- the ops
def run(repo: str, units: list[dict], fda_re, roots_edges: list[str]) -> dict[str, Any]:
    ident = read_identity(repo)
    tree = list_tree(repo, ident.commit)
    started = __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")

    base_rows, fda_rows = [], []
    blob_cache: dict[str, tuple[int, str]] = {}

    def measure(p: str) -> dict[str, Any]:
        e = tree[p]
        if e["sha"] not in blob_cache:
            blob = read_blob(repo, e["sha"])
            blob_cache[e["sha"]] = (len(blob), hashlib.sha256(blob).hexdigest())
        n, rs = blob_cache[e["sha"]]
        return {"path": p, "git_blob_sha1": e["sha"], "mode": e["mode"],
                "raw_sha256": rs, "bytes": n,
                "git_bytes_field": e.get("bytes")}

    for u in units:
        sp = u.get("source_payload") or []
        declared_cell = sp[2] if len(sp) > 2 else ""
        cands = declared_candidates(declared_cell)
        src_note = "source_payload[2]"
        if u.get("kind") == "KERNEL":
            alt = path_from_input_rule(u.get("input_rule") or "") or kernel_path(u["key"])
            cands, src_note = alt, ("input_rule" if path_from_input_rule(u.get("input_rule") or "")
                                    else "spec_04_K2_kernel_carrier")
        elif not cands:
            alt = path_from_input_rule(u.get("input_rule") or "")
            if alt:
                cands, src_note = alt, "input_rule"
        row = {"unit_id": u["unit_id"], "key": u["key"], "kind": u["kind"],
               "op_id": u.get("op_id"), "declared_cell": declared_cell,
               "declared_from": src_note,
               "declared_paths": cands, "case_ids": u.get("case_ids"),
               "resolutions": []}
        for c in cands:
            cls, hits, note = resolve(c, tree, repo)
            r = {"declared_path": c, "classification": cls, "matched": hits[:12],
                 "hit_count": len(hits), "note": note, "measured": []}
            if cls == "DISK_ONLY_UNTRACKED":
                ap = os.path.join(repo, c.replace("/", os.sep))
                if os.path.isfile(ap):
                    b = open(ap, "rb").read()
                    r["disk_measured"] = {"path": c, "raw_sha256": hashlib.sha256(b).hexdigest(),
                                          "bytes": len(b), "tracked": False}
            for h in hits[:12]:
                m = measure(h)
                if h.endswith(".py"):
                    m["symbols"] = py_symbols(read_blob(repo, tree[h]["sha"]))
                r["measured"].append(m)
            row["resolutions"].append(r)
        # row verdict
        classes = {x["classification"] for x in row["resolutions"]}
        trk = classes & {"TRACKED_PRESENT", "TRACKED_GLOB", "TRACKED_DIR_PRESENT"}
        if trk and not (classes & {"ABSENT_IN_TREE", "DISK_ONLY_UNTRACKED"}):
            row["verdict"] = "OBSERVED_IN_REPO"
        elif trk:
            row["verdict"] = "PARTIAL"
        elif "DISK_ONLY_UNTRACKED" in classes:
            row["verdict"] = "DISK_ONLY_UNTRACKED_NOT_AT_HEAD"
        elif "FOUND_ELSEWHERE" in classes:
            row["verdict"] = "DECLARED_PATH_ABSENT_FOUND_ELSEWHERE"
        else:
            row["verdict"] = "TYPED_MISSING_ABSENT_IN_TREE"
        row["first_fail"] = (None if row["verdict"] == "OBSERVED_IN_REPO"
                             else "B1_SOURCE_DECLARED_PATH_MISSING")
        (fda_rows if u["kind"] == "FDA" else base_rows).append(row)

    roots = []
    for edge in roots_edges:
        roots.append({"edge_id": edge, "scope": "PH01 W0", "head": ident.commit,
                      "evidence": [], "physical_status": "UNKNOWN",
                      "reason": "no config/import/alias/exec/runtime artefact for this edge in the HEAD tree; "
                                "static absence is not evidence of removal",
                      "missing": ["physical call-chain artefact"]})

    return {
        "schema": SCHEMA,
        "subject": SUBJECT, "original_wave": WAVE, "bid": BID,
        "generated_at": started,
        "effect": "SOURCE_READ", "write_set": [], "preimage": "N/A",
        "repo": asdict(ident),
        "tree_entries": len(tree),
        "ops": {
            "B1.REPO": {"typed_output": "RepoReadSet.commit/path/blob/missing",
                        "commit": ident.commit, "tree": ident.tree,
                        "local_head_equals_remote": (ident.remote_head == ident.commit
                                                     if ident.remote_head else None),
                        "remote_vs_local": {"local": ident.commit, "remote": ident.remote_head,
                                            "state": ident.remote_state},
                        "dirty": ident.dirty},
            "B1.BASE": {"typed_output": "CommitPathSpan", "rows": base_rows},
            "B1.FDA": {"typed_output": "7 slot source/lease/raw status", "rows": fda_rows,
                       "live_submit": {"slot": "FDA:broker_live_submit",
                                       "invariant": "DENY_INVARIANT",
                                       "allowed_effect_pos": None,
                                       "note": "no token/connector; never executed"}},
            "B1.ROOTS": {"typed_output": "UnknownPhysicalEdgeSet", "rows": roots},
        },
    }
