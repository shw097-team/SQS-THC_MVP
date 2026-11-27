#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real consumer-side receiving of the B0 SourceReadSet/2 (B1/B2/B3 each, independently).

Each consumer pins its OWN ExpectedSet before it looks at the envelope: expected source id,
expected raw SHA, expected clause span, its own required fields, its own purpose/consumer id.
The envelope's `observed` never becomes the expectation.

Emits the original 13 columns per source, plus the 14 authority fields it actually checked.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

R = r"<LOCAL_ROOT>\71_W0_B0-B3_R7_20261127"
OPS = os.path.join(R, "40_OPS")
# The B0 SourceReadSet/2 is NOT re-read in this round: its trusted-context descriptor
# (00_PREFLIGHT/B0_READ_CONTEXT_2026-11-26.json) expired at 2026-11-27T01:08+08:00 and pins a
# previous window's authorization_sha; renewing it is a product-code delta only the Owner can
# authorise. The consumers therefore receive the historical envelope and record its currency,
# instead of a fabricated fresh one.
READSET = os.path.join(r"<LOCAL_ROOT>\70_W0_B1B8_20261126",
                       "40_OPS", "b0_r5_sourcereadset.json")
WINDOW = os.path.expanduser("~/.hgk-owner/window.json")
RECEIPT = (r"<LOCAL_ROOT>"
           r"\FHS_vNEXT_W0W1_CLOSEOUT_W2_ENTRY_20261115\owner_ws\artifacts\OWNER_WINDOW.json")

# Independent expectations, fixed per consumer BEFORE reading the envelope.
EXPECTED = {
    "B1": {"source_id": "SST.ALL.W0.BLUEPRINT",
           "sha": "dd37a40b112bf5aac379adb44285ec01409519f7af64418298375833859d01a1",
           "clause_span": [572, 579], "required_fields": ["read"],
           "purpose": "B0 SOURCE_READ under SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
           "consumer_use": "B1 REPO/BASE/FDA/ROOTS source read", "scope_id": "SQS-THC-PH01-E00-B0-SOURCE-READ"},
    "B2": {"source_id": "SST.ALL.W0.BLUEPRINT",
           "sha": "dd37a40b112bf5aac379adb44285ec01409519f7af64418298375833859d01a1",
           "clause_span": [572, 579], "required_fields": ["read"],
           "purpose": "B0 SOURCE_READ under SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
           "consumer_use": "B2 QROWS/HARD/META/RETURN source read", "scope_id": "SQS-THC-PH01-E00-B0-SOURCE-READ"},
    "B3": {"source_id": "SST.ALL.W0.BLUEPRINT",
           "sha": "dd37a40b112bf5aac379adb44285ec01409519f7af64418298375833859d01a1",
           "clause_span": [572, 579], "required_fields": ["read"],
           "purpose": "B0 SOURCE_READ under SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
           "consumer_use": "B3 JOIN/CHILD/ROUTE source read", "scope_id": "SQS-THC-PH01-E00-B0-SOURCE-READ"},
}
VALIDATORS = {"B1": ("native_b1_consumer_r5", "2026-11-27_r7"),
              "B2": ("native_b2_consumer_r5", "2026-11-27_r7"),
              "B3": ("native_b3_consumer_r5", "2026-11-27_r7")}


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def sha_file(p: str) -> str:
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def rights_ref() -> tuple[str, bool]:
    try:
        w = json.load(open(WINDOW, encoding="utf-8"))
        rs = sha_file(RECEIPT)
        ok = (w.get("state") == "OPEN" and int(w.get("expires_at", 0)) > int(time.time())
              and "b0_source_read_authority" in (w.get("scope") or [])
              and w.get("effect_class_ceiling") in ("READ_ONLY_PROBE", "REPOSITORY_WRITE",
                                                    "HOST_OPERATIONS", "USER_DATA_EFFECT"))
        return f"OWNER_WINDOW:{w.get('window_id')}:receipt_sha256={rs}", ok
    except Exception:
        return "OWNER_WINDOW_UNBOUND", False


def clause_slice(path: str, span: list[int]) -> bytes:
    raw = open(path, "rb").read()
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
    a, b = span
    if a < 1 or b < a or b > len(lines):
        raise ValueError("SPAN_OUT_OF_RANGE")
    return raw[lines[a - 1][0]:lines[b - 1][1]]


