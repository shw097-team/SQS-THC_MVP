#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 product: four real Ops over the original units.

JOIN   — B0 SourceReadSet/2 x B2 ToolReadSet, per-atom, with the original mandatory fields
CHILD  — the original 11 Child + 92 DOC_BRIDGE + 11 Protected, each verified against its own pin
ROUTE  — a real router: per-key PH/W/B, expected-set snapshot, consumer and HOLD/ROUTE_OUT
COMMIT — a single guarded file write with containment, preimage ABSENT and readback

Nothing here is a projection of the tool read set dressed up as a ledger: every row carries the
unit id, the original key, the kind and the evidence that was actually recomputed.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time

K = r"<LOCAL_ROOT>\SQS\【1】SST_PLP_PH01-04"
W = r"<LOCAL_ROOT>\71_W0_B0-B3_R7_20261127"
OPS = os.path.join(W, "40_OPS")
DEV = os.path.join(W, "20_DEV")
LEDGER_DIR = os.path.join(W, "40_OPS", "b3_ledger")
WINDOW = os.path.expanduser("~/.hgk-owner/window.json")

REF = re.compile(r"^(?P<path>.+?)@(?P<sha>[0-9a-f]{64}):L(?P<a>\d+)[–\-]L?(?P<b>\d+)$")
LOCATOR_FIXES = (("W0_B0-m\\", "W0_B0-B8\\"), ("PHASE 00~04", "PHASE 01-04"))
EFFECT_ORDER = ("READ_ONLY_PROBE", "REPOSITORY_WRITE", "HOST_OPERATIONS", "USER_DATA_EFFECT")

# original routing table: kind -> the wave/batch the route hands off to, from B3 §03/§04
ROUTE_TARGET = {
    "CHILD": ("E00", "B4", "ledger_atom"),
    "PROTECTED": ("E00", "B4", "protected_clause"),
    "DOC_BRIDGE": ("E00", "B7", "document_bridge"),
    "H1_ROUTE": ("E00", "B7", "h1_route"),
    "CHILD_ROUTE": ("E00", "B5", "child_route"),
    "BEHAVIOR_ROUTE": ("E00", "B7", "behavior_route"),
    "AUTHORITY_SEAM": ("E00", "B4", "authority_seam"),
    "RECOVERY": ("E00", "B7", "recovery"),
}


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


_CACHE: dict[str, bytes] = {}


def read_bytes(p: str) -> bytes:
    """One read per file per process: the mutation loop re-verifies the same sources."""
    b = _CACHE.get(p)
    if b is None:
        b = open(p, "rb").read()
        _CACHE[p] = b
    return b


def sha_file(p: str) -> str:
    return sha_bytes(read_bytes(p))


def window_state() -> dict:
    try:
        return json.load(open(WINDOW, encoding="utf-8"))
    except Exception:
        return {}


def effect_allowed(required: str) -> tuple[bool, str]:
    """The window in force must be open, unexpired and its ceiling must cover the effect."""
    w = window_state()
    if not w:
        return False, "OWNER_WINDOW_UNBOUND"
    if w.get("state") != "OPEN":
        return False, "OWNER_WINDOW_CLOSED"
    if int(w.get("expires_at", 0)) <= int(time.time()):
        return False, "OWNER_WINDOW_EXPIRED"
    ceil = w.get("effect_class_ceiling")
    if ceil not in EFFECT_ORDER:
        return False, "EFFECT_CLASS_UNKNOWN"
    if EFFECT_ORDER.index(ceil) < EFFECT_ORDER.index(required):
        return False, f"EFFECT_CLASS_INSUFFICIENT:{ceil}<{required}"
    return True, f"OWNER_WINDOW:{w.get('window_id')}:{ceil}"


# ---------------------------------------------------------------- slices / pins
_LINES: dict[int, tuple[bytes, list[tuple[int, int]]]] = {}


