#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 native engine — r5 CODEX_FINAL product layer (SOURCE_READ only).

Ops: QROWS / HARD / META / RETURN.
Bound to the same spec manifest as B1 and to the owner-authorised tool carrier
raw SHA 463dcf33a668a9daa8f0bbf447c7dacc4c3d602bc53fa7e4866844ffbbc4b3e1.

What is really verified here:
  * the carrying row of every Q unit resolves to one physical line of the carrier,
    whose key column and row column equal the unit's key/OriginalRow, and whose
    JSON payload is byte-identical under the canonical compact encoding;
  * namespace join is exact (a look-alike tail in a different namespace is refused);
  * HARD/E00/ROUTE requiredness cannot be downgraded by this product.
What is NOT verified here and stays HOLD: wheel version/license/ABI/lock from
official metadata (no metadata right/network in this run), tool runtime semantics,
and the nine non-loss HARD inner->outer mappings.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b1_spec

CARRIER = (r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\PHASE 01~04"
           r"\藍圖\實質正文\SST_PLP_共用實質正文_工具合約_2026-11-23_r2.md")
CARRIER_SHA = "463dcf33a668a9daa8f0bbf447c7dacc4c3d602bc53fa7e4866844ffbbc4b3e1"
CARRIER_BYTES = 767859
CONSUMERS = {"B3": ["tool_key", "source_row", "requiredness"],
             "B5": ["tool_key", "source_row", "metadata", "missing"]}


def compact_sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


class Carrier:
    def __init__(self):
        raw = open(CARRIER, "rb").read()
        self.sha = hashlib.sha256(raw).hexdigest()
        self.bytes = len(raw)
        if self.sha != CARRIER_SHA or self.bytes != CARRIER_BYTES:
            raise RuntimeError(f"CARRIER_IDENTITY_MISMATCH {self.sha} {self.bytes}")
        self.lines = raw.decode("utf-8").splitlines()
        self.by_line = {}
        self.by_key = {}
        for i, line in enumerate(self.lines, 1):
            if not line.startswith("|"):
                continue
            body = line[1:].rstrip()
            if body.endswith("|"):
                body = body[:-1]
            parts = [x.strip() for x in body.split(" | ")]
            if len(parts) < 3 or not parts[0].startswith("R3-REGISTRY-Q"):
                continue
            key = parts[0]
            rec = {"line": i, "key": key, "original_row": parts[1].strip(), "raw": line}
            try:
                rec["payload"] = json.loads(parts[2])
                rec["payload_ok"] = True
            except Exception as ex:
                rec["payload"] = None
                rec["payload_ok"] = False
                rec["payload_error"] = str(ex)
            self.by_line[i] = rec
            self.by_key[key] = rec


# ---- carrier-declared dimensions (authority = the carrier's own section headers) ----
BASE_REQ_ATOMS = ("HARD", "SOFT", "CONDITIONAL", "OPTIONAL", "EVAL_ONLY", "REFERENCE")
REQ_VOCAB = ("HARD", "SOFT", "SOFT/CONDITIONAL", "CONDITIONAL", "OPTIONAL", "EVAL_ONLY")

NOT_REQUIREDNESS_MARKERS = ("ROUTE_ONLY_NOT_TOOL_REQUIREDNESS", "N_A", "NA", "N/A", "-", "NONE")


def is_requiredness_value(val: str) -> bool:
    """A requiredness cell is either a base atom, a compound of atoms (a/b), or an
    atom with an author qualifier (EVAL_ONLY_COMPARATOR, EVAL_ONLY_RESEARCH ...).
    The verbatim string is kept; only its shape is validated against the atom set."""
    if not val:
        return False
    if val in NOT_REQUIREDNESS_MARKERS:
        return False
    for a in BASE_REQ_ATOMS:
        if val == a or val.startswith(a + "/") or val.startswith(a + "_") or val.startswith(a + " "):
            return True
    return False
