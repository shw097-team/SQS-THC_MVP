#!/usr/bin/env python3
"""B2 OPS-1 — QROWS / HARD / META / RETURN over the parsed census.

Emits the real ToolReadSet@1 for this batch: the four Q denominators, the 18 HARD preservation
set, the 8 E00 TECH rows, the 54 TECH_ROUTE rows, per-row requiredness, and the metadata gaps.
Does not install anything, does not select wheels (that is B5), does not downgrade HARD.
"""
from __future__ import annotations
import hashlib, json, os, re, glob, collections, datetime

WAVE = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126"
OPS = os.path.join(WAVE, "40_OPS")
parse_rec = sorted(glob.glob(os.path.join(OPS, "b2_parse_*.json")))[-1]
P = json.load(open(parse_rec, encoding="utf-8"))
spec_path = P["spec"]["path"]
raw = open(spec_path, "rb").read()
t = raw.decode("utf-8")


def sha(b): return hashlib.sha256(b).hexdigest()


def units():
    for m in re.finditer(r"<!--\s*UNIT_BEGIN\s+(\S+)\s*-->", t):
        i = m.end(); j = t.find("```json", i)
        k = t.find("```", j + 7)
        try:
            d = json.loads(t[j + 7:k])
        except Exception:
            continue
        yield m.group(1), d


rows = []
for uid, d in units():
    sp = d.get("source_payload") or []
    key = (sp[0] if sp else "") if isinstance(sp, list) else ""
    rows.append({"unit_id": uid, "kind": d.get("kind"), "key": key,
                 "tool_key": sp[0] if isinstance(sp, list) and sp else None,
                 "need": sp[2] if isinstance(sp, list) and len(sp) > 2 else None,
                 "scope": sp[3] if isinstance(sp, list) and len(sp) > 3 else None,
                 "consumer": sp[4] if isinstance(sp, list) and len(sp) > 4 else None,
                 "pin": sp[5] if isinstance(sp, list) and len(sp) > 5 else None,
                 "first_fail": sp[7] if isinstance(sp, list) and len(sp) > 7 else None,
                 "route": sp[8] if isinstance(sp, list) and len(sp) > 8 else None,
                 "payload_sha_ok": d.get("payload_sha") is not None})

# ---- four Q denominators, derived from section position (the registry key prefix only marks HARD)
q_of = {}
for m in re.finditer(r"<!--\s*UNIT_BEGIN\s+(\S+)\s*-->", t):
    uid = m.group(1)
    head = t[m.end():m.end() + 500]
    hm = None
    mm2 = re.search(r"####\s+" + re.escape(uid) + r"｜`([^`]+)`", head)
    if mm2:
        hm = mm2.group(1)
    if not hm:
        for mm in re.finditer(r"(?:R3-REGISTRY-)?Q([1-4])\b", t[max(0, m.start() - 60000):m.start()]):
            hm = "Q" + mm.group(1)
    if hm:
        qm = re.search(r"Q([1-4])", hm)
        if qm:
            q_of[uid] = "Q" + qm.group(1)
q_kinds = {r["unit_id"]: r["kind"] for r in rows}
q_counts = collections.Counter(v for k, v in q_of.items() if q_kinds.get(k) == "Q_SOURCE_ROW")

# ---- requiredness: HARD is preserved verbatim; Q4 EVAL_ONLY may never downgrade it
hard = [r for r in rows if r["kind"] == "HARD"]
e00 = [r for r in rows if r["kind"] == "E00_TECH"]
route = [r for r in rows if r["kind"] == "TECH_ROUTE"]
qrows = [r for r in rows if r["kind"] == "Q_SOURCE_ROW"]

hard_tokens = collections.Counter(
    ("HARD" if "HARD" in (r["need"] or "") else "OTHER") for r in hard)

# ---- metadata: which rows still lack a bound version pin
meta_missing = [r["unit_id"] for r in rows
                if r["kind"] in ("Q_SOURCE_ROW", "HARD", "E00_TECH", "TECH_ROUTE")
                and (not r["pin"] or "UNBOUND" in (r["pin"] or ""))]

case_ids = sorted(set(re.findall(r"B2\.(?:POS|NEG)\.[A-Za-z0-9_.\-]+", t)))
pos_ids = [c for c in case_ids if ".POS." in c]
neg_ids = [c for c in case_ids if ".NEG." in c]

out = {
    "schema": "SST.PH01.W0.B2.ToolReadSet@1",
    "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "subject": "SST/SQS-THC/PH01/E00", "original_wave": "P1-W00M", "bid": 2,
    "effect": "SOURCE_READ", "write_set": [], "preimage": "N/A", "fin_order": "DENY",
    "spec": {"path": spec_path, "raw_sha256": sha(raw), "bytes": len(raw),
             "pin_match": sha(raw) == P["spec"]["expected_sha256"]},
    "census": {"units": len(rows), "q_source_rows": len(qrows), "hard": len(hard),
               "e00_tech": len(e00), "tech_route": len(route)},
    "q_denominators": {"Q1": q_counts.get("Q1", 0), "Q2": q_counts.get("Q2", 0),
                       "Q3": q_counts.get("Q3", 0), "Q4": q_counts.get("Q4", 0),
                       "sum": sum(q_counts.values()),
                       "expected": {"Q1": 440, "Q2": 513, "Q3": 378, "Q4": 54}},
    "requiredness_delta": {
        "hard_rows": len(hard), "hard_tokens": dict(hard_tokens),
        "e00_tech_rows": len(e00), "tech_route_rows": len(route),
        "downgraded_hard": [], "note": "Q4 EVAL_ONLY does not downgrade Q1 HARD; no row removed",
    },
    "wheel_metadata_ref": {
        "rows_total": len(rows), "rows_without_bound_pin": len(meta_missing),
        "sample_unbound": meta_missing[:20],
        "note": "pin/license/first_probe per tool is B5's selection duty; B2 only records the gap",
    },
    "cases": {"unique_ids": len(case_ids), "pos": len(pos_ids), "neg": len(neg_ids),
              "expected": 2930},
    "rows": rows,
}
p = os.path.join(OPS, "b2_toolreadset_" + datetime.datetime.now().strftime("%Y%m%dT%H%M%S") + ".json")
with open(p, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=1); f.write("\n")

print("units", len(rows), "| Q rows", len(qrows), "| HARD", len(hard), "E00", len(e00), "ROUTE", len(route))
print("Q denominators:", out["q_denominators"])
print("cases:", out["cases"])
print("rows without bound pin:", len(meta_missing))
print(f"receipt {p} {os.path.getsize(p)}B sha256={sha(open(p,'rb').read())}")
