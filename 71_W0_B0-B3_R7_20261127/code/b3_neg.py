#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 original NEG mutations, executed against the product entry.

Each CaseID keeps its original identity; the mutation is applied to a copy of that Unit and the
mutated set is fed to the real CHILD/ROUTE entry. A refusal only counts when the product itself
refuses with a specific first failure - not when a helper inspects a string.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import b3_product as P
import w0_spec as SPEC

OPS = P.OPS


def classify(case_id: str, unit: dict) -> str:
    c = case_id.upper()
    if "DELETE_CHILD" in c:
        return "DELETE_CHILD"
    if "DELETE_NEG" in c:
        return "DELETE_NEG"
    if "CHILD" in c and unit.get("kind") == "CHILD":
        return "DELETE_CHILD"
    if unit.get("kind") == "PROTECTED":
        return "PROTECTED_FIELD"
    return "GENERIC_REMOVE"


def mutate(units: list[dict], unit: dict, how: str):
    out = [u for u in units if u["unit_id"] != unit["unit_id"]]
    if how == "PROTECTED_FIELD":
        bad = copy.deepcopy(unit)
        bad["direct_clause_sha"] = "0" * 64          # a protected identity field is altered
        out.append(bad)
    elif how == "DELETE_NEG":
        out.append({**copy.deepcopy(unit), "key": unit["key"] + "::DELETED"})
    # DELETE_CHILD / GENERIC_REMOVE: the atom is simply gone from the set
    return out


def run() -> dict:
    spec = SPEC.load("B3")
    units = SPEC.units(spec["text"])
    base_child = P.op_child(units)
    base_ready = sum(1 for a in base_child["atoms"] if a["disposition"] == "READY_ATOM")
    rows = []
    for u in units:
        if u.get("kind") not in ("CHILD", "PROTECTED"):
            continue
        for cid in u.get("case_ids") or []:
            if ".NEG." not in cid:
                continue
            how = classify(cid, u)
            mutated = mutate(units, u, how)
            child = P.op_child(mutated)
            route = P.op_route(mutated, child)
            atom = next((a for a in child["atoms"] if a["atom"] == u["key"]), None)
            rt = next((r for r in route["routes"] if r["atom"] == u["key"]), None)
            refused_by_child = atom is None or atom["disposition"] != "READY_ATOM"
            refused_by_route = rt is None or rt["route_out"] != "ROUTE_OUT"
            first_fail = ((atom or {}).get("evidence") or {}).get("decision") or \
                         (rt or {}).get("first_fail") or ("ATOM_ABSENT" if atom is None else None)
            rows.append({"case_id": cid, "unit_id": u["unit_id"], "key": u["key"],
                         "kind": u.get("kind"), "mutation": how,
                         "product_entry": "op_child+op_route over the mutated set",
                         "refused": bool(refused_by_child or refused_by_route),
                         "first_fail": first_fail,
                         "verdict": "PASS_REFUSAL" if (refused_by_child or refused_by_route) else "FAIL"})
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    out = {"schema": "SST.PH01.W0.B3.NegMutations@1", "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "baseline": {"units": len(units), "atoms_ready_before": base_ready},
           "cases": rows, "counts": counts,
           "claim_ceiling": ("a refusal executed by the product entry over a mutated unit set; "
                             "it does not prove the downstream wave would behave the same")}
    p = os.path.join(OPS, "b3_r7_neg_mutations.json")
    json.dump(out, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"written": p, "counts": counts, "cases": len(rows)}, ensure_ascii=False))
    return out


if __name__ == "__main__":
    run()