DIMENSION_BY_NS = {
    "R3-REGISTRY-Q1": {"dimension": "Requiredness", "requiredness_index": 2},
    "R3-REGISTRY-Q2": {"dimension": "AdmissionDecision", "requiredness_index": 5,
                       "admission_decision_index": 2},
    "R3-REGISTRY-Q3": {"dimension": "KindApplicability", "requiredness_index": None},
    "R3-REGISTRY-Q4": {"dimension": "Golden", "requiredness_index": None},
}


def norm_cell(v) -> str:
    if not isinstance(v, str):
        return ""
    return v.strip().strip("`").replace("\\`", "").strip().strip("`").strip()


def carrier_sections() -> dict:
    """namespace -> (header_line, row_count_declared) parsed from the carrier itself."""
    out = {}
    c = carrier()
    for i, line in enumerate(c.lines, 1):
        m = re.match(r"^## (R3-REGISTRY-Q[1-4])｜(\d+)列", line)
        if m:
            out[m.group(1)] = {"header_line": i, "declared_rows": int(m.group(2)),
                               "evidence": f"carrier:{i}"}
    return out


def requiredness_for(namespace: str, payload: list) -> tuple[str, str, str]:
    """Return (value, basis, dimension) using the carrier-declared column map.

    Q1 carries Requiredness at index 2; Q2 carries Requiredness at index 5 while index 2
    is its own AdmissionDecision dimension; Q3/Q4 declare different dimensions and carry
    no Requiredness field at all. Anything outside the closed vocabulary is UNKNOWN.
    """
    spec = DIMENSION_BY_NS.get(namespace, {})
    dim = spec.get("dimension", "UNKNOWN")
    idx = spec.get("requiredness_index")
    if idx is None:
        sec = carrier_sections().get(namespace, {})
        return ("NOT_APPLICABLE",
                f"carrier:{sec.get('header_line','?')} dimension={dim} declares no Requiredness column",
                dim)
    if not isinstance(payload, list) or len(payload) <= idx:
        return "UNKNOWN", f"row shorter than declared requiredness index {idx}", dim
    val = norm_cell(payload[idx])
    if val in REQ_VOCAB:
        return val, f"carrier index {idx} of the {dim} registry", dim
    if is_requiredness_value(val):
        return val, f"carrier index {idx} of the {dim} registry (compound value)", dim
    if val in NOT_REQUIREDNESS_MARKERS:
        return ("NOT_APPLICABLE",
                f"carrier index {idx} holds the source's own not-applicable marker {val!r}", dim)
    return ("UNKNOWN",
            f"carrier index {idx} holds {val!r}, which is not in the closed requiredness vocabulary",
            dim)


_C = None


def carrier() -> Carrier:
    global _C
    if _C is None:
        _C = Carrier()
    return _C


def _unit_row_spec(unit: dict) -> dict:
    rule = unit.get("input_rule", "")
    m_key = re.search(r"key=([^\s；]+)", rule)
    m_row = re.search(r"OriginalRow=(\d+)", rule)
    m_car = re.search(r"carrier=L(\d+)", rule)
    return {"key_ns": m_key.group(1) if m_key else None,
            "original_row": int(m_row.group(1)) if m_row else None,
            "carrier_line": int(m_car.group(1)) if m_car else None}


def tech54_index() -> dict:
    """tool_key -> {SelectedDesign, SelectedVersion, line} from the carrier's TECH54 section.

    This is the independent original record for the E00 design selections; the spec's own
    payload is never used as its own oracle.
    """
    c = carrier()
    out, started, current = {}, False, None
    for i, line in enumerate(c.lines, 1):
        if line.startswith("## TECH54具名設計合約"):
            started = True
            continue
        if not started:
            continue
        m = re.match(r"^### (TOOL_R2_TECH54::TECH-\d+)", line)
        if m:
            current = m.group(1)
            out[current] = {"line": i}
            continue
        if current:
            m2 = re.match(r"^- (SelectedDesign|SelectedVersion|InternalShortName)：(.+)$", line)
            if m2:
                out[current][m2.group(1)] = m2.group(2).strip()
    return out


