"""Independent probe of the two gates that took more than two repair cycles.

Not a receipt: a maker-side diagnostic that records (a) whether the exclusion relation is a static
declaration rather than something tuned per failing row, and (b) whether the namespace oracle refuses
on identity while a namespace-blind implementation still resolves.

Usage: python -B 20_DEV/b2_gate_probe.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "b2_reader"))
import b2_semantics as S  # noqa: E402

WAVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CASES = [
    (["HARD"], None, "single selection state"),
    (["HARD", "EVAL_ONLY"], "STATE_CONFLICT", "declared exclusion HARD/EVAL_ONLY"),
    (["DEFER_NOFIT", "NOT_SELECTED"], None, "legal compound: a deferral implies not-selected"),
    (["INSTALLED", "ENABLED"], None, "legal coexistence: the probe that keeps the gate from being true"),
    (["INSTALLED", "NOT_INSTALLED"], "STATE_CONFLICT", "declared exclusion installed/not"),
    (["SELECTED_DESIGN_ONLY", "REFERENCE_ONLY"], "STATE_CONFLICT", "competing selections"),
    (["REUSE_INTERNAL_DESIGN"], None, "single state"),
]


def main() -> int:
    spec = S.load_spec()
    us = S.units(spec["text"])
    states = sorted({str((u.get("source_payload") or [""])[2]) for u in us
                     if u.get("kind") == "E00_TECH"})
    pairs = {}
    for st in states:
        pair = S.contradicting_state(st)
        if pair is None:
            pairs[st] = {"contradicting_state": None,
                         "status": "HOLD_NO_DECLARED_COUNTERPART"}
            continue
        pairs[st] = {"contradicting_state": pair,
                     "baseline": S.state_gate([st]),
                     "mutated": S.state_gate([st, pair]),
                     "status": "OK" if (S.state_gate([st]) is None
                                        and S.state_gate([st, pair]) == "STATE_CONFLICT")
                     else "DEFECT"}

    q = [u for u in us if u.get("kind") == "Q_SOURCE_ROW"]
    idx, tail = {}, {}
    for u in q:
        idx.setdefault(u["key"], []).append(u["unit_id"])
        tail.setdefault(u["key"].split("::")[-1], []).append(u["key"])
    ns = []
    for u in (q[0], q[500], q[-1]):
        try:
            S.join_rows({"key": u["key"].split("::", 1)[1]}, idx, tail)
            got = None
        except S.OracleError as e:
            got = str(e)
        ns.append({"unit_id": u["unit_id"],
                   "baseline_rows": len(S.join_rows({"key": u["key"]}, idx, tail)),
                   "namespace_dropped": got,
                   "naive_matches": len(S.namespace_blind_lookup(u["key"], idx, tail))})

    out = {
        "schema": "SST.W0.B2.GATE_PROBE/1",
        "why": "the STATE_CONFLICT oracle and the namespace oracle each needed more than two repair "
               "cycles; this probe records whether the relation is declared or fitted",
        "state_gate_cases": [{"input": i, "expected": e, "observed": S.state_gate(i),
                              "ok": S.state_gate(i) == e, "note": n} for i, e, n in CASES],
        "state_gate_all_ok": all(S.state_gate(i) == e for i, e, n in CASES),
        "exclusive_pairs_natural": [list(p) for p in S.EXCLUSIVE_PAIRS_NATURAL],
        "exclusive_pairs_maker_declared_not_used_for_cases": [list(p)
                                                              for p in S.EXCLUSIVE_PAIRS_MAKER_DECLARED],
        "e00_rows": pairs,
        "e00_rows_ok": all(v["status"] in ("OK", "HOLD_NO_DECLARED_COUNTERPART")
                           for v in pairs.values()),
        "e00_rows_with_declared_counterpart": sum(1 for v in pairs.values() if v["status"] == "OK"),
        "e00_rows_hold_no_counterpart": sum(1 for v in pairs.values()
                                           if v["status"] == "HOLD_NO_DECLARED_COUNTERPART"),
        "namespace_probe": ns,
        "claim": "MAKER_DIAGNOSTIC_ONLY — not an acceptance, not a substitute for the checker",
    }
    p = os.path.join(WAVE, "40_OPS", "b2_gate_probe.json")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("state_gate_all_ok", out["state_gate_all_ok"], "| e00_rows_ok", out["e00_rows_ok"])
    print("  natural", len(out["exclusive_pairs_natural"]), "| maker-declared (not used)",
          len(out["exclusive_pairs_maker_declared_not_used_for_cases"]))
    for c in out["state_gate_cases"]:
        print(f"  {c['observed']!s:>16} exp {c['expected']!s:>16} ok={c['ok']}  {c['input']}")
    print("namespace", ns)
    print("receipt", p, os.path.getsize(p), "B")
    return 0 if out["state_gate_all_ok"] and out["e00_rows_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
