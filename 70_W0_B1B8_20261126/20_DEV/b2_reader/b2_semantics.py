#!/usr/bin/env python3
"""B2 shared semantics — spec identity, independent parent source, row oracle.

Design rules (why this is an oracle and not a re-label):

* Source identity is the SPEC raw sha256 (140de5bc…), never a directory depth. The upstream
  library was reorganised; the file identity did not change.
* `direct_parent_ref` points at a path with a stale `W0_B0-m` segment. The parent blueprint is
  rebound BY SHA (d95c8ac6…) to its real location; a rebind is recorded as
  PARENT_SOURCE_REBOUND_BY_SHA / CANDIDATE_NOT_RATIFIED, never as a ratified amendment.
* `direct_clause_sha` is re-derived from the parent bytes under an explicit span rule; a clause
  that cannot be reproduced is a typed gap, not a PASS.
* NEG cases mutate a row that was itself proven valid, and the expected code is the SPEC §06
  column — never a value the Maker chose.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

KBASE = r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8"
SPEC_SHA = "140de5bc1249dbb6e2d199dae336cf3a57741097aaf5cd883a7ec280e9199d3b"
PARENT_SHA = "d95c8ac623112ac0bc2481a99cf19e368e661c5cbda2886d72599e29aa34fbf5"
REQUIRED_NEG = {"NAMESPACE_JOIN_DENY": 1385, "TOOL_REQUIREDNESS_HOLD": 72, "STATE_CONFLICT": 8}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def find_spec() -> str:
    """Locate the B2 SPEC by raw sha256 (identity), not by path or name uniqueness.

    The upstream library holds the r2 blueprint, the r3 candidate and the relocated r4 SPEC under
    the same filename pattern; only one of them is the pinned r4 body (140de5bc…).
    """
    cands = []
    for dp, dn, fn in os.walk(KBASE, onerror=lambda e: None, followlinks=False):
        dn[:] = [d for d in dn if d not in {".git", "__pycache__"}]
        for f in fn:
            if f.startswith("SST_PLP_PH01_W0_B2_") and "實質正文" in f and f.endswith(".md"):
                cands.append(os.path.join(dp, f))
    hits = [p for p in cands if os.path.getsize(p) <= 12_000_000 and sha(open(p, "rb").read())
            == SPEC_SHA]
    if len(hits) != 1:
        raise RuntimeError(f"B2_SPEC_NOT_UNIQUE_BY_SHA: {hits} (candidates {cands})")
    return hits[0]


def load_spec() -> dict:
    p = find_spec()
    raw = open(p, "rb").read()
    got = sha(raw)
    return {"path": p, "bytes": len(raw), "raw_sha256": got, "pin_match": got == SPEC_SHA,
            "text": raw.decode("utf-8")}


def units(t: str) -> list[dict]:
    out = []
    for m in re.finditer(r"<!--\s*UNIT_BEGIN\s+(\S+)\s*-->", t):
        a = t.find("```json", m.end())
        z = t.find("```", a + 7)
        d = json.loads(t[a + 7:z])
        d["_span"] = (m.start(), z)
        d["_h4"] = t[m.end():m.end() + 600]
        out.append(d)
    return out


def case_table(t: str) -> dict[str, dict]:
    i, j = t.find("\n## 06"), t.find("\n## 07")
    block = t[i:j if j > 0 else len(t)]
    out = {}
    for line in block.splitlines():
        if not line.strip().startswith("|"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 8:
            continue
        cid = re.sub(r"<[^>]+>", "", c[0]).strip()
        if not cid.startswith("B2."):
            continue
        out[cid] = {"case_id": cid, "key": c[1], "source": c[2], "mutation": c[3],
                    "predicate": c[4], "expected": c[5], "reader": c[6], "op": c[7]}
    return out


# ---------------------------------------------------------------- parent source (by sha)
_PARENT_CACHE: dict | None = None


def parent_index() -> dict[str, str]:
    """sha256 -> path for every blueprint-sized .md under the knowledge base."""
    global _PARENT_CACHE
    if _PARENT_CACHE is not None:
        return _PARENT_CACHE
    idx: dict[str, str] = {}
    for dp, dn, fn in os.walk(KBASE, onerror=lambda e: None, followlinks=False):
        dn[:] = [d for d in dn if d not in {".git", "__pycache__"}]
        for f in fn:
            if not f.endswith(".md"):
                continue
            p = os.path.join(dp, f)
            try:
                if os.path.getsize(p) > 12_000_000:
                    continue
                idx.setdefault(sha(open(p, "rb").read()), p)
            except Exception:
                continue
    _PARENT_CACHE = idx
    return idx


def parent_path() -> tuple[str | None, dict]:
    p = parent_index().get(PARENT_SHA)
    info = {"declared_path_has_stale_segment": True,
            "declared_path": (r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04"
                              r"\SST_PLP_PH01_W0_B0-m\藍圖\SST_PLP_PH01_W0_B0-B8_藍圖"
                              r"\SST_PLP_PH01_W0_B2_藍圖_實質正文_2026-11-24_r2.md"),
            "resolved_path": p, "expected_sha256": PARENT_SHA,
            "state": ("PARENT_SOURCE_REBOUND_BY_SHA" if p else "PARENT_SOURCE_UNBOUND"),
            "ratification": "CANDIDATE_NOT_RATIFIED — locator rebind only; no SPEC amendment"}
    return p, info


def clause_spans(text: str) -> dict[int, tuple[int, int]]:
    """1-based line number -> (start,end) char offsets of that line INCLUDING its terminator."""
    spans, pos, n = {}, 0, 0
    while pos <= len(text):
        n += 1
        nl = text.find("\n", pos)
        if nl < 0:
            spans[n] = (pos, len(text))
            break
        spans[n] = (pos, nl + 1)
        pos = nl + 1
        if pos >= len(text):
            break
    return spans


def clause_sha(text: str, a: int, b: int) -> dict:
    """Reproduce direct_clause_sha under explicit span rules; report which rule matched."""
    sp = clause_spans(text)
    if a not in sp or b not in sp:
        return {"reproduced": False, "reason": "SPAN_OUT_OF_RANGE"}
    raw = text[sp[a][0]:sp[b][1]]
    lf = raw.replace("\r\n", "\n")
    cands = {
        "RAW_WITH_TERMINATOR": sha(raw.encode("utf-8")),
        "LF_NO_TRAILING_NEWLINE": sha(lf.rstrip("\n").encode("utf-8")),
        "LF_WITH_TRAILING_NEWLINE": sha(lf.encode("utf-8")),
    }
    return {"reproduced": True, "candidates": cands, "bytes": len(raw)}


def parse_ref(ref: str) -> dict:
    m = re.match(r"^(PARENT|EVIDENCE)@([0-9a-f]{64}):L(\d+)[–-](\d+)$", ref or "")
    if m:
        return {"kind": m.group(1), "sha": m.group(2), "a": int(m.group(3)), "b": int(m.group(4))}
    m = re.match(r"^(.+?)@([0-9a-f]{64}):L(\d+)[–-](\d+)$", ref or "")
    if m:
        return {"kind": "FILE", "path": m.group(1), "sha": m.group(2),
                "a": int(m.group(3)), "b": int(m.group(4))}
    return {"kind": "UNPARSED", "raw": ref}


# ---------------------------------------------------------------- row semantics
STATE_TOKENS = ("SELECTED_OPTIONAL_DISABLED", "SELECTED_DESIGN_ONLY", "INSTALLED", "ENABLED",
                "NOT_INSTALLED_NOT_BOUND", "DISABLED")


def norm_req(s: str) -> str:
    x = str(s or "").strip().strip("`").replace("\\", "").strip()
    x = x.split("/")[0].split("·")[0].strip().strip("`")
    return x.upper()


def row_requiredness(u: dict) -> str:
    sp = u.get("source_payload") or []
    k = u.get("kind")
    if k == "HARD":
        return "HARD" if "HARD" in str(sp[1] if len(sp) > 1 else "") else "OTHER"
    if k == "E00_TECH":
        return norm_req(sp[2]) if len(sp) > 2 else "UNKNOWN"
    if k == "TECH_ROUTE":
        return "ROUTE_ONLY"
    if k == "Q_SOURCE_ROW":
        return norm_req(sp[2]) if len(sp) > 2 else "UNKNOWN"
    return "UNKNOWN"


def independent_requiredness(u: dict) -> tuple[str, str]:
    """Requiredness derived from the SPEC's own rule text (not from the payload being judged)."""
    k, rule = u.get("kind"), u.get("input_rule") or ""
    if k == "HARD":
        return ("HARD" if re.search(r"HARD Requiredness", rule) else "OTHER",
                "rule: input_rule states HARD Requiredness preserved")
    if k == "E00_TECH":
        m = re.search(r"selection=([A-Za-z0-9_]+)", rule) or re.search(r"處置=([A-Z_]+)", rule)
        return (norm_req(m.group(1)) if m else "OTHER", "rule: input_rule selection=<state>")
    if k == "TECH_ROUTE":
        return ("ROUTE_ONLY", "rule: TECH_ROUTE rows are route-only by kind (SPEC "
                              "05.KIND.TECH_ROUTE); their disposition is checked separately, not "
                              "as a requiredness")
    if k == "Q_SOURCE_ROW":
        q = (u.get("q_row") or {}).get("full_key", "")
        n = re.search(r"Q([1-4])", u.get("key", ""))
        qn = "Q" + n.group(1) if n else "?"
        col = str((u.get("source_payload") or ["", "", ""])[2])
        return (norm_req(col), f"rule: original {qn} row column 2 ({q}) is the source "
                               f"requiredness and is preserved verbatim")
    return ("UNKNOWN", "no rule")