def receive(consumer: str, env: dict, env_bytes: bytes) -> dict:
    exp = EXPECTED[consumer]
    vname, vver = VALIDATORS[consumer]
    rec = {"consumer_id": consumer, "validator_name": vname, "validator_version": vver,
           "subject": env.get("subject"), "scope_id": env.get("scope", {}).get("scope_id"),
           "spec_version": env.get("spec_version"),
           # the producer's own freeze digest; the envelope hash is recorded separately
           "candidate_digest": env.get("candidate_digest"),
           "source_id": exp["source_id"], "sha": None, "rights_check_ref": None,
           "decision": None, "first_fail": None, "checked_at": now(),
           "expected_set": {k: exp[k] for k in ("source_id", "sha", "clause_span", "required_fields", "purpose", "consumer_use")},
           "envelope_sha256": hashlib.sha256(env_bytes).hexdigest(),
           "producer_spec_version": env.get("spec_version"),
           "source_manifest": env.get("source_manifest")}

    def fail(code: str) -> dict:
        rec["decision"], rec["first_fail"] = "REJECT", code
        return rec

    # 1 strict wire / identity
    if env.get("wire_version") != "SST.B0.SourceReadSet/2":
        return fail("WIRE_VERSION_INVALID")
    if env.get("spec_version") != "2026-11-25_r4_Native-first":
        return fail("SPEC_VERSION_INVALID")
    if env.get("subject") != "SST/SQS-THC/PH01/E00":
        return fail("SUBJECT_INVALID")
    if env.get("errors"):
        return fail("ENVELOPE_CARRIES_ERRORS")
    if env.get("write_set") != [] or env.get("fin_order") != "DENY":
        return fail("EFFECT_CLAIM_INVALID")
    if not env.get("candidate_digest"):
        return fail("PRODUCER_FREEZE_UNBOUND")

    # 2 own scope / purpose / consumer membership
    sc = env.get("scope") or {}
    if sc.get("scope_id") != exp["scope_id"]:
        return fail("SCOPE_MISMATCH")
    if consumer not in (sc.get("consumer_ids") or []):
        return fail("CONSUMER_NOT_IN_SCOPE")
    if sc.get("purpose") != exp["purpose"]:
        return fail("PURPOSE_MISMATCH")

    # 3 rights actually in force
    rref, rok = rights_ref()
    rec["rights_check_ref"] = rref
    if not rok:
        return fail("RIGHTS_UNVERIFIED")

    # 4 the entry itself, checked against the INDEPENDENT expectation
    ent = next((e for e in env.get("entries") or []
                if e.get("source_ref", {}).get("source_id") == exp["source_id"]), None)
    if ent is None:
        return fail("EXPECTED_SOURCE_ABSENT")
    rec["sha"] = ent.get("sha")
    if ent.get("sha") != exp["sha"]:
        return fail("RAW_SHA_MISMATCH")
    if ent.get("clause_span") != exp["clause_span"]:
        return fail("SPAN_MISMATCH")
    loc = ent.get("source_ref", {}).get("locator")
    if not loc or not os.path.isfile(loc):
        return fail("LOCATOR_UNRESOLVED")
    if sha_file(loc) != exp["sha"]:
        return fail("SOURCE_CHANGED_SINCE_READ")
    if hashlib.sha256(clause_slice(loc, exp["clause_span"])).hexdigest() != ent.get("clause_sha"):
        return fail("CLAUSE_SHA_MISMATCH")
    if sorted(ent.get("required_fields") or []) != sorted(exp["required_fields"]):
        return fail("REQUIRED_SET_MISMATCH")
    observed = ent.get("observed") or {}
    if sorted(observed) != sorted(exp["required_fields"]):
        return fail("R_P_M_INCONSISTENT")
    if ent.get("missing") not in ([], None) and ent.get("missing"):
        return fail("MANDATORY_FIELD_MISSING")
    slice_text = clause_slice(loc, exp["clause_span"]).decode("utf-8", "strict")
    for f, o in observed.items():
        if o.get("value") not in slice_text:
            return fail("VALUE_NOT_IN_SLICE")
        if hashlib.sha256(o["value"].encode("utf-8")).hexdigest() != o.get("value_sha"):
            return fail("VALUE_SHA_MISMATCH")

    # 5 authority object completeness (14 fields) — checked, not trusted
    auth = ent.get("authority") or {}
    need = ("source_owner", "usage_evidence_ref", "usage_evidence_sha", "os_principal",
            "verification_method", "rights_check_ref", "checked_at", "valid_from", "expires_at",
            "revocation_check_ref", "epoch_strategy", "epoch_provider_ref", "epoch_evidence_ref",
            "disclosure")
    absent = [k for k in need if k not in auth]
    if absent:
        return fail("AUTHORITY_FIELD_ABSENT:" + ",".join(absent))
    rec["authority_checked"] = {k: auth[k] for k in need}
    # The envelope's own authority block carries its own interval. A live window in front of
    # an expired envelope does not make the envelope current; this is the fail-closed check.
    def _ts(s):
        try:
            return time.mktime(time.strptime(str(s)[:19], "%Y-%m-%dT%H:%M:%S"))
        except Exception:
            return None
    exp_ts, now_ts = _ts(auth.get("expires_at")), time.time()
    rec["envelope_authority_interval"] = {"valid_from": auth.get("valid_from"),
                                          "expires_at": auth.get("expires_at"),
                                          "checked_at_run_clock": now()}
    if exp_ts is not None and exp_ts <= now_ts:
        rec["envelope_authority_expired_at_receive"] = True
        return fail("ENVELOPE_AUTHORITY_EXPIRED")
    # currency, derived from the envelope's own authority block against the live window
    live = json.load(open(WINDOW, encoding="utf-8")).get("window_id") if os.path.isfile(WINDOW) else None
    env_ref = str(auth.get("rights_check_ref") or "")
    env_wid = env_ref.split(":")[1] if env_ref.startswith("OWNER_WINDOW:") else None
    rec["envelope_window_id"] = env_wid
    rec["live_window_id"] = live
    rec["rights_currency"] = ("CURRENT" if env_wid and env_wid == live
                              else "ENVELOPE_MINTED_UNDER_A_DIFFERENT_WINDOW")
    rec["readset_origin"] = {"path": READSET, "sha256": sha_file(READSET),
                             "note": "historical B0 read; not re-executed this round"}
    rec["decision"] = "ACCEPT"
    return rec