def resolve_tool_row(key: str) -> dict:
    """A tool key may live in more than one registry namespace; resolve without guessing."""
    c = carrier()
    hits = []
    for ns in ("R3-REGISTRY-Q1", "R3-REGISTRY-Q2"):
        qualified = key if key.startswith(ns + "::") else f"{ns}::{key}"
        rec = c.by_key.get(qualified)
        if rec:
            val, basis, dim = requiredness_for(ns, rec["payload"])
            hits.append({"namespace": ns, "record": rec, "requiredness": val,
                         "basis": basis, "dimension": dim})
    if len(hits) == 1:
        return {"status": "RESOLVED", "hit": hits[0]}
    if len(hits) > 1:
        vals = {h["requiredness"] for h in hits}
        return {"status": "AMBIGUOUS" if len(vals) > 1 else "RESOLVED_AGREE",
                "hits": hits, "agreed_value": vals.pop() if len(vals) == 1 else None}
    return {"status": "ABSENT"}


def op_qrows(units: list[dict]) -> dict:
    c = carrier()
    entries, errors = [], []
    ns_counter = {}
    for u in units:
        spec = _unit_row_spec(u)
        key_full = u["key"]
        ns = key_full.split("::")[0]
        row_id = key_full.rsplit("::ROW=", 1)[-1]
        ns_counter[ns] = ns_counter.get(ns, 0) + 1
        ent = {"unit_id": u["unit_id"], "key": key_full, "namespace": ns,
               "original_row_expected": row_id, "carrier_line_expected": spec["carrier_line"],
               "payload_sha_expected": u.get("payload_sha"), "decision": None}
        line = spec["carrier_line"]
        rec = c.by_line.get(line) if line else None
        if not rec:
            ent["decision"] = "MISSING"
            ent["first_fail"] = "TOOL_REQUIREDNESS_HOLD"
            ent["missing"] = [{"field": "carrier_line", "reason": "ABSENT",
                               "detail": f"no registry row at carrier line {line}"}]
            errors.append({"unit_id": u["unit_id"], "code": "Q_ROW_MISSING",
                           "first_fail": "TOOL_REQUIREDNESS_HOLD"})
            entries.append(ent)
            continue
        ent.update({"carrier_line_observed": rec["line"], "carrier_key": rec["key"],
                    "carrier_row": rec["original_row"]})
        if rec["key"] != spec["key_ns"]:
            ent["decision"] = "NAMESPACE_JOIN_DENY"
            ent["first_fail"] = "NAMESPACE_JOIN_DENY"
        elif rec["original_row"] != row_id:
            ent["decision"] = "ROW_MISMATCH"
            ent["first_fail"] = "NAMESPACE_JOIN_DENY"
        elif not rec["payload_ok"]:
            ent["decision"] = "PAYLOAD_UNPARSEABLE"
            ent["first_fail"] = "PAYLOAD_SHA_MISMATCH"
        else:
            val, basis, dim = requiredness_for(ns, rec["payload"])
            ent["requiredness"] = val
            ent["requiredness_basis"] = basis
            ent["dimension"] = dim
            idx = DIMENSION_BY_NS.get(ns, {}).get("admission_decision_index")
            if idx is not None and len(rec["payload"]) > idx:
                ent["admission_decision"] = norm_cell(rec["payload"][idx])
            obs = compact_sha(rec["payload"])
            ent["payload_sha_observed"] = obs
            if obs == u.get("payload_sha"):
                ent["decision"] = "VERIFIED"
            else:
                ent["decision"] = "PAYLOAD_SHA_MISMATCH"
                ent["first_fail"] = "PAYLOAD_SHA_MISMATCH"
        if ent["decision"] != "VERIFIED":
            errors.append({"unit_id": u["unit_id"], "code": ent["decision"],
                           "first_fail": ent.get("first_fail")})
        entries.append(ent)
    return {"entries": entries, "errors": errors,
            "carrier": {"path": CARRIER, "sha256": c.sha, "bytes": c.bytes,
                        "indexed_rows": len(c.by_key), "physical_lines": len(c.lines)},
            "namespaces": ns_counter,
            "summary": {"units": len(entries),
                        "verified": sum(1 for e in entries if e["decision"] == "VERIFIED"),
                        "not_verified": sum(1 for e in entries if e["decision"] != "VERIFIED")}}