def _line_table(raw: bytes) -> list[tuple[int, int]]:
    """Physical line table for one bytes object, computed once per process.

    The r7 re-run calls this 1,092 times over files up to 12 MB; rebuilding the table on
    every call spent 96 s of the 107 s product run in bytes.find. Offsets are identical
    to the previous per-call scan (CRLF counts as one terminator, a lone CR terminates).
    """
    ent = _LINES.get(id(raw))
    if ent is not None and ent[0] is raw:
        return ent[1]
    lines, pos = [], 0
    while pos < len(raw):
        nl = raw.find(b"\n", pos)
        cr = raw.find(b"\r", pos)
        if nl == -1 and cr == -1:
            lines.append((pos, len(raw)))
            break
        if cr != -1 and (nl == -1 or cr < nl):
            end = cr + 2 if raw[cr:cr + 2] == b"\r\n" else cr + 1
            lines.append((pos, end))
        else:
            lines.append((pos, nl + 1))
        pos = lines[-1][1]
    _LINES[id(raw)] = (raw, lines)
    return lines


def _slice(raw: bytes, a: int, b: int):
    lines = _line_table(raw)
    if a < 1 or b < a or b > len(lines):
        return None
    return raw[lines[a - 1][0]:lines[b - 1][1]]


def resolve_pin(ref: str):
    m = REF.match(ref or "")
    if not m:
        return None
    d = m.groupdict()
    d["a"], d["b"] = int(d["a"]), int(d["b"])
    return d


def verify_mapping(unit: dict) -> dict:
    dp, rs = resolve_pin(unit.get("direct_parent_ref")), resolve_pin(unit.get("resolved_source_ref"))
    out = {"direct_parent_ref": unit.get("direct_parent_ref"),
           "resolved_source_ref": unit.get("resolved_source_ref"), "binding": None}
    if not (dp and rs):
        return {**out, "decision": "REF_NOT_PARSEABLE"}
    rp = rs["path"]
    if not os.path.isfile(rp):
        for a, b in LOCATOR_FIXES:
            rp = rp.replace(a, b)
    if not os.path.isfile(rp):
        return {**out, "decision": "RESOLVED_SOURCE_ABSENT"}
    if sha_file(rp) != rs["sha"]:
        return {**out, "decision": "RESOLVED_SOURCE_CHANGED"}
    if _slice(read_bytes(rp), rs["a"], rs["b"]) is None:
        return {**out, "decision": "RESOLVED_SPAN_OUT_OF_RANGE"}
    dpp = dp["path"]
    if not os.path.isfile(dpp):
        for a, b in LOCATOR_FIXES:
            cand = dpp.replace(a, b)
            if os.path.isfile(cand):
                out["binding"] = {"declared": dp["path"], "resolved": cand,
                                  "ratification": "CANDIDATE_NOT_RATIFIED"}
                dpp = cand
                break
    if not os.path.isfile(dpp):
        return {**out, "decision": "DIRECT_PARENT_ABSENT"}
    praw = read_bytes(dpp)
    if sha_bytes(praw) != dp["sha"]:
        return {**out, "decision": "DIRECT_PARENT_CHANGED"}
    sl = _slice(praw, dp["a"], dp["b"])
    if sl is None:
        return {**out, "decision": "DIRECT_SPAN_OUT_OF_RANGE"}
    got = sha_bytes(sl)
    out["clause_sha_observed"], out["clause_sha_expected"] = got, unit.get("direct_clause_sha")
    out["clause_text_head"] = sl[:120].decode("utf-8", "replace")
    out["decision"] = ("SOURCE_BOUND_VERIFIED" if got == unit.get("direct_clause_sha")
                       else "DIRECT_CLAUSE_SHA_MISMATCH")
    return out


_INDEX: dict[str, list[str]] | None = None


def _name_index() -> dict[str, list[str]]:
    """filename -> paths under the authorised roots (one walk per process, sorted for determinism)."""
    global _INDEX
    if _INDEX is None:
        idx: dict[str, list[str]] = {}
        for root in (K, os.path.join(K, "PHASE 01-04")):
            for dirpath, dns, fns in os.walk(root, onerror=lambda e: None, followlinks=False):
                dns[:] = [d for d in dns if d not in {".git", "__pycache__", "node_modules"}]
                for f in fns:
                    idx.setdefault(f, []).append(os.path.join(dirpath, f))
        for v in idx.values():
            v.sort()
        _INDEX = idx
    return _INDEX