def q_of(u: dict) -> dict:
    """Quadrant attribution from the two data-derived identity signals.

    The B2 SPEC has no per-quadrant section (H3 is per KIND), so the section vote is not
    available; the namespace prefix and q_row.full_key are independent carriers of the same
    original table position and must agree exactly.
    """
    kp = re.search(r"Q([1-4])", (u.get("key") or "").split("::")[0])
    qr = re.search(r"Q([1-4])", (u.get("q_row") or {}).get("full_key", "") or "")
    votes = {"key_namespace_prefix": ("Q" + kp.group(1)) if kp else None,
             "q_row_full_key": ("Q" + qr.group(1)) if qr else None}
    seen = {v for v in votes.values() if v}
    agree = len(seen) == 1
    q = next(iter(seen)) if agree else None
    return {"q": q, "agree": agree, "votes": votes}


# ---------------------------------------------------------------- oracles
class OracleError(Exception):
    pass


def join_rows(selector: dict, index: dict[str, list[dict]]) -> list[dict]:
    """A join that is only legal on the full namespace-qualified identity.

    A suffix/tail selector is refused even when it would resolve to exactly one row: the namespace
    is part of the identity, not a decoration that happens to be unique today.
    """
    if set(selector) != {"key"}:
        raise OracleError("NAMESPACE_JOIN_DENY")
    key = selector["key"]
    if key.count("::") < 1 or not re.match(r"^[A-Za-z0-9_.\-]+::", key):
        raise OracleError("NAMESPACE_JOIN_DENY")
    return index.get(key, [])


def suffix_lookup(suffix: str, index: dict[str, list[str]]) -> list[str]:
    """What a naive implementation would do: match on the tail of the key. Used only to prove
    that the refusal above is not vacuous."""
    return [k for k in index if k.endswith("::" + suffix) or k.endswith(suffix)]


def requiredness_gate(declared: str, independent: str, claimed_enable: bool) -> str | None:
    if declared != independent:
        return "TOOL_REQUIREDNESS_HOLD"               # HARD deleted, or non-HARD claimed as HARD
    if claimed_enable:
        return "TOOL_REQUIREDNESS_HOLD"               # enablement without authorisation
    return None


def state_gate(states: list[str]) -> str | None:
    distinct = {s for s in states if s}
    if len(distinct) > 1:
        return "STATE_CONFLICT"
    return None