def derive_requiredness(unit: dict) -> tuple[str, str]:
    """Requiredness is read from the carrier row the unit points at, never guessed."""
    key = unit["key"].split("::ROW=")[0]
    ns = key.split("::")[0]
    rec = carrier().by_key.get(key)
    if rec and rec.get("payload_ok"):
        val, basis, _dim = requiredness_for(ns, rec["payload"])
        return val, basis
    return "UNKNOWN", "carrier row absent for this key"


def op_hard(units: list[dict]) -> dict:
    entries = []
    for u in units:
        kind, key = u["kind"], u["key"]
        payload = u.get("source_payload") or []
        ent = {"unit_id": u["unit_id"], "key": key, "kind": kind,
               "payload_sha": u.get("payload_sha")}
        if kind in ("HARD", "TECH_ROUTE"):
            base_key = key.replace("::ROUTE", "")
            res = resolve_tool_row(base_key)
            rec = (res.get("hit") or (res.get("hits") or [{}])[0]).get("record")
            if res["status"] in ("RESOLVED", "RESOLVED_AGREE") and rec and rec.get("payload_ok"):
                ns = (res.get("hit") or res["hits"][0])["namespace"]
                car_req, basis, dim = requiredness_for(ns, rec["payload"])
                ent["resolved_namespace"] = ns
                ent["resolution_status"] = res["status"]
                ent.update({"carrier_requiredness": car_req, "requiredness_basis": basis,
                            "dimension": dim})
                if kind == "HARD":
                    # the unit states its requiredness in its own input_rule ("原Python / HARD
                    # Requiredness保留"); its payload array is not the carrier row, so the
                    # carrier index must not be applied to it
                    unit_req = "UNKNOWN"
                    for a in REQ_VOCAB + ("REFERENCE",):
                        if re.search(r"(^|[^A-Z_])" + re.escape(a.split("/")[0]) + r"([^A-Z_]|$)",
                                     u.get("input_rule", "")):
                            unit_req = a
                            break
                    if unit_req == "UNKNOWN":
                        for item in payload:
                            cand = norm_cell(item)
                            if is_requiredness_value(cand):
                                unit_req = cand
                                break
                    ent["unit_requiredness"] = unit_req
                    ent["requiredness_delta"] = {
                        "original": car_req, "observed": unit_req,
                        "missing": ([] if unit_req == car_req else
                                    [{"field": "requiredness", "reason": "AMBIGUOUS",
                                      "detail": f"unit says {unit_req}, carrier says {car_req}"}]),
                        "affected_scope": ns}
                    ent["decision"] = "PRESERVED" if unit_req == car_req else "DRIFT"
                else:
                    # route row: its own text must keep the same requiredness statement
                    text = " ".join(norm_cell(x) for x in payload)
                    stated_rt = route_stated_requiredness(text)
                    verbatim = bool(car_req) and car_req in stated_rt
                    ent["route_contains_carrier_value"] = verbatim
                    ent["route_stated_requiredness"] = stated_rt
                    # no vocabulary scanning: a route either restates the row value verbatim or
                    # it says nothing this product can contradict
                    g = guard_route_requiredness(car_req, text)
                    ent["decision"] = {"ALLOW": "PRESERVED", "DENY": "DRIFT",
                                       "HOLD": "NOT_ASSERTED"}[g["decision"]]
                    ent["requiredness_delta"] = {"original": car_req,
                                                 "observed": car_req if verbatim else None,
                                                 "missing": [] if verbatim else
                                                 [{"field": "route_requiredness_statement",
                                                   "reason": "AMBIGUOUS",
                                                   "detail": "route text does not restate the row "
                                                             "value verbatim; no contradiction is "
                                                             "asserted"}],
                                                 "affected_scope": base_key.split("::")[0]}
            else:
                ent["decision"] = "CARRIER_ROW_ABSENT"
                ent["resolution_status"] = res["status"]
                ent["requiredness_delta"] = None
        elif kind == "E00_TECH":
            idx = tech54_index()
            orig = idx.get(key)
            unit_sel = [norm_cell(x) for x in payload
                        if isinstance(x, str) and ("SELECTED" in x or "NOT_SELECTED" in x)]
            ent["unit_design_selection"] = unit_sel
            ent["requiredness_delta"] = None
            if not orig or "SelectedDesign" not in orig:
                ent["decision"] = "CARRIER_SELECTION_ABSENT"
                ent["missing"] = [{"field": "design_selection",
                                   "reason": "UNVERIFIED",
                                   "detail": "the carrier's TECH54 section has no SelectedDesign "
                                             "for this tool"}]
            else:
                ent["carrier_design_selection"] = orig["SelectedDesign"]
                ent["carrier_line"] = orig["line"]
                ent["carrier_version"] = orig.get("SelectedVersion")
                same = bool(unit_sel) and unit_sel[0] == orig["SelectedDesign"]
                ent["carrier_agrees"] = same
                # the pinned spec (B2-F05) declares these units' original typed
                # DesignSelection oracle as unbound except for two historical cases, so a
                # carrier cross-check cannot upgrade the case to PASS
                ent["decision"] = ("CARRIER_AGREES_SPEC_ORACLE_HOLD" if same
                                   else "CARRIER_DISAGREES_SPEC_ORACLE_HOLD")
        entries.append(ent)
    return {"entries": entries,
            "summary": {"units": len(entries),
                        "preserved": sum(1 for e in entries if e["decision"] == "PRESERVED"),
                        "drift": sum(1 for e in entries if e["decision"] == "DRIFT"),
                        "selection_present": sum(1 for e in entries
                                                 if e["decision"] == "SELECTION_PRESENT"),
                        "other": sum(1 for e in entries if e["decision"] not in
                                     ("PRESERVED", "DRIFT", "SELECTION_PRESENT"))}}