def doc_bridge(unit: dict) -> dict:
    t = unit.get("source_payload")
    t = "\n".join(x for x in t if isinstance(x, str)) if isinstance(t, list) else str(t)
    m = re.search(r"`([^`]+\.md)`", t)
    sha = re.search(r"`([0-9a-f]{64})`", t)
    span = re.search(r"`L(\d+)-L(\d+)`", t)
    heads = re.search(r"headings=(\d+)", t)
    if not (m and sha and span):
        return {"decision": "PIN_NOT_PARSEABLE"}
    name = m.group(1)
    cand = None
    # authorised roots only: the PH01 tree, not the whole workspace.
    # The walk is indexed once per process (name -> candidate paths) instead of re-walking
    # the tree for every DOC unit; identity is still decided by raw sha256, never by name.
    for p in _name_index().get(name, []):
        if sha_file(p) == sha.group(1):
            cand = p
            break
    if cand is None:
        return {"decision": "SOURCE_ABSENT", "document": name}
    raw = read_bytes(cand)
    a, b = int(span.group(1)), int(span.group(2))
    sl = _slice(raw, a, b)
    if sl is None:
        return {"decision": "SPAN_OUT_OF_RANGE", "line_count": len(raw.splitlines())}
    rec = {"document": name, "resolved": cand, "span": [a, b]}
    if heads:
        n = sum(1 for ln in sl.decode("utf-8", "replace").splitlines() if re.match(r"^#{1,6} ", ln))
        rec["headings_observed"], rec["headings_expected"] = n, int(heads.group(1))
    return {**rec, "decision": "SOURCE_BOUND_VERIFIED"}


