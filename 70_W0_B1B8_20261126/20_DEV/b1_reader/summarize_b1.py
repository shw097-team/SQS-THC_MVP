#!/usr/bin/env python3
"""Aggregate the latest B1 receipt into the numbers the CLOSEOUT/HANDOFF will quote."""
import json, glob, os, hashlib

OPS = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126\40_OPS"
p = sorted(glob.glob(os.path.join(OPS, "b1_run_*.json")))[-1]
d = json.load(open(p, encoding="utf-8"))

rows = {r["unit_id"]: r for op in ("B1.BASE", "B1.FDA") for r in d["ops"][op]["rows"]}
v = {}
for r in rows.values():
    v[r["verdict"]] = v.get(r["verdict"], 0) + 1

kernels = []
for r in rows.values():
    if r["kind"] != "KERNEL":
        continue
    syms = {}
    for res in r["resolutions"]:
        for m in res["measured"]:
            s = m.get("symbols") or {}
            if s.get("ast") == "PARSED":
                syms = s
    kernels.append({"key": r["key"], "verdict": r["verdict"],
                    "path": r["declared_paths"][0],
                    "blob": (r["resolutions"][0]["measured"][0]["git_blob_sha1"]
                             if r["resolutions"][0]["measured"] else None),
                    "bytes": (r["resolutions"][0]["measured"][0]["bytes"]
                              if r["resolutions"][0]["measured"] else None),
                    "raw_sha256": (r["resolutions"][0]["measured"][0]["raw_sha256"]
                                   if r["resolutions"][0]["measured"] else None),
                    "public_symbols": syms.get("public")})

missing = [{"unit": r["unit_id"], "key": r["key"], "verdict": r["verdict"],
            "declared": r["declared_paths"]}
           for r in rows.values() if r["verdict"] != "OBSERVED_IN_REPO"]

summary = {
    "receipt": p, "receipt_sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(),
    "generated_at": d["generated_at"],
    "repo": d["repo"], "tree_entries": d["tree_entries"],
    "spec": d["spec"],
    "units": len(rows),
    "cases": sum(len(r["case_ids"] or []) for r in rows.values()),
    "verdict_counts": v,
    "kernels": kernels,
    "not_observed": missing,
    "no_write": d["ops"]["no_write"]["verdict"],
    "roots": {"edges": len(d["ops"]["B1.ROOTS"]["rows"]),
              "status": sorted({r["physical_status"] for r in d["ops"]["B1.ROOTS"]["rows"]})},
}
out = os.path.join(OPS, "b1_summary.json")
json.dump(summary, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print(json.dumps({k: summary[k] for k in
                  ("units", "cases", "verdict_counts", "no_write", "roots")},
                 ensure_ascii=False, indent=1))
print("\nKERNELS")
for k in kernels:
    print(f"  {k['key']:20s} {k['verdict']:18s} blob={str(k['blob'])[:10]} {k['bytes']}B "
          f"public={len(k['public_symbols'] or [])}")
    print("     ", ", ".join((k["public_symbols"] or [])[:12]))
print("\nNOT OBSERVED")
for m in missing:
    print(f"  {m['unit']} {m['key']:34s} {m['verdict']}")
print("\nsummary:", out)