def guard_design_selection(original: str, proposed: str) -> dict:
    """A selected-optional-disabled tool may not be enabled by an unauthorised change."""
    if "DISABLED" in original and "DISABLED" not in proposed:
        return {"decision": "DENY", "first_fail": "STATE_CONFLICT",
                "detail": f"{original} -> {proposed} would enable a disabled selection, which is a "
                          f"state conflict against the pinned SelectedDesign"}
    if original != proposed:
        return {"decision": "DENY", "first_fail": "STATE_CONFLICT",
                "detail": f"{original} -> {proposed} changes the original design selection "
                          f"(state conflict)"}
    return {"decision": "ALLOW", "detail": "unchanged"}


def req_components(value: str) -> set:
    return {p.strip() for p in re.split(r"[/,;]", value or "") if p.strip()}


def route_stated_requiredness(route_text: str) -> list:
    """The route string is field-structured with the full-width separator; the requiredness
    field is the leading token of one of those fields. Read it structurally instead of
    scanning free text (which produced false contradictions)."""
    out = []
    for seg in re.split(r"[／/]", route_text):
        head = seg.split(";")[0].strip()
        if not head or " " in head:
            continue
        if is_requiredness_value(head):
            out.append(head)
    return sorted(set(out))


def guard_route_requiredness(carrier_req: str, route_text: str) -> dict:
    """Compare the route text to its tool row by *verbatim containment only*.

    Scanning for vocabulary tokens inside free text produced false contradictions
    (a route saying `EVAL_ONLY_COMPARATOR` would match `EVAL_ONLY`), so the only
    assertion this guard makes is: does the carrier's own value appear verbatim?
    If it does the route is consistent; if it does not, the route is not shown to
    contradict the row either, so the answer is HOLD, not a denial.
    """
    stated = route_stated_requiredness(route_text)
    comps = req_components(carrier_req)
    if carrier_req and carrier_req in stated:
        return {"decision": "ALLOW",
                "detail": f"the route states {carrier_req!r}, exactly its tool row value"}
    if stated and not (set(stated) & comps):
        return {"decision": "DENY", "first_fail": "ROUTE_REQUIREDNESS_DRIFT_DENY",
                "detail": f"the route states {stated} while the tool row carries {carrier_req!r}"}
    if stated:
        return {"decision": "ALLOW",
                "detail": f"the route states {stated}, a component of {carrier_req!r}"}
    return {"decision": "HOLD",
            "detail": "the route states no requiredness field, so nothing is asserted"}