# ---------------------------------------------------------------- ops
def op_join(units: list[dict], tool_readset: dict, source_side: dict) -> dict:
    """Real per-atom join: the atom must exist in the tool read set AND carry its mandatory fields."""
    rows, errors = [], []
    seen = set()
    declared = set((tool_readset.get("namespace") or {}).keys()) or {
        "R3-REGISTRY-Q1", "R3-REGISTRY-Q2", "R3-REGISTRY-Q3", "R3-REGISTRY-Q4"}
    # B3 atoms and B2 rows are different key spaces (REQ-xx / PLP-xx vs R3-REGISTRY-..::ROW=n),
    # so the relation is by TOOL ID: an atom that names a tool joins to that tool's rows.
    by_tool, by_key = {}, {}
    for e in tool_readset.get("entries") or []:
        by_key.setdefault(e.get("tool_key"), e)
        for tid in re.findall(r"TECH-\d+", e.get("tool_key") or ""):
            by_tool.setdefault(tid, []).append(e)

    def tool_ids_of(u):
        blob = json.dumps(u, ensure_ascii=False)
        return sorted(set(re.findall(r"TECH-\d+", blob)))
    for u in units:
        key = u.get("key")
        ns = key.split("::")[0] if key.startswith("R3-REGISTRY-") else None
        tids = tool_ids_of(u)
        rows_for = [r for tid in tids for r in by_tool.get(tid, [])]
        e = by_key.get(key) or (rows_for[0] if rows_for else None)
        row = {"unit_id": u["unit_id"], "key": key, "kind": u.get("kind"),
               "namespace": ns, "b0_side": source_side.get("kind"),
               "tool_ids": tids, "tool_rows": len(rows_for), "missing": []}
        if ns and ns not in declared:
            errors.append({"code": "NAMESPACE_JOIN_DENY", "key": key})
            row["missing"].append({"field": "namespace", "reason": "AMBIGUOUS"})
        if key in seen:
            errors.append({"code": "DUPLICATE_ATOM_DENY", "key": key})
            row["missing"].append({"field": "atom", "reason": "AMBIGUOUS"})
        seen.add(key)
        if not tids and e is None:
            row["tool_binding"] = "NOT_APPLICABLE_NO_TOOL_REF"
        elif e is None:
            row["missing"].append({"field": "tool_row", "reason": "ABSENT",
                                   "detail": f"the atom names {tids} but no B2 row carries it"})
        if e is not None:
            row["requiredness"] = e.get("requiredness")
            if e.get("requiredness") in (None, "UNKNOWN"):
                row["missing"].append({"field": "requiredness", "reason": "UNVERIFIED"})
            if e.get("source_row") in (None, ""):
                row["missing"].append({"field": "source_row", "reason": "ABSENT",
                                       "detail": "no authorised equivalent locator exists"})
            if not e.get("metadata") and "metadata" not in (e.get("missing") or [{}])[0].get("field", ""):
                pass  # metadata is a B5 concern; B3 does not require it
        if source_side.get("kind") != "READSET":
            row["missing"].append({"field": "b0_source_readset", "reason": "UNVERIFIED"})
        # the atom's own source must verify, not just the envelope's presence
        ev = doc_bridge(u) if u.get("kind") == "DOC_BRIDGE" else verify_mapping(u)
        row["source_check"] = ev.get("decision")
        if ev.get("decision") != "SOURCE_BOUND_VERIFIED":
            row["missing"].append({"field": "source_verified", "reason": "UNVERIFIED",
                                   "detail": ev.get("decision")})
        # Two different readiness claims, kept apart: a source-bound atom is not an
        # admissible ledger row. The owner field is literally "#" in 365/365 units and no
        # atom carries a ratification, so the admission half is 0 by measurement, not by mood.
        owner, owner_basis = declared_owner(u)
        row["owner"] = owner
        row["owner_basis"] = owner_basis
        row["owner_bound"] = bool(owner)
        # Two different acceptances, kept apart: the SPEC's own locators are adopted (A6),
        # while the semantic half needs the original Reader, which is absent. The second is a
        # ReadyAccept criterion, not a ReadyExecute blocker.
        row["ratification"] = {"locator": "SPEC_ADOPTED_A6",
                               "semantic": "ORIGINAL_READER_ABSENT"}
        row["source_bound_ready"] = not row["missing"]
        admission_blockers = []
        if not row["owner_bound"]:
            admission_blockers.append({"field": "owner", "reason": "UNBOUND",
                                       "detail": f"owner basis {owner_basis}; a row may not be "
                                                 "admitted or routed to B4 on an undeclared owner"})
        row["admission_blockers"] = admission_blockers
        row["admission_ready"] = row["source_bound_ready"] and not admission_blockers
        rows.append(row)
    return {"rows": rows, "errors": errors,
            "summary": {"rows": len(rows),
                        "source_bound_ready": sum(1 for r in rows if r["source_bound_ready"]),
                        "admission_ready": sum(1 for r in rows if r["admission_ready"]),
                        "held": sum(1 for r in rows if r["missing"]),
                        "errors": len(errors)}}


_OWNER_RE = re.compile(r"Owner\s*[=：:]\s*([^；;\n」。]+)")


def _payload_text(u: dict) -> str:
    p = u.get("source_payload")
    if isinstance(p, str):
        return p
    if isinstance(p, list):
        return "\n".join(x for x in p if isinstance(x, str))
    return ""


def declared_owner(u: dict) -> tuple[str | None, str]:
    """Owner as the unit actually declares it.

    The previous fallback was `(source_payload or [None])[0]`, which on a string payload
    returns the first CHARACTER — that is where the literal '#' in 365/365 rows came from.
    Now: an explicit `owner` field, else the clause's own `Owner=` line, else nothing, with
    the basis recorded so a blocker can name its cause.
    """
    if isinstance(u.get("owner"), str) and u["owner"].strip():
        return u["owner"].strip(), "UNIT_FIELD"
    m = _OWNER_RE.search(_payload_text(u))
    if m:
        return m.group(1).strip(), "CLAUSE_TEXT"
    return None, "NOT_DECLARED_IN_UNIT"


