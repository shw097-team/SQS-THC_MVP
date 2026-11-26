#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 typed fixtures (BEHAVIOR / SEAM / RECOVERY) and the CLOSEOUT / HANDOFF documents.

The fixtures are a typed skeleton: the fields the original cases name, bound to the verified
source evidence. They are NOT a semantic oracle - that needs the original Reader - and the
ceiling is written into every file.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import b3_product as P
import w0_spec as SPEC

OPS = P.OPS
OUT = os.path.join(P.W, "60_CLOSEOUT")
KINDS = ("BEHAVIOR_ROUTE", "AUTHORITY_SEAM", "RECOVERY")


def typed_fixture(u: dict) -> dict:
    """Fields the original case names, with the evidence that was actually recomputed."""
    ev = P.verify_mapping(u)
    pol = None
    blob = json.dumps(u, ensure_ascii=False)
    m = re.search(r"(POSITIVE|NEGATIVE|POLARITY_[A-Z_]+)", blob)
    if m:
        pol = m.group(1)
    return {
        "unit_id": u["unit_id"], "atom": u.get("key"), "kind": u.get("kind"),
        "PH": "PH01", "W": "E00", "B": P.ROUTE_TARGET.get(u.get("kind"), ("E00", "?", "?"))[1],
        "owner": u.get("owner"),
        "reader": u.get("reader") or "ORIGINAL_READER_UNBOUND",
        "polarity": pol or "NOT_DECLARED_IN_PAYLOAD",
        "protected_field": {"direct_clause_sha": u.get("direct_clause_sha"),
                            "payload_sha": u.get("payload_sha")},
        "expected_set": {"direct_parent_ref": u.get("direct_parent_ref"),
                         "resolved_source_ref": u.get("resolved_source_ref")},
        "trigger": "case-level invocation of the B3 ROUTE entry",
        "first_fail": None if ev["decision"] == "SOURCE_BOUND_VERIFIED" else ev["decision"],
        "source_evidence": {"decision": ev["decision"],
                            "clause_sha_observed": ev.get("clause_sha_observed"),
                            "binding": ev.get("binding")},
        "fixture_ceiling": "TYPED_SKELETON_NOT_SEMANTIC_ORACLE",
    }