def guard_requiredness(original: str, proposed: str) -> dict:
    """HARD may never be downgraded by the product; the guard is real and tested."""
    order = {"HARD": 3, "CONDITIONAL": 2, "OPTIONAL": 1, "EVAL_ONLY": 1}
    o, p = order.get(original, 0), order.get(proposed, 0)
    if p < o:
        return {"decision": "DENY", "first_fail": "TOOL_REQUIREDNESS_HOLD",
                "detail": f"{original} -> {proposed} would downgrade an original obligation"}
    return {"decision": "ALLOW", "detail": "no downgrade"}


def op_meta(units: list[dict]) -> dict:
    entries = []
    for u in units:
        entries.append({"unit_id": u["unit_id"], "key": u["key"],
                        "kind": u["kind"],
                        "wheel_metadata": {
                            "version": None, "license": None, "abi": None, "lock": None,
                            "first_probe": None},
                        "decision": "NOT_EXECUTED",
                        "missing": [{"field": "official_metadata",
                                     "reason": "UNVERIFIED",
                                     "detail": "no official package metadata read right / network "
                                               "access was exercised in this run; tool NAME is not a "
                                               "license and not an admission"},
                                    {"field": "license_declaration_vs_actual",
                                     "reason": "UNVERIFIED",
                                     "detail": "B2-F07: declaration/actual license, lock, ABI and "
                                               "first probe belong to the real B5 selection step"}],
                        "note": "metadata collection is a B5 selection input, not a B2 install right"})
    return {"entries": entries,
            "summary": {"units": len(entries), "collected": 0, "not_executed": len(entries)}}


def receiver(consumer_id: str, tool_readset: dict) -> dict:
    """Minimal B3/B5 receiver: validates its own mandatory fields, emits 13 columns."""
    mandatory = CONSUMERS[consumer_id]
    receipts, refused = [], []
    for ent in tool_readset["entries"]:
        missing = [m for m in mandatory if ent.get(m) in (None, "", [], {})]
        # a derived-but-unknown requiredness is not an acceptable value: it would let a
        # row through on a field whose original content was never established
        if ent.get("requiredness") == "UNKNOWN" and "requiredness" not in missing:
            missing.append("requiredness")
        if ent.get("requiredness") == "NOT_APPLICABLE" and not ent.get("applicability_evidence"):
            missing.append("requiredness_applicability_evidence")
        rec = {
            "consumer_id": consumer_id,
            "validator_name": f"native_{consumer_id.lower()}_receiver_r5",
            "validator_version": "2026-11-26_r5_CODEX_FINAL",
            "subject": "SST/SQS-THC/PH01/E00",
            "scope_id": (ent.get("tool_key") or ent.get("key", "")).split("::")[0],
            "spec_version": "2026-11-26_r5_Native-first_CODEX_FINAL",
            "candidate_digest": "3c816deb8fc216eae831dddfac396217d5b224fc7575c03415ef9f08ebbfa046",
            "source_id": ent.get("tool_key") or ent.get("key", ""),
            "sha": ent.get("payload_sha") or "",
            "rights_check_ref": "owner_allowlist+b1_locator_bindings (SOURCE_READ, no product write)",
            "decision": "REJECT" if missing else "ACCEPT_FOR_DRAFT",
            "first_fail": "MANDATORY_FIELD_MISSING" if missing else None,
            "checked_at": None,
            "checked_values": {"requiredness": ent.get("requiredness"),
                               "source_row": ent.get("source_row"),
                               "kind": ent.get("kind"),
                               "applicability_evidence": ent.get("applicability_evidence")},
        }
        (refused if missing else receipts).append(rec)
    return {"consumer_id": consumer_id, "mandatory_fields": mandatory,
            "receipts": receipts, "refused": refused,
            "accepted": len(receipts), "rejected": len(refused),
            "note": "ACCEPT_FOR_DRAFT is a receiver readiness state, never a product ACK"}