def op_child(units: list[dict]) -> dict:
    """The original Child / Protected / DOC_BRIDGE atoms, each verified, with owner+scope+source_sha."""
    out = []
    for u in units:
        if u.get("kind") not in ("CHILD", "PROTECTED", "DOC_BRIDGE"):
            continue
        ev = doc_bridge(u) if u.get("kind") == "DOC_BRIDGE" else verify_mapping(u)
        out.append({"atom": u.get("key"), "unit_id": u["unit_id"], "kind": u.get("kind"),
                    "owner": declared_owner(u)[0], "owner_basis": declared_owner(u)[1],
                    "source_sha": ev.get("clause_sha_observed") or ev.get("resolved"),
                    "evidence": ev,
                    "disposition": ("READY_ATOM" if ev["decision"] == "SOURCE_BOUND_VERIFIED"
                                    else "HOLD")})
    return {"atoms": out,
            "summary": {"atoms": len(out),
                        "ready": sum(1 for a in out if a["disposition"] == "READY_ATOM"),
                        "held": sum(1 for a in out if a["disposition"] == "HOLD")}}


def op_route(units: list[dict], child: dict) -> dict:
    """A real router: per key emit PH/W/B, consumer, expected-set snapshot and HOLD/ROUTE_OUT."""
    idx = {a["atom"]: a for a in child["atoms"]}
    routes = []
    for u in units:
        kind = u.get("kind")
        target = ROUTE_TARGET.get(kind)
        if not target:
            continue
        wave, consumer, route_kind = target
        ev = idx.get(u.get("key"), {}).get("evidence") or verify_mapping(u)
        ok = ev.get("decision") == "SOURCE_BOUND_VERIFIED"
        owner_ok = bool(declared_owner(u)[0])
        # A route may only leave when the source verifies AND the owner is bound. Without an
        # owner a ROUTE_OUT would name a consumer of a row nobody owns, which is exactly the
        # ROUTE_OUT/null-owner shape the separated checker rejected.
        route_out = ok and owner_ok
        routes.append({"atom": u.get("key"), "unit_id": u["unit_id"], "kind": kind,
                       "PH": "PH01", "W": wave, "B": consumer, "route_kind": route_kind,
                       "consumer": consumer,
                       "expected_set_snapshot": {"direct_clause_sha": u.get("direct_clause_sha"),
                                                 "payload_sha": u.get("payload_sha")},
                       "source_verified": ok, "owner_bound": owner_ok,
                       "route_out": "ROUTE_OUT" if route_out else "HOLD",
                       "first_fail": (None if route_out else
                                      (ev.get("decision") if not ok else "ROUTE_OWNER_UNBOUND")),
                       "owner": declared_owner(u)[0], "owner_basis": declared_owner(u)[1]})
    return {"routes": routes,
            "summary": {"routes": len(routes),
                        "source_bound": sum(1 for r in routes if r["source_verified"]),
                        "route_out": sum(1 for r in routes if r["route_out"] == "ROUTE_OUT"),
                        "hold": sum(1 for r in routes if r["route_out"] == "HOLD")}}


def op_commit(ledger: dict, name: str = "SourceChildLedger.draft.md") -> dict:
    """Single guarded write: containment, preimage ABSENT, exclusive create, readback."""
    ok, ref = effect_allowed("REPOSITORY_WRITE")
    if not ok:
        return {"decision": "NOT_COMMITTED", "first_fail": ref,
                "note": "the Ops run in memory; the product write needs a window whose ceiling "
                        "covers REPOSITORY_WRITE"}
    os.makedirs(LEDGER_DIR, exist_ok=True)
    root = os.path.realpath(LEDGER_DIR)
    path = os.path.realpath(os.path.join(root, name))
    if os.path.commonpath([root, path]) != root:
        return {"decision": "REFUSED", "first_fail": "PATH_ESCAPES_OUTPUT_ROOT"}
    if os.path.dirname(path) != root:
        return {"decision": "REFUSED", "first_fail": "NOT_SINGLE_FILE_IN_ROOT"}
    if os.path.exists(path):
        return {"decision": "NOT_COMMITTED", "first_fail": "PREIMAGE_NOT_ABSENT", "path": path}
    body = ledger.encode("utf-8")
    # exclusive create: 'x' fails if the file appeared between the check and the open
    with open(path, "xb") as f:
        f.write(body)
    readback = open(path, "rb").read()
    return {"decision": "COMMITTED", "path": path, "bytes": len(readback),
            "sha256": sha_bytes(readback), "preimage": "ABSENT",
            "postimage_verified": readback == body, "write_set": [path],
            "rights_ref": ref, "single_file": True, "effect": "LOCAL_DRAFT_WRITE"}


