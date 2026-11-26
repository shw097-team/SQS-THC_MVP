#!/usr/bin/env python3
"""B1 reader v2 — adds disk-side resolution and the FDA carrier inventory.

v1 only searched the git tree at HEAD, so untracked-but-present implementation files
were reported as absent. v2 indexes the working tree as well (the Owner's instruction:
mine the previous implementation instead of rebuilding), and inventories the FDA slot
sources across the candidate carrier roots under FHS/Fabric.

Effects remain SOURCE_READ / WriteSet=[] / preimage=N/A. No import, no execution,
no checkout.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from typing import Any

SCHEMA = "SST.PH01.W0.B1.RepoReadSet@2"
SUBJECT = "SST/SQS-THC/PH01/E00"
WAVE = "P1-W00M"
BID = 1

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache",
             ".pytest_cache", ".ruff_cache", ".idea", ".vscode"}


# ---------------------------------------------------------------- git plumbing
def _git(repo: str, *args: str, timeout: int = 300) -> tuple[int, bytes, bytes]:
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def read_identity(repo: str) -> dict[str, Any]:
    rc, out, err = _git(repo, "rev-parse", "--verify", "HEAD")
    if rc != 0:
        raise RuntimeError(f"REPO_UNBOUND: {err[:200]!r}")
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
            remote_head = out2.decode().split()[0]; remote_state = "MEASURED"
        else:
            remote_state = "UNREACHABLE_OR_NO_MAIN"
    _, out, _ = _git(repo, "--version")
    return {"root": repo, "commit": commit, "tree": tree, "branch": branch,
            "dirty": bool(st), "status_entries": len(st), "remotes": remotes,
            "remote_head": remote_head, "remote_state": remote_state,
            "git_version": out.decode().strip()}


def list_tree(repo: str, commit: str) -> dict[str, dict[str, str]]:
    rc, out, err = _git(repo, "ls-tree", "-r", "-l", "-z", commit)
    if rc != 0:
        raise RuntimeError(f"ls-tree failed: {err[:200]!r}")
    e: dict[str, dict[str, str]] = {}
    for rec in out.split(b"\0"):
        if not rec:
            continue
        meta, _, path = rec.partition(b"\t")
        p = meta.split()
        if len(p) < 4:
            continue
        e[path.decode("utf-8", "surrogateescape")] = {
            "mode": p[0].decode(), "type": p[1].decode(), "sha": p[2].decode(),
            "bytes": p[3].decode() if p[3] != b"-" else None}
    return e


def read_blob(repo: str, blob_sha: str) -> bytes:
    rc, out, err = _git(repo, "cat-file", "blob", blob_sha)
    if rc != 0:
        raise RuntimeError(f"cat-file failed {blob_sha}: {err[:160]!r}")
    return out


# -------------------------------------------------------------- disk indexing
def index_disk(root: str, max_files: int = 400_000) -> dict[str, list[str]]:
    """basename -> [relative posix paths] over the working tree, skipping VCS caches."""
    byname: dict[str, list[str]] = {}
    n = 0
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel_dir = os.path.relpath(dirpath, root)
        for fn in filenames:
            n += 1
            if n > max_files:
                return byname
            rel = fn if rel_dir == "." else f"{rel_dir.replace(os.sep, '/')}/{fn}"
            byname.setdefault(fn, []).append(rel)
    return byname


def sha_file(p: str) -> tuple[str, int]:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest(), os.path.getsize(p)


# ------------------------------------------------------------- path resolving
def _norm(p: str) -> str:
    p = p.strip().strip("`").strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


_EXT = r"(?:py|yaml|yml|json|md|toml|txt|ts|js|ps1|cmd)"
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
    name = key.split(":", 1)[1] if ":" in key else key
    return [f"src/kernel/{name}/__init__.py"]


def resolve(path: str, tree: dict[str, dict[str, str]], repo: str,
            disk: dict[str, list[str]]) -> dict[str, Any]:
    """Classify a declared path against HEAD tree, working tree, and a disk index."""
    r: dict[str, Any] = {"declared_path": path, "matched": [], "note": ""}
    p = path[:-1] if path.endswith("/") else path

    if "*" in p:
        pre, _, suf = p.partition("*")
        hits = sorted(x for x in tree if x.startswith(pre) and x.endswith(suf))
        if hits:
            r.update(classification="TRACKED_GLOB", matched=hits[:24], note=f"glob {p}")
            return r
        allpaths = sorted({x for v in disk.values() for x in v})
        dh = sorted(x for x in allpaths if x.startswith(pre) and x.endswith(suf)
                    and os.path.isfile(os.path.join(repo, x.replace("/", os.sep))))
        if dh:
            r.update(classification="DISK_GLOB_UNTRACKED", matched=dh[:24],
                     note=f"glob {p} matched {len(dh)} working-tree path(s)")
            return r
        r.update(classification="ABSENT_IN_TREE_AND_DISK", matched=[], note=f"glob {p} no hit")
        return r
    if p in tree:
        r.update(classification="TRACKED_PRESENT", matched=[p])
        return r

    pref = p + "/"
    trk = sorted(x for x in tree if x.startswith(pref))
    if trk:
        r.update(classification="TRACKED_DIR_PRESENT", matched=trk[:24],
                 note=f"{len(trk)} tracked entries")
        return r

    # exact path on disk (untracked)
    ap = os.path.join(repo, p.replace("/", os.sep))
    if os.path.isdir(ap):
        inner = sorted(os.listdir(ap))[:24]
        r.update(classification="DISK_DIR_UNTRACKED", matched=[p],
                 note=f"untracked dir, {len(inner)} entries", disk_dir_listing=inner)
        return r
    if os.path.isfile(ap):
        s, b = sha_file(ap)
        r.update(classification="DISK_FILE_UNTRACKED", matched=[p],
                 disk_measured={"path": p, "raw_sha256": s, "bytes": b, "tracked": False})
        return r

    # same basename elsewhere in HEAD tree
    base = os.path.basename(p)
    th = sorted(x for x in tree if os.path.basename(x) == base)
    if th:
        r.update(classification="FOUND_ELSEWHERE_IN_TREE", matched=th[:12],
                 note=f"declared path absent; basename at {len(th)} tracked path(s)")
        return r

    # same basename elsewhere on disk (the case the Owner flagged). A caller-supplied index entry
    # that claims the DECLARED path itself is rejected: that path was already checked on the real
    # filesystem above, so an index hit equal to it is forged, not evidence.
    dh = sorted(x for x in disk.get(base, []) if x != p)
    if dh:
        r.update(classification="FOUND_ELSEWHERE_ON_DISK", matched=dh[:12],
                 note=f"declared path absent; basename at {len(dh)} working-tree path(s)")
        return r

    r.update(classification="ABSENT_IN_TREE_AND_DISK", note="no hit at declared path, by basename, tree or disk")
    return r


def py_symbols(src: bytes) -> dict[str, Any]:
    try:
        mod = ast.parse(src.decode("utf-8", "strict"))
    except Exception as e:
        return {"ast": "PARSE_FAILED", "error": f"{type(e).__name__}: {e}"[:200]}
    f, c, a = [], [], []
    for n in mod.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            f.append(n.name)
        elif isinstance(n, ast.ClassDef):
            c.append(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    a.append(t.id)
    return {"ast": "PARSED", "functions": sorted(f), "classes": sorted(c),
            "assignments": sorted(a),
            "public": sorted(x for x in f + c + a if not x.startswith("_"))}


# ------------------------------------------------------------ FDA inventory
FDA_ARTEFACTS = ["fda_router.py", "fda_lease.py", "xq_native_adapter.py",
                 "FDA_EXECUTION_BINDING.json", "FDA_DESKTOP_CAPABILITY_MATRIX.yaml",
                 "FDA_ASSET_REGISTRY.json", "FDA_DIRECTORY_TREE.txt",
                 "FDA_FOLDER_REORGANIZATION_RECEIPT.json", "independent_checker.py",
                 "test_xq_build_drift.py", "TEAM.md", "AGENTS.md", "README.md",
                 "docs/FDA_USER_GUIDE.md", "governance/FDA_INTEROP_DISPOSITION.yaml",
                 "governance/FDA_DEFERRED_SEMIAUTO_CONTRACT.yaml"]
# README.md is one of the 16 allow-listed artefacts; excluding it from the collision inventory
# made IDENTICAL_MODULO_EOL cover 15/16 (round-3 checker item 5).


def matrix_vocabulary(carriers: list[str]) -> dict[str, Any]:
    """Read the FDA capability matrix's own vocabulary (the carriers do not use the
    SPEC's seven slot names verbatim; the SPEC itself declares a 7-slot::5-action M:N)."""
    out: dict[str, Any] = {}
    for c in carriers:
        m = os.path.join(c, "FDA_DESKTOP_CAPABILITY_MATRIX.yaml")
        if not os.path.isfile(m):
            continue
        t = open(m, encoding="utf-8", errors="ignore").read()
        lines = t.splitlines()
        idx = [i for i, l in enumerate(lines) if l.startswith("action_classes:")]
        classes: list[str] = []
        if idx:
            for l in lines[idx[0] + 1:]:
                if re.match(r"^[A-Za-z_]", l):
                    break
                mm = re.match(r"^  ([A-Z][A-Za-z0-9_\-]*):\s*$", l)
                if mm:
                    classes.append(mm.group(1))
        out[c] = {
            "matrix_bytes": os.path.getsize(m),
            "action_classes": classes,
            "live_broker": (re.findall(r"live_broker:\s*(\S+)", t) or [None])[0],
            "has_routing_rules": "routing_rules:" in t,
        }
    return out