def build_fixtures() -> dict:
    spec = SPEC.load("B3")
    units = SPEC.units(spec["text"])
    out = {}
    for k in KINDS:
        rows = [typed_fixture(u) for u in units if u.get("kind") == k]
        out[k] = {"count": len(rows), "fixtures": rows}
    doc = {"schema": "SST.PH01.W0.B3.TypedFixtures@1",
           "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "kinds": out,
           "claim_ceiling": ("typed skeleton bound to verified source evidence; the semantic "
                             "Oracle and the original Reader are still unbound, so no case is "
                             "called a semantic PASS on the strength of these fixtures")}
    p = os.path.join(OPS, "b3_r5_typed_fixtures.json")
    json.dump(doc, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    return doc


def load(name):
    p = os.path.join(OPS, name) if not name.startswith("40_") else os.path.join(P.W, name)
    return json.load(open(p, encoding="utf-8"))


def closeout(fx: dict) -> dict:
    tqaep = load("b3_r5_tqaep.json")
    prod = load("b3_r5_product.json")
    neg = load("b3_r5_neg_mutations.json") if os.path.isfile(os.path.join(OPS, "b3_r5_neg_mutations.json")) else {}
    cons = load("r5_consumer_receipts.json") if os.path.isfile(os.path.join(OPS, "r5_consumer_receipts.json")) else {}
    freeze = load("b1b2_r5_candidate_freeze.json")
    vc = tqaep["verdict_counts"]
    body = f"""# SST_PLP_PH01_W0_B3 — CLOSEOUT（r5，B3 四 Op 首輪真施工）

- 產生：{time.strftime('%Y-%m-%dT%H:%M:%S%z')}
- SPEC：B3 r4 HERMES_FINAL `a1d759c7157c4ca8d34acb3f0730b74f653baaa86eb5c3c4302837d0df6deac1`
- 候選凍結：`{freeze.get('manifest_sha256')}`（{freeze.get('artefacts')} 成員）
- `FIN_ORDER=DENY`、`distribution=LOCAL_ONLY`、產品效果僅 `SOURCE_READ+IN_MEMORY_TRANSFORM(+LOCAL_DRAFT_WRITE)`

## 1｜四 Op 實跑

| Op | 結果 |
|---|---|
| JOIN | {prod['join']['rows']} 列：ready {prod['join']['ready']}／held {prod['join']['held']}；errors {prod['join']['errors']} |
| CHILD | {prod['child']['atoms']} atom：READY_ATOM {prod['child']['ready']}／HOLD {prod['child']['held']} |
| ROUTE | {prod['route']['routes']} 條：ROUTE_OUT {prod['route']['route_out']}／HOLD {prod['route']['hold']} |
| COMMIT | `{prod['commit'].get('decision')}`{('｜' + str(prod['commit'].get('bytes')) + ' B｜' + str(prod['commit'].get('sha256'))[:16] + '｜preimage ' + str(prod['commit'].get('preimage'))) if prod['commit'].get('decision') == 'COMMITTED' else ('｜' + str(prod['commit'].get('first_fail')))} |

## 2｜752 案真分帳

| 判定 | 案數 |
|---|---:|
| PASS_SOURCE_BOUND | {vc.get('PASS_SOURCE_BOUND',0)} |
| PASS_REFUSAL | {vc.get('PASS_REFUSAL',0)} |
| HOLD | {vc.get('HOLD',0)} |
| NOT_EXECUTED | {vc.get('NOT_EXECUTED',0)} |

原始 NEG 逐案 mutation（`b3_r5_neg_mutations.json`）：{json.dumps(neg.get('counts', {}), ensure_ascii=False)}

## 3｜typed fixture

| kind | 數量 | 上限 |
|---|---:|---|
| BEHAVIOR_ROUTE | {fx['kinds']['BEHAVIOR_ROUTE']['count']} | TYPED_SKELETON_NOT_SEMANTIC_ORACLE |
| AUTHORITY_SEAM | {fx['kinds']['AUTHORITY_SEAM']['count']} | 同上 |
| RECOVERY | {fx['kinds']['RECOVERY']['count']} | 同上 |

## 4｜接收

{('B0→B1/B2/B3：' + '、'.join(f"{r['consumer_id']}={r['decision']}" for r in cons.get('receipts', []))) if cons else 'B0 接收收據未在本次載入（本地檔存在）'}

## 5｜未成立與 Resume

| 項 | 現況 | Resume |
|---|---|---|
| B3_ACCEPTED | **未宣** | 需分離 Checker 對同候選、逐案語義 Oracle、原 Reader |
| 10 份文件 heading 不符（20 案） | HOLD，兩數並列 | 由原文件作者確認計數規則或內容版本 |
| 62/92 DOC_BRIDGE pin | 不在 `【4】舊版封存` | 指出其餘世代的合法位置 |
| ROUTE 語義 | 只到來源可證 | 需原 H1/Behaviour 的 ROUTE_OUT 契約 |
| B4／B5 准入 | 見下節 | 依各自 mandatory 真接收 |

## 6｜B4／B5 四 Ready 判定

| 批 | ReadyDraft | ReadyAtom | ReadyExecute | ReadyAccept |
|---|---|---|---|---|
| B4 | 可（B1 RepoReadSet＋B3 Ledger 結構） | 部分（22 atom） | 不可（B1 RepoRoot／D-1、D-3 未閉合） | 不可 |
| B5 | 可（B2 ToolReadSet 1,465＋metadata 2 條） | 部分（HARD 18 中僅 2 有 metadata） | 不可（B2 76 HOLD、TT-UP-1 未取） | 不可 |

## 7｜宣稱上限

本文件不是 B3 產品接受；`B3_ACCEPTED`、`W0_COMPLETE`、`W1 ReadyExecute` 均未成立。
"""
    handoff = f"""# SST_PLP_PH01_W0_B3 — HANDOFF（r5）

- 同候選凍結：`{freeze.get('manifest_sha256')}`
- 產出：`40_OPS/b3_r5_product.json`（四 Op）、`b3_r5_tqaep.json`（752 案）、`b3_r5_neg_mutations.json`（原 NEG）、`b3_r5_typed_fixtures.json`（typed skeleton）、`b3_draft/SourceChildLedger.draft.v2.json`（工程投影）、`b3_ledger/SourceChildLedger.draft.v2.md`（真 LOCAL_DRAFT_WRITE）

## 下游接口（mandatory）

| Consumer | 需要 B3 提供 | 現況 |
|---|---|---|
| B4 | `SourceChildLedger` 的 atom／owner／scope／source_sha | 22 atom 有完整三欄；其餘標 HOLD |
| B5 | `SourceChildLedger` 的 atom／requiredness／owner | 同上（requiredness 來自 B2 對映，僅工具型 atom） |
| B7 | `ref／digest／hold_set` | digest 可出；hold_set 為 92 atom |

## 下一手

1. 分離 Checker 對本候選（`{freeze.get('manifest_sha256')}`）逐案語義驗收
2. 10 份文件 heading 規則確認
3. 其餘 62 個 DOC pin 的世代位置
4. B4／B5 各自的真 mandatory 接收（不是 B3 自稱）
"""
    pc = os.path.join(OUT, "SST_PLP_PH01_W0_B3_CLOSEOUT.md")
    ph = os.path.join(OUT, "SST_PLP_PH01_W0_B3_HANDOFF.md")
    open(pc, "w", encoding="utf-8", newline="\n").write(body)
    open(ph, "w", encoding="utf-8", newline="\n").write(handoff)
    return {"closeout": pc, "handoff": ph,
            "closeout_sha": hashlib.sha256(body.encode()).hexdigest(),
            "handoff_sha": hashlib.sha256(handoff.encode()).hexdigest()}


if __name__ == "__main__":
    fx = build_fixtures()
    print(json.dumps({"fixtures": {k: v["count"] for k, v in fx["kinds"].items()}}, ensure_ascii=False))
    print(json.dumps(closeout(fx), ensure_ascii=False, indent=1))