def render_ledger(join: dict, child: dict, route: dict, units: list[dict]) -> str:
    L = ["# SourceChildLedger.draft", "",
         "generated_at: NOT_IN_BODY - the wall clock lives in the receipt, so the ledger digest is reproducible",
         "claim_ceiling: DRAFT_ONLY - not a product outcome, not an ACK",
         f"units: {len(units)}",
         f"source_bound_ready: {join['summary']['source_bound_ready']}",
         f"admission_ready: {join['summary']['admission_ready']}",
         f"join_held: {join['summary']['held']}",
         f"child_ready: {child['summary']['ready']}", f"child_held: {child['summary']['held']}",
         f"routes_out: {route['summary']['route_out']}", f"routes_hold: {route['summary']['hold']}",
         "", "## atoms", ""]
    for a in child["atoms"]:
        L.append(f"- {a['atom']} | {a['kind']} | {a['disposition']} | "
                 f"{(a['evidence'] or {}).get('decision')}")
    L += ["", "## routes", ""]
    for r in route["routes"]:
        L.append(f"- {r['atom']} | {r['PH']}/{r['W']}/{r['B']} | {r['route_out']}"
                 + (f" | {r['first_fail']}" if r["first_fail"] else ""))
    L += ["", "## holds", ""]
    for row in join["rows"]:
        if row["missing"]:
            L.append(f"- {row['key']} | " + ", ".join(f"{m['field']}:{m['reason']}"
                                                     for m in row["missing"]))
    return "\n".join(L) + "\n"


def run(dry_run: bool = False) -> dict:
    import sys
    sys.path.insert(0, DEV)
    import w0_spec as SPEC
    spec = SPEC.load("B3")
    units = SPEC.units(spec["text"])
    tool = json.load(open(os.path.join(OPS, "b2_r7_tool_readset.json"), encoding="utf-8"))
    src = {"kind": "READSET"}
    if os.path.isfile(os.path.join(OPS, "b0_r7_sourcereadset.json")):
        rd = json.load(open(os.path.join(OPS, "b0_r7_sourcereadset.json"), encoding="utf-8"))
        if rd.get("wire_version") == "SST.B0.SourceReadSet/2":
            src = {"kind": "READSET", "wire_version": rd["wire_version"],
                   "spec_version": rd.get("spec_version"),
                   "sources": [e["source_ref"]["source_id"] for e in rd.get("entries") or []]}
    join = op_join(units, tool, src)
    child = op_child(units)
    route = op_route(units, child)
    ledger = render_ledger(join, child, route, units)
    lname = os.environ.get("B3_LEDGER_NAME", "SourceChildLedger.draft.md")
    commit = {"decision": "DRY_RUN"} if dry_run else op_commit(ledger, name=lname)
    out = {"schema": "SST.PH01.W0.B3.Product@1", "generated_at": now(),
           "spec_b3_sha256": spec["raw_sha256"], "units": len(units),
           "join": join["summary"], "child": child["summary"], "route": route["summary"],
           "commit": commit, "fin_order": "DENY",
           "effect": "SOURCE_READ+IN_MEMORY_TRANSFORM" if commit.get("decision") != "COMMITTED"
                     else "SOURCE_READ+IN_MEMORY_TRANSFORM+LOCAL_DRAFT_WRITE",
           "ledger_sha256": sha_bytes(ledger.encode("utf-8")),
           "errors": join["errors"][:20]}
    p = os.path.join(OPS, "b3_r7_product.json")
    json.dump({**out, "rows_sample": join["rows"][:5], "routes": route["routes"],
               "atoms": child["atoms"]},
              open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    import sys
    print(json.dumps(run(dry_run="--dry-run" in sys.argv), ensure_ascii=False, indent=1))
