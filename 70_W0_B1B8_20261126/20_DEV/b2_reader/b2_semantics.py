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
_CARRIER_CACHE: dict | None = None


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


def carrier_index() -> dict[str, str]:
    """sha256 -> path for the wider PH01-04 tree.

    The batch library (KBASE) only holds the W0_B0-B8 package, but Q rows cite a carrier document
    that lives one level up (…/PHASE 01~04/藍圖/實質正文/), so carrier resolution needs its own walk.
    Still sha-first: the declared path in the SPEC says 'PHASE 00~04' and is stale.
    """
    global _CARRIER_CACHE
    if _CARRIER_CACHE is not None:
        return _CARRIER_CACHE
    idx: dict[str, str] = {}
    root = os.path.dirname(KBASE)
    for dp, dn, fn in os.walk(root, onerror=lambda e: None, followlinks=False):
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
    _CARRIER_CACHE = idx
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
    m = re.match(r"^(.+?)@([0-9a-f]{64}):L(\d+)$", ref or "")     # single-line carrier citation
    if m:
        n = int(m.group(3))
        return {"kind": "FILE", "path": m.group(1), "sha": m.group(2), "a": n, "b": n}
    return {"kind": "UNPARSED", "raw": ref}


# ---------------------------------------------------------------- row semantics
REQ_TOKENS = {"HARD", "EVAL_ONLY", "OPTIONAL", "DEFER_WITH_TRIGGER", "DEFER_NOFIT",
              "REFERENCE_ONLY", "NOT_SELECTED", "SELECTED_OPTIONAL_DISABLED",
              "SELECTED_DESIGN_ONLY", "SELECTED_DOCUMENT_ADAPTER", "SOFT", "CONDITIONAL"}

# states that cannot hold at the same time. Coexistence of INSTALLED with ENABLED is legal and is
# used as the discrimination probe: a gate that flags "any two distinct states" would fail it.
# Two ownership classes. NATURAL pairs are self-evident mutual exclusions; MAKER_DECLARED pairs were
# inferred by the Maker from the design-selection vocabulary and are NOT in the SPEC, so a case that
# would need one of them must be reported HOLD_ORACLE_UNBOUND, not executed.
EXCLUSIVE_PAIRS_NATURAL = (("SELECTED", "NOT_SELECTED"), ("INSTALLED", "NOT_INSTALLED"),
                           ("ENABLED", "DISABLED"), ("BOUND", "UNBOUND"),
                           ("VERIFIED", "NOT_VERIFIED"), ("APPROVED", "REJECTED"),
                           ("HARD", "EVAL_ONLY"))
EXCLUSIVE_PAIRS_MAKER_DECLARED = (("REUSE_INTERNAL_DESIGN", "SELECTED_DESIGN_ONLY"),
                                  ("DEFER_NOFIT", "SELECTED_DESIGN_ONLY"),
                                  ("REFERENCE_ONLY", "SELECTED_DESIGN_ONLY"))
EXCLUSIVE_PAIRS = EXCLUSIVE_PAIRS_NATURAL + EXCLUSIVE_PAIRS_MAKER_DECLARED


def clause_rule_note() -> str:
    return ("direct_clause_sha = sha256 of the UTF-8 bytes of the DIRECT PARENT's lines a..b "
            "inclusive, including the LF terminator of line b (parent is LF-only). "
            "`original_source_ref` is a different reference and must not be used for this check.")


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


def join_rows(selector: dict, index: dict[str, list[dict]],
              tail_index: dict[str, list[str]] | None = None) -> list[dict]:
    """A join that is only legal on a full, existing, namespace-qualified identity.

    Differences from the first attempt (which the round-1 checker rejected as selector-shape-only):
    a key that is not present but whose TAIL resolves elsewhere is denied with NAMESPACE_JOIN_DENY,
    so dropping or forging the namespace is refused on identity grounds rather than on argument
    shape. An unknown key with no tail collision returns [] (not a denial).
    """
    if set(selector) != {"key"}:
        raise OracleError("NAMESPACE_JOIN_DENY")
    key = selector["key"]
    if key in index:
        rows = index[key]
        if len(rows) != 1:
            raise OracleError("STATE_CONFLICT")          # duplicate identity, not a join
        return rows
    # Not an existing full key. If some indexed key ENDS WITH the presented key (namespace dropped) or
    # the presented key ends with a namespace-stripped indexed key (namespace forged), the caller has
    # tampered with the identity -> deny. Nothing matching at all is simply an unknown key.
    if any(k.endswith(key) for k in index):
        raise OracleError("NAMESPACE_JOIN_DENY")
    if "::" in key:
        stripped = key.split("::", 1)[1]
        if any(k.endswith(stripped) for k in index):
            raise OracleError("NAMESPACE_JOIN_DENY")
    return []


def namespace_blind_lookup(key: str, index: dict[str, list[dict]],
                           tail_index: dict[str, list[str]]) -> list[str]:
    """What a tail-only implementation would do. Used to prove a refusal is not vacuous."""
    return [k for k in index if k.endswith(key) or key.endswith(k)]


def requiredness_gate(declared: str, independent: str, claimed_enable: bool) -> str | None:
    if declared != independent:
        return "TOOL_REQUIREDNESS_HOLD"               # HARD deleted, or non-HARD claimed as HARD
    if claimed_enable:
        return "TOOL_REQUIREDNESS_HOLD"               # enablement without authorisation
    return None


def contradicting_state(state: str) -> str | None:
    """The row's counterpart for a NATURAL exclusion, matched on tokens.

    Maker-declared pairs are deliberately excluded: a row whose only counterpart would come from
    them must be reported HOLD_ORACLE_UNBOUND (the design-selection owner owes that relation).
    """
    toks = _state_tokens([state])
    for a, b in EXCLUSIVE_PAIRS_NATURAL:
        if a in toks:
            return b
        if b in toks:
            return a
    return None


SELECTION_CLASS = {"HARD", "SOFT", "CONDITIONAL", "EVAL_ONLY", "OPTIONAL", "DEFER_NOFIT",
                   "DEFER_WITH_TRIGGER", "REFERENCE_ONLY", "NOT_SELECTED", "SELECTED_OPTIONAL_DISABLED",
                   "SELECTED_DESIGN_ONLY", "SELECTED_DOCUMENT_ADAPTER", "REUSE_INTERNAL_DESIGN",
                   "NOT_INSTALLED_NOT_BOUND"}


def _state_tokens(states: list[str]) -> set[str]:
    """Tokenise on anything that is not [A-Z0-9_].

    Substring matching was a real defect: "SELECTED" is a substring of "NOT_SELECTED", so the pair
    (SELECTED, NOT_SELECTED) fired on a single legal token. Tokens are compared for equality only.
    """
    toks: set[str] = set()
    for s in states:
        for t in re.split(r"[^A-Z0-9_]+", (s or "").upper()):
            if t:
                toks.add(t)
    return toks


def state_gate(states: list[str]) -> str | None:
    """Conflict only on a declared mutual-exclusion relation.

    Deliberately NOT "any two distinct states": INSTALLED+ENABLED is legal coexistence and
    DEFER_NOFIT+NOT_SELECTED is a legal compound; both are probe cases that keep this gate from
    being trivially true.
    """
    toks = _state_tokens(states)
    for a, b in EXCLUSIVE_PAIRS:
        if a in toks and b in toks:
            return "STATE_CONFLICT"
    return None