def selftest() -> int:
    """Prove the consumers are not rubber stamps: every mutation must be rejected."""
    import copy
    raw = open(READSET, "rb").read()
    env0 = json.loads(raw)
    arms = []

    def run(mut, name, mutator, consumer="B1"):
        e = copy.deepcopy(env0)
        mutator(e)
        r = receive(consumer, e, json.dumps(e, ensure_ascii=False).encode("utf-8"))
        arms.append({"arm": name, "consumer": consumer, "decision": r["decision"],
                     "first_fail": r["first_fail"], "pass": r["decision"] == "REJECT"})

    run(None, "BASELINE_POS", lambda e: None)
    arms[-1]["pass"] = arms[-1]["decision"] == "ACCEPT"
    if not arms[-1]["pass"]:
        # A negative arm whose positive baseline already fails cannot tell its mutation apart
        # from the baseline it was applied to. Report the inadmissible baseline, not 10/11.
        out = {"schema": "SST.PH01.W0.B0B3.ConsumerSelfTest@1",
               "verdict": "HOLD_BASELINE_NOT_VALID",
               "baseline_decision": arms[-1]["decision"],
               "baseline_first_fail": arms[-1]["first_fail"],
               "passed": 0, "total": 11, "arms": arms,
               "note": ("the envelope's own authority interval has expired, so every arm "
                        "rejects for the same reason the baseline does; the mutations are "
                        "not distinguished in this round")}
        json.dump(out, open(os.path.join(OPS, "r7_consumer_selftest.json"), "w",
                            encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
        print(json.dumps({"verdict": out["verdict"], "baseline": arms[-1]["first_fail"],
                          "written": os.path.join(OPS, "r7_consumer_selftest.json")},
                         ensure_ascii=False, indent=1))
        return 0
    run(None, "WIRE_VERSION", lambda e: e.__setitem__("wire_version", "SST.B0.SourceReadSet/1"))
    run(None, "RAW_SHA", lambda e: e["entries"][0].__setitem__("sha", "0" * 64))
    run(None, "SPAN", lambda e: e["entries"][0].__setitem__("clause_span", [571, 579]))
    run(None, "CLAUSE_SHA", lambda e: e["entries"][0].__setitem__("clause_sha", "f" * 64))
    run(None, "VALUE_TAMPER", lambda e: e["entries"][0]["observed"]["read"].__setitem__("value", "tampered"))
    run(None, "AUTHORITY_FIELD", lambda e: e["entries"][0]["authority"].pop("disclosure"))
    run(None, "EFFECT_CLAIM", lambda e: e.__setitem__("fin_order", "ALLOW"))
    run(None, "SCOPE_PURPOSE", lambda e: e["scope"].__setitem__("purpose", "some other use"))
    run(None, "CONSUMER_MEMBERSHIP", lambda e: e["scope"].__setitem__("consumer_ids", ["B4"]))
    run(None, "REQUIRED_SET", lambda e: e["entries"][0].__setitem__("required_fields", ["read", "write"]))

    ok = sum(1 for a in arms if a["pass"])
    out = {"schema": "SST.PH01.W0.B1B2.ConsumerSelftest@1", "generated_at": now(),
           "arms": arms, "passed": ok, "total": len(arms),
           "note": "one POS baseline plus single-mutation negatives; a consumer that accepted any "
                   "mutation would be a rubber stamp"}
    pth = os.path.join(OPS, "r7_consumer_selftest.json")
    json.dump(out, open(pth, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    for a in arms:
        print(f'{a["arm"]:22s} {a["decision"]:7s} {a["first_fail"] or "":28s} {"OK" if a["pass"] else "FAIL"}')
    print(json.dumps({"passed": ok, "total": len(arms), "written": pth}, ensure_ascii=False))
    return 0


def main() -> int:
    raw = open(READSET, "rb").read()
    env = json.loads(raw)
    out = {"schema": "SST.PH01.W0.B1B2.ConsumerReceipts@1", "generated_at": now(),
           "envelope": {"path": READSET, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)},
           "note": "each consumer fixed its own ExpectedSet before reading the envelope; "
                   "the envelope's observed values are never used as the expectation",
           "receipts": [receive(c, env, raw) for c in ("B1", "B2", "B3")]}
    for r in out["receipts"]:
        print(f'{r["consumer_id"]}: {r["decision"]} {r["first_fail"] or ""}')
    p = os.path.join(OPS, "r7_consumer_receipts.json")
    json.dump(out, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"written": p}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