def _sha_norm(p: str) -> str:
    """sha256 of the file with CRLF normalised to LF — separates content from EOL policy."""
    b = open(p, "rb").read().replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def fda_inventory(carriers: list[str], slots: list[str],
                  authority_roots: set[str] | None = None) -> dict[str, Any]:
    """Per-carrier artefact inventory + per-slot textual reference count + collision.

    Only the allow-listed artefacts are opened (the allow-list says "exactly the 16 artefact
    paths ... nothing else under FHS/"), and the authority collision verdict is computed over
    allow-listed roots only; a non-allow-listed mirror is reported separately and never feeds
    the authority verdict.
    """
    out: dict[str, Any] = {"carriers": [], "slots": slots,
                           "read_surface": "ALLOW_LISTED_ARTEFACTS_ONLY"}
    for c in carriers:
        entry: dict[str, Any] = {"root": c, "exists": os.path.isdir(c), "artefacts": []}
        if not entry["exists"]:
            out["carriers"].append(entry); continue
        for rel in FDA_ARTEFACTS:
            ap = os.path.join(c, rel.replace("/", os.sep))
            if os.path.isfile(ap):
                s, b = sha_file(ap)
                eol = "CRLF" if b"\r\n" in open(ap, "rb").read() else "LF"
                entry["artefacts"].append({"path": rel, "raw_sha256": s, "bytes": b,
                                           "eol": eol, "content_sha256_lf": _sha_norm(ap)})
            else:
                entry["artefacts"].append({"path": rel, "raw_sha256": None, "bytes": None,
                                           "eol": None, "content_sha256_lf": None})
        # per-slot reference counts across the allow-listed artefacts ONLY (the allow-list
        # ceiling is "exactly the 16 artefact paths"; an unrestricted walk would read beyond it)
        counts = {s: 0 for s in slots}
        for a in entry["artefacts"]:
            if not a["raw_sha256"]:
                continue
            try:
                txt = open(os.path.join(c, a["path"].replace("/", os.sep)),
                           encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for s in slots:
                if s in txt:
                    counts[s] += 1
        entry["slot_reference_counts"] = counts
        out["carriers"].append(entry)

    # collision: same artefact path, different bytes across EXISTING carriers
    real = [c for c in out["carriers"] if c["exists"]]
    if authority_roots:
        auth = [c for c in real if os.path.normcase(c["root"]) in authority_roots]
    else:
        auth = real
    mirror = [c for c in real if c not in auth]

    def _diff(carriers_in: list[dict]) -> tuple[list[dict], list[dict]]:
        coll_: list[dict] = []
        eol_: list[dict] = []
        if len(carriers_in) >= 2:
            for a in FDA_ARTEFACTS:
                raw, norm = {}, {}
                for c in carriers_in:
                    for x in c["artefacts"]:
                        if x["path"] == a and x["raw_sha256"]:
                            raw.setdefault(x["raw_sha256"], []).append(c["root"])
                            norm.setdefault(x["content_sha256_lf"], []).append(c["root"])
                if len(raw) > 1:
                    rec = {"path": a, "distinct_raw_sha256": sorted(raw),
                           "distinct_content_sha256_lf": sorted(norm),
                           "content_identical": len(norm) == 1}
                    coll_.append(rec)
                    if len(norm) == 1:
                        eol_.append(rec)
        return coll_, eol_

    coll, eol_only = _diff(auth)
    content_collision = [c for c in coll if not c["content_identical"]]
    out["authority_collision"] = {
        "detected": bool(coll),
        "byte_level_differences": len(coll),
        "content_level_differences": len(content_collision),
        "carriers_compared": [c["root"] for c in auth],
        "differing_artefacts": coll,
        "verdict": ("AUTHORITY_COLLISION_HOLD" if content_collision else
                    ("IDENTICAL_MODULO_EOL" if coll else
                     ("SINGLE_CARRIER" if len(auth) <= 1 else "CARRIERS_IDENTICAL"))),
        "rule": "byte difference with equal LF-normalised sha is an EOL policy difference, not a build "
                "divergence; only a content-level difference is an Owner decision (SPEC §02 / W0M CH-01)",
        "eol_only_artefacts": [c["path"] for c in eol_only],
        "authority_scope": ("allow-listed roots only" if authority_roots
                            else "all discovered carriers (no allow-list supplied)"),
    }
    if mirror:
        mcoll, meol = _diff(auth[:1] + mirror) if auth else _diff(mirror)
        mcontent = [c for c in mcoll if not c["content_identical"]]
        out["mirror_observation"] = {
            "roots": [c["root"] for c in mirror],
            "status": "MIRROR_CARRIER_UNRATIFIED",
            "byte_level_differences_vs_primary": len(mcoll),
            "content_level_differences_vs_primary": len(mcontent),
            "content_identical_modulo_eol": not mcontent,
            "used_for_authority_verdict": False,
            "why": "the structured allow-list covers the primary carrier only; a mirror is "
                   "observed and reported but cannot carry the EOL/collision verdict (D-2)",
        }
    else:
        out["mirror_observation"] = {"roots": [], "status": "NO_MIRROR_PRESENT",
                                     "used_for_authority_verdict": False}
    return out


# ------------------------------------------------------------------- the ops
def run(repo: str, units: list[dict], fda_carriers: list[str], roots_edges: list[str],
        slots: list[str]) -> dict[str, Any]:
    ident = read_identity(repo)
    tree = list_tree(repo, ident["commit"])
    disk = index_disk(repo)
    started = __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")

    base_rows, fda_rows = [], []
    blob_cache: dict[str, tuple[int, str]] = {}

    # ---- preflight inputs (pinned into the receipt: round-3 checker item 1/10)
    _pf = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "00_PREFLIGHT")

    def _pin(name: str) -> dict[str, Any]:
        p = os.path.join(_pf, name)
        try:
            b = open(p, "rb").read()
        except Exception:
            return {"path": p, "present": False}
        return {"path": p, "present": True, "bytes": len(b),
                "raw_sha256": hashlib.sha256(b).hexdigest()}

    INPUT_PINS = {n: _pin(n) for n in ("b1_locator_bindings.json", "b1_source_allowlist.json")}
    BINDINGS: dict[tuple[str, str], dict] = {}
    ALLOW_ROOTS: set[str] = set()
    ALLOW_ARTEFACTS: dict[str, dict] = {}
    try:
        _b = json.load(open(os.path.join(_pf, "b1_locator_bindings.json"), encoding="utf-8"))
        BINDINGS = {(x["unit"], x["declared_path"]): x for x in _b["bindings"]}
    except Exception:
        BINDINGS = {}
    try:
        _a = json.load(open(os.path.join(_pf, "b1_source_allowlist.json"), encoding="utf-8"))
        if _a.get("root"):
            ALLOW_ROOTS.add(os.path.normcase(_a["root"]))
        ALLOW_ARTEFACTS = {x["path"]: x for x in _a.get("artefacts", [])}
    except Exception:
        pass

    def measure(p: str) -> dict[str, Any]:
        e = tree[p]
        if e["sha"] not in blob_cache:
            blob = read_blob(repo, e["sha"])
            blob_cache[e["sha"]] = (len(blob), hashlib.sha256(blob).hexdigest())
        n, rs = blob_cache[e["sha"]]
        return {"path": p, "git_blob_sha1": e["sha"], "mode": e["mode"], "raw_sha256": rs,
                "bytes": n, "git_bytes_field": e.get("bytes")}

    for u in units:
        sp = u.get("source_payload") or []
        cell = sp[2] if len(sp) > 2 else ""
        cands = declared_candidates(cell)
        src_note = "source_payload[2]"
        if u.get("kind") == "KERNEL":
            alt = path_from_input_rule(u.get("input_rule") or "")
            if alt:
                cands, src_note = alt, "input_rule"
            else:
                cands, src_note = kernel_path(u["key"]), "spec_04_K2_kernel_carrier"
        elif not cands:
            alt = path_from_input_rule(u.get("input_rule") or "")
            if alt:
                cands, src_note = alt, "input_rule"

        # a cell that qualifies one sibling with the carrier path qualifies its bare siblings too
        cpref = None
        for c in cands:
            m = re.search(r"((?:[A-Za-z0-9_.\-]+/)*fabric-desktop-automation/)", c)
            if m:
                cpref = m.group(1)
                break
        if cpref and any("/" not in c for c in cands):
            cands = [(cpref + c) if "/" not in c else c for c in cands]

        row = {"unit_id": u["unit_id"], "key": u["key"], "kind": u["kind"],
               "op_id": u.get("op_id"), "declared_cell": cell, "declared_from": src_note,
               "declared_paths": cands, "case_ids": u.get("case_ids"), "resolutions": [],
               "prefix_propagation": cpref}
        for c in cands:
            r = resolve(c, tree, repo, disk)
            r["measured"] = []
            for h in r["matched"]:
                if h in tree:
                    m = measure(h)
                    if h.endswith(".py"):
                        m["symbols"] = py_symbols(read_blob(repo, tree[h]["sha"]))
                    r["measured"].append(m)
                elif r["classification"] == "FOUND_ELSEWHERE_ON_DISK":
                    ap = os.path.join(repo, h.replace("/", os.sep))
                    if os.path.isfile(ap):
                        s, b = sha_file(ap)
                        r["measured"].append({"path": h, "raw_sha256": s, "bytes": b,
                                              "tracked": False})
            row["resolutions"].append(r)

        classes = {x["classification"] for x in row["resolutions"]}
        trk = classes & {"TRACKED_PRESENT", "TRACKED_GLOB", "TRACKED_DIR_PRESENT"}
        dsk = classes & {"DISK_FILE_UNTRACKED", "DISK_DIR_UNTRACKED"}
        oth = classes & {"FOUND_ELSEWHERE_IN_TREE", "FOUND_ELSEWHERE_ON_DISK"}
        if trk and not (classes & {"ABSENT_IN_TREE", "DISK_FILE_UNTRACKED", "DISK_DIR_UNTRACKED",
                                   "FOUND_ELSEWHERE_IN_TREE", "FOUND_ELSEWHERE_ON_DISK",
                                   "ABSENT_IN_TREE_AND_DISK"}):
            v = "OBSERVED_TRACKED_AT_HEAD"
        elif trk:
            v = "PARTIAL_TRACKED_AND_OTHER"
        elif dsk and not (classes & {"ABSENT_IN_TREE_AND_DISK"}):
            v = "OBSERVED_IN_WORKING_TREE_UNTRACKED"
        elif oth:
            v = "OBSERVED_ELSEWHERE_PATH_DIFFERS"
        else:
            v = "TYPED_MISSING_ABSENT_IN_TREE_AND_DISK"
        row["verdict"] = v
        row["first_fail"] = None if v.startswith("OBSERVED") else (
            "BASE_ROW_MISSING" if u["kind"] == "BASE" else "B1_SOURCE_DECLARED_PATH_MISSING")
        (fda_rows if u["kind"] == "FDA" else base_rows).append(row)

    fda_car = fda_inventory(fda_carriers, slots, authority_roots=ALLOW_ROOTS or None)
    vocab = matrix_vocabulary(fda_carriers)
    fda_car["matrix_vocabulary"] = vocab
    carriers_present = [c for c in fda_car["carriers"] if c["exists"]]
    carrier_files = sum(1 for c in carriers_present
                        for a in c["artefacts"] if a["raw_sha256"])
    for row in fda_rows:
        slot = row["key"].split(":", 1)[1]
        refs = {c["root"]: (c.get("slot_reference_counts") or {}).get(slot)
                for c in carriers_present}
        # the carrier is the real locator; the SPEC's slot name is an author decomposition
        if carriers_present and carrier_files:
            if fda_car["authority_collision"]["content_level_differences"]:
                row["verdict"] = "CARRIER_OBSERVED_AUTHORITY_COLLISION"
                row["first_fail"] = "FDA_CARRIER_AUTHORITY_COLLISION"
            elif fda_car["authority_collision"]["byte_level_differences"]:
                row["verdict"] = "CARRIER_OBSERVED_EOL_ONLY_DIFFERENCE"
                row["first_fail"] = None
            else:
                row["verdict"] = "CARRIER_OBSERVED_SINGLE"
                row["first_fail"] = None
        row["carrier_evidence"] = {
            "verdict": fda_car["authority_collision"]["verdict"],
            "slot": slot,
            "literal_slot_name_hits_in_carrier_source": refs,
            "carrier_action_classes": sorted({k for v in vocab.values()
                                              for k in v["action_classes"]}),
            "live_broker_declared": sorted({v["live_broker"] for v in vocab.values()
                                            if v["live_broker"]}),
        }

    # BASE units whose basename lives in an FDA carrier rather than the brownfield repo.
    # Read surface = the allow-listed artefacts only (the allow-list ceiling is 16 paths).
    carrier_paths: dict[str, set[str]] = {}
    for c in carriers_present:
        present = set()
        for rel in ALLOW_ARTEFACTS:
            if os.path.isfile(os.path.join(c["root"], rel.replace("/", os.sep))):
                present.add(rel)
        carrier_paths[c["root"]] = present
    carrier_index: dict[str, dict[str, list[str]]] = {
        root: {rel.rsplit("/", 1)[-1]: [rel] for rel in sorted(paths)}
        for root, paths in carrier_paths.items()}
    for row in base_rows:
        need = False
        for r in row["resolutions"]:
            dp2 = (r.get("declared_path") or "").replace("\\", "/").lstrip("./")
            hit2 = r.get("matched") or []
            if "*" in dp2:
                p2, _, s2 = dp2.partition("*")
                got = any(h.startswith(p2) and h.endswith(s2) for h in hit2)
            else:
                got = any(h.replace("\\", "/") == dp2 for h in hit2)
            if not got:
                need = True
        if not need:
            continue
        for res in row["resolutions"]:
            dp = (res.get("declared_path") or "").replace("\\", "/").lstrip("./")
            rel = (dp.split("fabric-desktop-automation/", 1)[1]
                   if "fabric-desktop-automation/" in dp else dp)
            is_glob = "*" in rel
            pre, _, suf = rel.partition("*")
            for c in carriers_present:
                if is_glob:
                    hits = sorted(h for h in carrier_paths.get(c["root"], ())
                                  if h.startswith(pre) and h.endswith(suf))
                else:
                    hits = [rel] if rel in carrier_paths.get(c["root"], set()) else []
                for h in hits[:4]:
                    ap = os.path.join(c["root"], h.replace("/", os.sep))
                    s, b = sha_file(ap)
                    res.setdefault("carrier_hits", []).append(
                        {"carrier": c["root"], "path": h, "raw_sha256": s, "bytes": b})
            if not res.get("carrier_hits"):
                # present in a carrier but outside the 16-artefact allow-list: existence is a
                # stat/glob listing (no content read) and must surface as a scope gap, not "absent".
                # Every carrier is recorded (primary first) — collapsing them would name the
                # unratified mirror while dropping the allow-listed primary.
                import glob as _glob
                order = sorted(carriers_present,
                               key=lambda c: os.path.normcase(c["root"]) not in ALLOW_ROOTS)
                for c in order:
                    if "*" in rel:
                        found = sorted(os.path.relpath(p, c["root"]).replace(os.sep, "/")
                                       for p in _glob.glob(os.path.join(
                                           c["root"], rel.replace("/", os.sep))))
                    else:
                        found = [rel] if os.path.isfile(
                            os.path.join(c["root"], rel.replace("/", os.sep))) else []
                    if found:
                        res.setdefault("carrier_present_out_of_scope", []).append(
                            {"carrier": c["root"], "path": rel, "matches": found[:6],
                             "allow_listed_root": os.path.normcase(c["root"]) in ALLOW_ROOTS,
                             "why": "file(s) exist in the carrier but are not among the allow-listed "
                                    "artefacts; reading them would exceed the declared scope"})
            _dp = (res.get("declared_path") or "").replace("\\", "/").lstrip("./")
            _h = res.get("matched") or []
            if "*" in _dp:
                _p, _, _s = _dp.partition("*")
                _repo_exact = any(x.startswith(_p) and x.endswith(_s) and x in tree for x in _h)
            else:
                _repo_exact = any(x.replace("\\", "/") == _dp and x in tree for x in _h)
            # never overwrite a HEAD-tracked classification with a carrier label
            if res.get("carrier_hits") and not _repo_exact:
                res["classification"] = "FOUND_IN_FDA_CARRIER"
                res["note"] = "absent from the brownfield repo; present in an FDA carrier"
        if any(r["classification"] == "FOUND_IN_FDA_CARRIER" for r in row["resolutions"]):
            ac = fda_car["authority_collision"]
            row["verdict"] = ("OBSERVED_IN_FDA_CARRIER_CONTENT_COLLISION"
                              if ac["content_level_differences"]
                              else "OBSERVED_IN_FDA_CARRIER_CONTENT_IDENTICAL")
            row["first_fail"] = "FDA_CARRIER_AUTHORITY_COLLISION" if ac["content_level_differences"] else None
        elif not any(r["classification"] == "ABSENT_IN_TREE_AND_DISK" for r in row["resolutions"]):
            row["verdict"] = "OBSERVED_MIXED_SURFACES"
            row["first_fail"] = None

    roots = [{"edge_id": e, "scope": "PH01 W0", "head": ident["commit"], "evidence": [],
              "physical_status": "UNKNOWN",
              "reason": "no config/import/alias/exec/runtime artefact for this edge; static "
                        "absence is not evidence of removal",
              "missing": ["physical call-chain artefact"]} for e in roots_edges]

    # ---- finalise: declared-path exactness, per-target CommitPathSpan, missing sets, authority
    repo_root = os.path.normcase(os.path.abspath(repo))

    def _finalise(row):
        missing = []
        for res in row["resolutions"]:
            dp = (res.get("declared_path") or "").replace("\\", "/").lstrip("./")
            hits = res.get("matched") or []
            is_glob = "*" in dp
            pre, _, suf = dp.partition("*")
            if is_glob:
                exact = [h for h in hits if h.startswith(pre) and h.endswith(suf)]
            else:
                exact = [h for h in hits if h.replace("\\", "/") == dp]
            tracked = [h for h in exact if h in tree]
            car = res.get("carrier_hits") or []

            def _car_matches(c):
                p = (c.get("path") or "").replace("\\", "/")
                rel = dp
                if "fabric-desktop-automation/" in rel:
                    rel = rel.split("fabric-desktop-automation/", 1)[1]
                if is_glob:
                    rp, _, rs = rel.partition("*")
                    return p.startswith(rp) and p.endswith(rs)
                return p == rel

            car_exact = [c for c in car if _car_matches(c)]
            # explicit locator binding (declared cell omitted a directory qualifier): identity is
            # the bound full path + raw sha256, re-verified by MEASURING the file (not an echo)
            bind = BINDINGS.get((row["key"], res["declared_path"]))
            bind_ok, bind_measured = False, None
            if bind:
                try:
                    s2, b2 = sha_file(bind["resolved_path"])
                    bind_ok = (s2 == bind["raw_sha256"] and b2 == bind.get("bytes", b2))
                    if bind_ok:
                        bind_measured = {"path": bind["resolved_path"], "raw_sha256": s2,
                                         "bytes": b2, "measured": True, "tracked": False,
                                         "binding_ratification": bind.get("ratification")}
                except Exception:
                    bind_ok = False
            repo_exact = bool(tracked)          # present AT the declared path IN the HEAD tree
            carrier_unit = bool(row.get("prefix_propagation")) or any(
                "fabric-desktop-automation" in (c or "") for c in row["declared_paths"])
            conf = ("EXACT" if (exact or car_exact or bind_ok) else
                    ("BASENAME_ONLY" if (hits or car) else "NONE"))
            if repo_exact:
                src, dom = tracked[0], "REPO_ROOT"
            elif car_exact and (carrier_unit or not exact):
                src, dom = car_exact[0]["path"], "EXTERNAL_CARRIER"
            elif exact:
                src, dom = exact[0], "DISK_AT_DECLARED_PATH"    # untracked, where declared
            elif car_exact:
                src, dom = car_exact[0]["path"], "EXTERNAL_CARRIER"
            elif bind_ok:
                src, dom = bind["resolved_path"], bind["authority"]["read_domain"]
            else:
                src, dom = None, "NONE"
            if bind_ok and bind_measured:
                res["measured"] = [bind_measured] + [m for m in (res.get("measured") or [])]
            if car_exact:
                # measure the carrier artefact itself (a hash, not an echo of the allow-list entry)
                res["measured"] = [{"path": os.path.join(c["carrier"], c["path"]),
                                    "carrier": c["carrier"], "rel": c["path"],
                                    "raw_sha256": c["raw_sha256"], "bytes": c["bytes"],
                                    "measured": True, "tracked": False}
                                   for c in car_exact[:2]] + [m for m in (res.get("measured") or [])]
            if bind_ok and not repo_exact and not car_exact:
                res["classification"] = "FOUND_BY_LOCATOR_BINDING"
            res["locator_binding"] = ({"used": True, "resolved_path": bind["resolved_path"],
                                       "raw_sha256": bind["raw_sha256"],
                                       "ratification": bind["ratification"]} if bind_ok else None)
            res["locator_confidence"] = conf
            res["declared_path_exact"] = conf == "EXACT"
            res["resolved_relative_path"] = src
            res["read_domain"] = dom
            res["outside_repo_root"] = dom == "EXTERNAL_CARRIER"
            # commit identity exists ONLY for a tracked repo-tree hit; never fabricate one
            res["commit"] = ident["commit"] if repo_exact else None
            res["commit_reason"] = (
                None if repo_exact else
                ("locator binding: declared cell omits a directory qualifier; identity is the full "
                 "path + measured raw sha, not a basename match (CANDIDATE_NOT_RATIFIED)"
                 if bind_ok else
                 ("carrier artefact: no brownfield commit identity exists outside the "
                  "brownfield repo (the carrier may have its own git history)"
                  if dom == "EXTERNAL_CARRIER" else
                  ("disk-only (untracked): no commit identity exists"
                   if dom == "DISK_AT_DECLARED_PATH" else
                   "no locator resolved at the declared path"))))
            measured_sha = None
            if dom == "EXTERNAL_CARRIER" and car_exact:
                measured_sha = car_exact[0]["raw_sha256"]
            elif bind_ok and bind_measured:
                measured_sha = bind_measured["raw_sha256"]
            root, rel_hit = None, None
            if dom == "REPO_ROOT":
                root = repo
            elif dom == "EXTERNAL_CARRIER":
                if car_exact:
                    root, rel_hit = car_exact[0]["carrier"], car_exact[0]["path"]
                elif bind_ok:
                    rp = bind["resolved_path"].replace("\\", "/")
                    for rel, _ent in ALLOW_ARTEFACTS.items():
                        if rp.endswith("/" + rel):
                            root, rel_hit = rp[:-(len(rel) + 1)], rel
                            break
            al_root = bool(root) and os.path.normcase(root) in ALLOW_ROOTS
            al_art = bool(rel_hit) and rel_hit in ALLOW_ARTEFACTS
            al_sha = bool(measured_sha and al_art
                          and measured_sha == ALLOW_ARTEFACTS[rel_hit]["raw_sha256"])
            allow_declared = dom == "REPO_ROOT" or (al_root and al_art and al_sha)
            if dom == "REPO_ROOT":
                al_root = al_art = al_sha = None      # allow-list governs the external read surface only
            res["authority"] = {
                "root": root,
                "allow_list_declared": allow_declared,
                "allow_list_root_ok": al_root,
                "allow_list_artefact_ok": al_art,
                "allow_list_sha_ok": al_sha,
                "artefact_rel": rel_hit,
                "outside_repo_root": dom == "EXTERNAL_CARRIER",
                "note": ("within the authorised RepoRoot" if dom == "REPO_ROOT" else
                         ("carrier artefact covered by the per-artefact allow-list entry "
                          "(root + path + measured sha)" if allow_declared else
                          ("carrier artefact NOT covered by a per-artefact allow-list entry; "
                           "no effect may rely on it" if dom == "EXTERNAL_CARRIER"
                           else "no locator resolved"))),
            }
            if conf != "EXACT":
                oos = res.get("carrier_present_out_of_scope")
                missing.append({"declared_path": res.get("declared_path"),
                                "reason": ("OUT_OF_ALLOW_LIST_SCOPE" if oos else
                                           ("BASENAME_ONLY_AMBIGUOUS" if conf == "BASENAME_ONLY"
                                            else "ABSENT")),
                                "basename_hits": (hits + [c["path"] for c in car])[:6],
                                **({"out_of_scope": oos} if oos else {})})
        row["missing"] = missing
        if missing:
            reasons = {m["reason"] for m in missing}
            if reasons == {"OUT_OF_ALLOW_LIST_SCOPE"}:
                row["verdict"] = "TYPED_MISSING_OUT_OF_ALLOW_LIST_SCOPE"
                row["first_fail"] = "B1_SOURCE_OUT_OF_ALLOW_LIST_SCOPE"
                row["scope_gap"] = ("the declared evidence exists in the carrier but is not one of "
                                    "the 16 allow-listed artefacts; extending the allow-list is an "
                                    "Owner act (D-2), not a Maker default")
            else:
                # never claim OBSERVED when a declared target has no declared-path-exact locator
                row["verdict"] = ("TYPED_MISSING_ABSENT_IN_TREE_AND_DISK"
                                  if reasons == {"ABSENT"} else
                                  "PARTIAL_BASENAME_ONLY_NOT_ACCEPTED"
                                  if reasons == {"BASENAME_ONLY_AMBIGUOUS"} else
                                  "PARTIAL_SCOPE_GAP_NOT_ACCEPTED")
                row["first_fail"] = ("BASE_ROW_MISSING" if row["key"].startswith("BASE-")
                                     else "B1_SOURCE_DECLARED_PATH_MISSING")
            row["claim_ceiling"] = "LOCATOR_NOT_EXACT"

    for row in base_rows:
        _finalise(row)
    return {"schema": SCHEMA, "subject": SUBJECT, "original_wave": WAVE, "bid": BID,
            "generated_at": started, "effect": "SOURCE_READ", "write_set": [],
            "preimage": "N/A", "repo": ident, "tree_entries": len(tree),
            "inputs": INPUT_PINS,
            "allow_list": {"roots": sorted(ALLOW_ROOTS),
                           "artefact_count": len(ALLOW_ARTEFACTS),
                           "artefact_paths": sorted(ALLOW_ARTEFACTS)},
            "disk_files_indexed": sum(len(v) for v in disk.values()),
            "ops": {
                "B1.REPO": {"typed_output": "RepoReadSet.commit/path/blob/missing",
                            "commit": ident["commit"], "tree": ident["tree"],
                            "local_head_equals_remote": (ident["remote_head"] == ident["commit"]
                                                         if ident["remote_head"] else None),
                            "remote_vs_local": {"local": ident["commit"],
                                                "remote": ident["remote_head"],
                                                "state": ident["remote_state"]},
                            "dirty": ident["dirty"],
                            "missing": sorted({m["declared_path"] for r in base_rows
                                               for m in r.get("missing", [])})},
                "B1.BASE": {"typed_output": "CommitPathSpan", "rows": base_rows},
                "B1.FDA": {"typed_output": "7 slot source/lease/raw status", "rows": fda_rows,
                           "carrier_inventory": fda_car,
                           "live_submit": {"slot": "FDA:broker_live_submit",
                                           "invariant": "DENY_INVARIANT",
                                           "allowed_effect_pos": None,
                                           "note": "no token/connector; never executed"}},
                "B1.ROOTS": {"typed_output": "UnknownPhysicalEdgeSet", "rows": roots}}}
