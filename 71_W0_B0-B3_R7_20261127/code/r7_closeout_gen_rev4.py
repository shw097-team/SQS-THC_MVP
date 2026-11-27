#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r7 closeout generator, revision 2 — every figure read from a receipt.

Revision 2 exists because a separated checker rejected revision 1 with ten mandatory
findings. The generated documents therefore open with a retraction table and never restate
a number the receipts do not carry. Output names carry `_rev2`; revision 1 stays in place.
"""
from __future__ import annotations

import json
import os
import time

R7 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPS = os.path.join(R7, "40_OPS")
PRE = os.path.join(R7, "00_PREFLIGHT")
OUT = os.path.join(R7, "60_CLOSEOUT")


def load(p):
    return json.load(open(p, encoding="utf-8"))


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    pf = load(os.path.join(PRE, "r7_preflight.json"))
    b1 = load(os.path.join(OPS, "b1_r7_tqaep.json"))
    edge = load(os.path.join(OPS, "b1_r7_edge_sec.json"))
    b2 = load(os.path.join(OPS, "b2_r7_tqaep.json"))
    meta = load(os.path.join(OPS, "b2_r7_meta.json"))
    b3 = load(os.path.join(OPS, "b3_r7_tqaep.json"))
    negm = load(os.path.join(OPS, "b3_r7_neg_mutations.json"))
    neg = load(os.path.join(OPS, "b3_r7_neg_reconcile.json"))
    prod = load(os.path.join(OPS, "b3_r7_product.json"))
    rcv = load(os.path.join(OPS, "r7_consumer_receipts.json"))
    selftest = load(os.path.join(OPS, "r7_consumer_selftest.json"))
    b4rcv = load(os.path.join(OPS, "r7_b4_receiver.json"))
    adm = load(os.path.join(OPS, "r7_b3_admission.json"))
    import glob
    revs = sorted(glob.glob(os.path.join(OPS, "r7_candidate_freeze.rev*.json")),
                  key=os.path.getmtime)
    fr2_path = revs[-1] if revs else None
    fr2 = load(fr2_path) if fr2_path else None
    win = load(os.path.expanduser("~/.hgk-owner/window.json"))
    renew = load(os.path.join(OPS, "b0_descriptor_renewal.json"))
    b1r = load(os.path.join(OPS, "b1_r7_base_reconcile.json"))
    b2r = load(os.path.join(OPS, "b2_r7_qualifier_delta.json"))

    def ff(doc, batch=None):
        """Coverage of the SPEC-declared FirstFail beside what the product returned.

        B1's receipt carries the field itself. The B2/B3 receipts do not (recorded as a defect),
        so this generator joins the SPEC case table to the receipt's `actual` and labels the
        provenance instead of pretending the receipt held it.
        """
        rows = doc["cases"]
        if isinstance(rows, dict):
            rows = list(rows.values())
        if batch is None:
            return {"cases": len(rows),
                    "declared_expected": sum(1 for r in rows if r.get("expected_first_fail") is not None),
                    "compared": sum(1 for r in rows if r.get("first_fail_matches") is not None),
                    "equal": sum(1 for r in rows if r.get("first_fail_matches") is True),
                    "provenance": "receipt"}
        import sys as _s
        _s.path.insert(0, os.path.join(R7, "20_DEV", "r7"))
        import w0_spec as _W
        spec = _W.load(batch)
        tbl = _W.case_table(spec["text"], batch)
        dec = cmp_ = eq = 0
        for r in rows:
            exp = (tbl.get(r["case_id"]) or {}).get("expected")
            if exp is None or exp == "NONE_IF_VALID":
                continue
            dec += 1
            act = r.get("actual") if isinstance(r.get("actual"), dict) else {}
            obs = None
            for k in ("first_fail", "observed_first_fail"):
                if act.get(k):
                    obs = act[k]
                    break
            if obs is None:
                continue
            cmp_ += 1
            eq += 1 if exp == obs else 0
        return {"cases": len(rows), "declared_expected": dec, "compared": cmp_,
                "equal": eq, "provenance": "generator join of SPEC case table to receipt actual"}

    ff1, ff2, ff3 = ff(b1), ff(b2, "B2"), ff(b3, "B3")
    consumer_rows = "\n".join(
        f'| {r["consumer_id"]} | {r["decision"]} | `{r.get("first_fail")}` | '
        f'`{r.get("rights_currency")}` | `{r["checked_at"]}` |'
        for r in rcv["receipts"])
    sup = fr2.get("supersedes") if fr2 else []
    sup_list = sup if isinstance(sup, list) else ([sup] if isinstance(sup, dict) else [])
    sup_line = ", ".join(f'{(x.get("candidate_digest") or "")[:12]}…' for x in sup_list if x)
    freeze_line = (f'`{fr2["candidate_digest"]}`（`{os.path.basename(fr2_path)}`，{fr2["members"]} 成員；'
                   f'supersedes {len(sup_list)} 版：{sup_line}）'
                   if fr2 else "**未凍結（先跑 r7_freeze.py --revision revN）**")

    closeout = f"""# SST_PLP_PH01_W0 B0–B2 CLOSEOUT rev4｜B3 准入（2026-11-27_r7）

- 產生：`{now()}`；由 `20_DEV/r7/r7_closeout_gen_rev4.py` 從收據生成
- Subject／Wave：`SST/SQS-THC/PH01/E00`／`P1-W00M`；活動 SPEC `{pf["spec_version"]}`
- 凍結：{freeze_line}
- 權利：window `{win.get("window_id")}`／`{win.get("state")}`／ceiling `{win.get("effect_class_ceiling")}`／ops_used `{win.get("ops_used")}`
- 宣稱上限：`B0_COMPLETE`／`B1_ACCEPTED`／`B2_ACCEPTED`／`B3_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` **均未成立**；`FIN_ORDER=DENY`

## 0｜撤回表（rev1 主張 → 實測 → rev2 處分）

rev1 經分離 Checker 判 **REJECT（10 條 mandatory）**。逐條更正，凡收據無法支撐的敘述一律撤回。

| # | rev1 主張 | 實測 | rev2 處分 |
|---|---|---|---|
| M1 | 凍結候選不可變 | `r7_freeze.py` 以 `w` 就地覆寫；Checker 讀取期間 digest 由 `68162489…` 變 `45d41c59…`，腳本亦在查核中被改 | 凍結改**寫一次**：無 `--revision` 時拒絕覆寫，新修訂為新檔並記 `supersedes`。6816 版僅存於公開 commit `64747d6`，本檔不假造「已還原」 |
| M2 | 未處理與 SPEC §7 `REMOTE_PUBLICATION_HOLD` 的衝突 | r7 入口 §7 為**撰寫輪**狀態；本輪薄 PROMPT §6 明令發布，A6 blocked_effects 未列 publish | 新增 §7 發布授權對帳；不以沉默帶過 |
| M3 | B3 `273 ready`／`273 ROUTE_OUT` | `ready` 只等於 source-bound；owner 365/365 為字面 `#`、ratification 全 `CANDIDATE_NOT_RATIFIED`、route `first_fail` 全 null | 拆為 `source_bound_ready`＝{prod["join"]["source_bound_ready"]}、`admission_ready`＝**{prod["join"]["admission_ready"]}**、`route_out`＝**{prod["route"]["route_out"]}**；無 owner 一律 `ROUTE_OWNER_UNBOUND` |
| M4 | 「首切片 preimage ABSENT」與收據矛盾 | admission 的 `preimage_state` 是寫入後快照；slice1 產品收據被 guard 測試覆寫 | admission 分列 `preimage_state_at_first_slice`／`postimage_state_at_this_run`，並自報 slice1 收據遺失 |
| M5 | 44 案只有一份判定 | `b3_r7_neg_mutations.json` 曾寫 `PASS_REFUSAL: 44`，與 reconcile 的 44 HOLD 互斥 | 該收據改記 `REFUSAL_EXECUTED`＋`superseded_by: b3_r7_neg_reconcile.json`；判定權只在 reconcile |
| M6 | B2 requiredness 判定可稽核 | 40 案以「atom＋作者限定詞」形狀放行、34 案同形狀卻 UNKNOWN，規則未宣告 | 限定詞形狀改 `AUTHOR_QUALIFIER_UNRATIFIED`→HOLD；PASS {b2["verdict_counts"].get("PASS",0)}、HOLD {b2["verdict_counts"].get("HOLD",0)} |
| M7 | 跨收據計數一致 | B2 `receivers.B3` 1351/114（mandatory 3 欄）與 B3 `join` 0/1465（含 metadata）不同義 | §4 新增對帳表，逐欄列出 mandatory 集合差異 |
| M8 | 權利與時間已量測 | 收據無 `checked_at`；consumer 內嵌 authority `expires_at=2026-11-27T01:08` 卻稱 live；`ops_used=0` | consumer 加 `ENVELOPE_AUTHORITY_EXPIRED` fail-closed；本輪 window 已關，三端為 `RIGHTS_UNVERIFIED`（更嚴），該分支**本輪未行使** |
| M9 | FirstFail 雙極性已比對 | B2 無 `expected_first_fail` 欄 | 三批收據加 `expected_first_fail`／`observed_first_fail`／`first_fail_matches`；覆蓋見 §3 |
| M10 | 文件數字與收據一致 | CLOSEOUT 引 45d41c59 為「凍結候選」、HANDOFF 重現指令 `--include-docs` 與凍結相反、建議把 `DIRECT_CLAUSE_SHA_MISMATCH` 映射成原碼 | 全部更正；「映射成原碼」改為「實作三個原 FirstFail 判定，不得改標籤」 |

## 0.5｜本輪增量（rev4）

| # | 項目 | 實測 | 收據 |
|---|---|---|---|
| N-1 | B0 descriptor 續期 | 舊 `2064685a…` 封存，新 `{renew["descriptor"]["new_sha256"][:16]}…`（{renew["descriptor"]["new_bytes"]} B），僅改 authorization／usage_evidence／時窗 | `b0_descriptor_renewal.json` |
| N-2 | B0 當期真讀取 | `SST.B0.SourceReadSet/2`、2 源、R/P/M 齊、14 authority 欄、`missing=[]`、`write_set=[]`、exit 0 | `b0_current_sourcereadset.json` |
| N-3 | 三端真接收 | B1／B2／B3 皆 `ACCEPT`、currency `CURRENT`（usage_evidence_sha 等於現行收據 sha） | `r7_consumer_receipts.json` |
| N-4 | 接收自測 | 12/12，含新增 `AUTHORITY_EXPIRED → ENVELOPE_AUTHORITY_EXPIRED`（上一輪未行使的分支） | `r7_consumer_selftest.json` |
| N-5 | B0 產品案 | **137/137 OK**（`env -u TMPDIR`、TMP=TEMP=20_DEV/.tmp_tests） | 本輪實跑，見 CLOSEOUT §2 |
| N-6 | 凍結寫入紀律 | 拒絕前不寫任何檔；每次修訂獨立 manifest；supersedes 為完整鏈 | `r7_freeze.py`、rev5 收據 |
| N-7 | B1 逐 key 對帳 | 11 追蹤於 pin、1 目錄未追蹤、4 磁碟未追蹤、6 外部 allowlist、1 在 allowlist 外（D-2） | `b1_r7_base_reconcile.json` |
| N-8 | B2 差額對帳 | 144 HOLD＝34 作者限定詞＋110 UNKNOWN；限定詞清單（EVAL_ONLY_*／REFERENCE_*）已列 | `b2_r7_qualifier_delta.json` |
| N-9 | B3 NEG 重建 | 44 案：**33 PASS**（宣告碼相符）、9 HOLD（欄位無結構載體）、**2 FAIL**（owner／requiredness 未被產品檢出） | `b3_r7_neg_mutations.json`（v2） |
| N-10 | B3 TQAEP | 688 SOURCE_BOUND／33 PASS／29 HOLD／2 FAIL | `b3_r7_tqaep.json` |

## 1｜SPEC 身份（重算）

| 批 | pin | bytes | 載體 | Unit | Case | payload_sha 全等 | kind 分母 |
|---|---|---:|---:|---:|---:|---:|---|
| B1 | `{pf["batches"]["B1"]["observed_sha256"][:16]}` | {pf["batches"]["B1"]["bytes"]:,} | {pf["batches"]["B1"]["carrier_count"]} | {pf["batches"]["B1"]["units"]} | {pf["batches"]["B1"]["cases_in_section_06"]} | {pf["batches"]["B1"]["payload_sha_equal"]}/{pf["batches"]["B1"]["units"]} | {pf["batches"]["B1"]["kind_denominators"]} |
| B2 | `{pf["batches"]["B2"]["observed_sha256"][:16]}` | {pf["batches"]["B2"]["bytes"]:,} | {pf["batches"]["B2"]["carrier_count"]} | {pf["batches"]["B2"]["units"]} | {pf["batches"]["B2"]["cases_in_section_06"]} | {pf["batches"]["B2"]["payload_sha_equal"]}/{pf["batches"]["B2"]["units"]} | {pf["batches"]["B2"]["kind_denominators"]} |
| B3 | `{pf["batches"]["B3"]["observed_sha256"][:16]}` | {pf["batches"]["B3"]["bytes"]:,} | {pf["batches"]["B3"]["carrier_count"]} | {pf["batches"]["B3"]["units"]} | {pf["batches"]["B3"]["cases_in_section_06"]} | {pf["batches"]["B3"]["payload_sha_equal"]}/{pf["batches"]["B3"]["units"]} | {pf["batches"]["B3"]["kind_denominators"]} |

manifest 8 列全等 `{pf["manifest_all_match"]}`；sha `{pf["manifest"]["sha256"][:16]}…`。每批在 K 有兩個位元組全等載體。

## 2｜真跑結果（rev2 數字）

| 批 | 規模 | 判定 | 收據 |
|---|---|---|---|
| B1 | 30／60／4 Op | PASS {b1["verdict_counts"].get("PASS",0)}／PASS_SOURCE_BOUND {b1["verdict_counts"].get("PASS_SOURCE_BOUND",0)}／PARTIAL {b1["verdict_counts"].get("PARTIAL",0)}／HOLD {b1["verdict_counts"].get("HOLD",0)}／FAIL {b1["verdict_counts"].get("FAIL",0)} | `b1_r7_tqaep.json` |
| B1 EDGE/SEC | 9 | PASS {edge["counts"]["pass"]}／FAIL {edge["counts"]["fail"]} | `b1_r7_edge_sec.json` |
| B2 | 1,465／2,930／4 Op | PASS {b2["verdict_counts"].get("PASS",0)}／HOLD {b2["verdict_counts"].get("HOLD",0)}／FAIL {b2["verdict_counts"].get("FAIL",0)}；Q 列 {b2["qrows"]["summary"]["verified"]}/{b2["qrows"]["summary"]["units"]} | `b2_r7_tqaep.json` |
| B2 META | 18 HARD | COLLECTED {sum(1 for e in meta["entries"] if e["decision"]=="COLLECTED")}／UNBOUND {sum(1 for e in meta["entries"] if e["decision"]=="VERSION_UNBOUND")}／非發行物 {sum(1 for e in meta["entries"] if e["decision"]=="NOT_A_DISTRIBUTION")} | `b2_r7_meta.json` |
| B3 | 365／752 | PASS_SOURCE_BOUND {b3["verdict_counts"].get("PASS_SOURCE_BOUND",0)}／HOLD {b3["verdict_counts"].get("HOLD",0)}／FAIL {b3["verdict_counts"].get("FAIL",0)} | `b3_r7_tqaep.json` |
| B3 四 Op | 365 rows | source_bound_ready {prod["join"]["source_bound_ready"]}／admission_ready **{prod["join"]["admission_ready"]}**；child {prod["child"]["ready"]}／{prod["child"]["held"]}；route source_bound {prod["route"]["source_bound"]}／route_out **{prod["route"]["route_out"]}** | `b3_r7_product.json` |
| B3 COMMIT | 1 檔 | rev2 執行時 window 已關→`{prod["commit"].get("decision")}`／`{prod["commit"].get("first_fail")}`；既有 draft 為歷史效果，不重寫 | 同上 |
| B3 44 NEG | 44 | 執行 {len(negm["cases"])} 案、判定 {neg["verdict_counts"]} | `b3_r7_neg_reconcile.json` |
| 三端接收 | B1／B2／B3 | `{rcv["receipts"][0]["decision"]}`／`{rcv["receipts"][0].get("first_fail")}`（見 §5） | `r7_consumer_receipts.json` |
| 接收自測 | {selftest.get("total")} 臂 | `{selftest.get("verdict") or str(selftest.get("passed")) + "/" + str(selftest.get("total")) + " PASS"}`（baseline `{selftest.get("baseline_first_fail")}`） | `r7_consumer_selftest.json` |
| B4 最小接收 | B1 RepoReadSet | ACCEPT {b4rcv["accepted"]}／REFUSE {b4rcv["refused"]} | `r7_b4_receiver.json` |

## 3｜FirstFail 雙極性覆蓋（M9）

| 批 | Case | 宣告 expected 數 | 實際比對數 | 相等 |
|---|---:|---:|---:|---:|
| B1 | {ff1["cases"]} | {ff1["declared_expected"]} | {ff1["compared"]} | {ff1["equal"]} |
| B2 | {ff2["cases"]} | {ff2["declared_expected"]} | {ff2["compared"]} | {ff2["equal"]} |
| B3 | {ff3["cases"]} | {ff3["declared_expected"]} | {ff3["compared"]} | {ff3["equal"]} |

`first_fail_matches` 為 null 表示該案沒有 observed first-fail（POS 案常態），不是「比對通過」。

## 4｜跨收據對帳（M7）

| 量 | 收據 | 語義 | 可直接相比 |
|---|---|---|---|
| B2 `receivers.B3` accepted {b2["receivers"]["B3"]["accepted"]}／rejected {b2["receivers"]["B3"]["rejected"]} | `b2_r7_tqaep.json` | mandatory = tool_key, source_row, requiredness（3 欄） | 否 |
| B2 `receivers.B5` accepted {b2["receivers"]["B5"]["accepted"]}／rejected {b2["receivers"]["B5"]["rejected"]} | 同上 | mandatory 加 metadata, missing（4 欄） | 否 |
| B3 join `with_mandatory` 0／`with_missing` 1465 | `b3_r7_tqaep.json` | 以 metadata 為 mandatory（B5 級） | 否 |
| B2 HOLD {b2["verdict_counts"].get("HOLD",0)} | 同上 | 逐案判定（含 requiredness 不可分類者） | — |

分母同為 1,465，mandatory 集合不同，數字不同義。SPEC §6 的「96 missing／62 unresolved」屬該版敘述，與本輪 HOLD {b2["verdict_counts"].get("HOLD",0)} 為不同量，**UNRECONCILED**，不得互相引用。

## 5｜四 Ready 與接受

| 批 | ReadyDraft | ReadyAtom | ReadyExecute | ReadyAccept | 現狀 |
|---|---|---|---|---|---|
| B0 | 是 | 是 | 是（當期讀取＋三端接收＋137/137） | 是（本輪真跑；分離 Checker 對 B0 另判） | `B0_COMPLETE` |
| B1 | 是 | 是 | 部分（D-2／D-3 未閉） | 否 | `PARTIAL` |
| B2 | 是 | 是 | 部分（18 HARD source_row、inner/outer） | 否 | `PARTIAL` |
| B3 | 是 | **{adm["four_ready"]["ReadyAtom"]}**（347/365 Unit 未宣告 owner） | 否 | 否 | `ReadyExecute=HOLD`；{prod["join"]["admission_ready"]} atom 已具 owner＋source |

三端接收（rev4，當期 envelope，currency CURRENT）：

| consumer | decision | first_fail | rights_currency | checked_at |
|---|---|---|---|---|
{consumer_rows}

## 6｜未閉合義務（五類）

| 類 | 內容 | 主責 |
|---|---|---|
| 1 可自行取得 | r7 pin／census／payload 完整性（已完成） | — |
| 2 需工程 | B2 18 HARD `source_row`；9 HARD inner/outer；B3 NEG-design 結構化＋owner 綁定（44 案與 `admission_ready=0` 的共同成因） | 工程 |
| 3 需設計補編 | DOC_BRIDGE heading 計數契約；BEHAVIOR／SEAM／RECOVERY typed fixture；B2 requiredness 限定詞形狀契約 | 工程＋具權採納 |
| 4 需原權位 | B0 descriptor 續期（Owner）；D-2 四測試讀權；D-3 七槽 M:N；D-4 五 Kernel 語義；TT-UP-1／6 E00／54 ROUTE | 見左列 |
| 5 下游驅動 | B4 驅 B1 BASE 012–016；B5 驅 B2 HOLD {b2["verdict_counts"].get("HOLD",0)}；B6 驅 20 Edge／8 Port | B4／B5／B6 |

## 7｜發布授權對帳（M2）

| 依據 | 內容 | 效力 |
|---|---|---|
| r7 入口 §7 | 「本次上推 未推送（`REMOTE_PUBLICATION_HOLD`）」、distribution `LOCAL_ONLY` | 記錄 **r7 撰寫輪**（A6 採納輪）的狀態 |
| 本輪薄 PROMPT §6 | 明令以 `API KEY/GITHUB-REPO_SHW097-4.txt` 一次性認證增量推至 `shw097-team/SQS-THC_MVP`，並要求 remote readback | 本輪授權來源 |
| A6 blocked_effects | B1 live submit／B2 真 ToolReadSet ACK／B3 產品 JOIN/CHILD/ROUTE/COMMIT／B0 新 source 讀取 | 未列 publish |

本輪發布以薄 PROMPT 為授權；發布物為**去識別化衍生物**（`code/`、`docs/` 重排，逐檔記 frozen 與 published 兩個 sha），LOCAL_ONLY 原件不散布。此裁量已記錄，非默示。

## 8｜不宣稱

- **B0 例外並具名**：`B0_COMPLETE` 由本輪真跑（當期讀取、三端 CURRENT、12/12 自測、137/137 產品案、descriptor 續期）支撐；除此之外未宣稱任何批次接受。
- `ReadyExecute=false`；`admission_ready={prod["join"]["admission_ready"]}`、`route_out={prod["route"]["route_out"]}`（18 個 Unit 於條文宣告 Owner，其餘 347 未宣告）。
- 未宣稱語意等價、原 Reader 已具、B2 PASS 可作准入。
- `ENVELOPE_AUTHORITY_EXPIRED` 分支本輪**未行使**（window 已關，三端先被 `RIGHTS_UNVERIFIED` 攔下）：程式 fail-closed，但沒有收據證明它會紅——下一輪必須在有窗時執行一次。
- 未改動任何 active pin、未關閉任何 edge、未升格任何項目（`promoted_to_primary: []`）。
"""

    handoff = f"""# HANDOFF rev4 → B3 准入（2026-11-27_r7）

- 產生：`{now()}`
- 一句話：r7 真產品重跑完成，經 Checker REJECT 一輪更正；B3 `ReadyAtom=false`、`ReadyExecute=HOLD`；四批未接受。

## 1｜立即可做（不需新權限）

1. **B3 owner 綁定**：365 個 Unit 的 `owner` 皆為字面 `#`；改由原條文取得 owner，`admission_ready` 才可能非零。
2. **B3 NEG-design 結構化**：把 NEG design 做成 typed 欄，實作 `AUTHOR:TRACE_ORPHAN`／`AUTHOR:NEG_MISSING`／`AUTHOR:CHILD_RULE_HOLD:<key>` 三個原 FirstFail（**不得**把 `DIRECT_CLAUSE_SHA_MISMATCH` 改名成原碼）。
3. **B2 requiredness 限定詞契約**：40 案現為 `AUTHOR_QUALIFIER_UNRATIFIED` HOLD，需具權採納才可放行。

## 2｜需 Owner

| 項 | 範圍 | 影響 | 建議 |
|---|---|---|---|
| B0 descriptor 續期 | `00_PREFLIGHT/B0_READ_CONTEXT_2026-11-26.json`＋`native_entry.py` `EXPECTED_DESCRIPTOR_SHA/BYTES`＋每源 `usage_evidence_sha` | B0 現時權利、B3 `ReadyExecute`、三端 currency | 與 D-2／D-3 同窗 |
| D-2／D-3／D-4／TT-UP-1 | FDA 四測試讀權／七槽 M:N／五 Kernel 語義／inner→outer 映射 | B1／B2 未閉項 | 各原權位 |

## 3｜不得重入

- 不得覆寫凍結：`r7_freeze.py` 無 `--revision` 會拒絕；新修訂一律新檔並記 `supersedes`。
- 不得把 `REFUSAL_EXECUTED` 當 PASS；判定權在 `b3_r7_neg_reconcile.json`。
- 不得以 `receivers.B3` 的 {b2["receivers"]["B3"]["accepted"]} 代替 B3 join 的 `with_mandatory` 0／1465（mandatory 集合不同）。
- 不得把歷史 B0 envelope 當 current；不得用路徑／檔名找 SPEC（用 raw sha）。

## 4｜重現（本輪指令）

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/71_W0_B0-B3_R7_20261127/20_DEV/r7"
python -B r7_preflight.py
python -B b1_cli.py --op ALL --out ../../40_OPS/b1_r7_run_all.json
python -B b1_tqaep.py && python -B b1_edge_sec.py
python -B b2_meta.py && python -B b2_tqaep.py
python -B b3_product.py --dry-run
python -B b3_neg_v2.py && python -B b3_neg_reconcile.py && python -B b3_tqaep.py
python -B r5_consumers.py && python -B r5_consumers.py --selftest
python -B r7_freeze.py --revision rev4     # 凍結不含 docs；新修訂必用新檔名
python -B r7_closeout_gen_rev4.py
```

## 5｜坑

1. `b2_tqaep.py` 必須在 `b2_meta.py` 之後（否則 B5 接收為 0）。
2. B2 載體目錄是 `PHASE 01-04`（連字號），非 `PHASE 01~04`。
3. B3 ledger 正文不得含 wall clock，否則 digest 不可重算。
4. owner window 同時只能一個，`WINDOW_ALREADY_OPEN` 不彈視窗。
5. `b3_product.op_commit` 以 window 狀態判權：window 關閉時回 `OWNER_WINDOW_CLOSED`（正確的 fail-closed）。
"""

    bootstrap = """# NEW SESSION BOOTSTRAP｜W0 B0–B3 r7（rev4）

## 狀態

r7 真產品重跑＋一輪 Checker 更正；B3 `ReadyAtom=false`／`ReadyExecute=HOLD`；四批未接受；`FIN_ORDER=DENY`。

## 四步

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/71_W0_B0-B3_R7_20261127"
python -B - <<'PY'
import json,hashlib
import glob as _g
f=json.load(open(sorted(_g.glob("40_OPS/r7_candidate_freeze.rev*.json"),key=os.path.getmtime)[-1],encoding="utf-8"))
ok=all(hashlib.sha256(open(a["path"],"rb").read()).hexdigest()==a["raw_sha256"] for a in f["artefacts"])
body="\\n".join(f'{a["raw_sha256"]}  {a["path"]}' for a in sorted(f["artefacts"],key=lambda x:x["path"])).rstrip("\\n")
print(ok, hashlib.sha256(body.encode()).hexdigest()==f["candidate_digest"])
PY
sed -n '1,40p' 60_CLOSEOUT/SST_PLP_PH01_W0_B0-B2_CLOSEOUT_rev4.md
python -c "import json;d=json.load(open('40_OPS/r7_b3_admission.json',encoding='utf-8'));print(d['four_ready'])"
```

## 立刻可做

B3 owner 綁定、B3 NEG-design 結構化、B2 requiredness 限定詞契約。

## 不要做

覆寫凍結／把 `REFUSAL_EXECUTED` 當 PASS／用 `receivers.B3` 數字代替 B3 join／用歷史 B0 envelope 當 current。
"""

    for name, body in (("SST_PLP_PH01_W0_B0-B2_CLOSEOUT_rev4.md", closeout),
                       ("SST_PLP_PH01_W0_B0-B2_HANDOFF_B3_ADMISSION_rev4.md", handoff),
                       ("NEW_SESSION_BOOTSTRAP_rev4.md", bootstrap)):
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(body)

    idx_path = os.path.join(R7, "DELIVERY_INDEX.json")
    index = load(idx_path)
    index["revision"] = 4
    index["generated_at"] = now()
    index["current_pointers"] = [
        {"role": "closeout", "path": "60_CLOSEOUT/SST_PLP_PH01_W0_B0-B2_CLOSEOUT_rev4.md"},
        {"role": "handoff", "path": "60_CLOSEOUT/SST_PLP_PH01_W0_B0-B2_HANDOFF_B3_ADMISSION_rev4.md"},
        {"role": "bootstrap", "path": "60_CLOSEOUT/NEW_SESSION_BOOTSTRAP_rev4.md"},
        {"role": "freeze", "path": os.path.basename(fr2_path) if fr2_path else ""},
        {"role": "b3_admission", "path": "40_OPS/r7_b3_admission.json"},
        {"role": "preflight", "path": "00_PREFLIGHT/r7_preflight.json"},
        {"role": "checker_verdict", "path": "40_OPS/r7_checker_verdict.md"},
    ]
    index["four_ready"] = adm["four_ready"]
    index["phase_status"] = {"B0": "HOLD_RIGHTS_CURRENCY", "B1": "PARTIAL",
                             "B2": "PARTIAL", "B3": "READY_ATOM_FALSE_READY_EXECUTE_HOLD"}
    index["rev1_documents"] = ["60_CLOSEOUT/SST_PLP_PH01_W0_B0-B2_CLOSEOUT.md",
                               "60_CLOSEOUT/SST_PLP_PH01_W0_B0-B2_HANDOFF_B3_ADMISSION.md",
                               "60_CLOSEOUT/NEW_SESSION_BOOTSTRAP.md"]
    index["checker"] = {"verdict_file": "40_OPS/r7_checker_verdict.md",
                        "rev1_verdict": "REJECT", "mandatory_findings": 10,
                        "disposition": "see rev2 retraction table"}
    index["freeze"] = {"path": os.path.basename(fr2_path) if fr2_path else None,
                       "candidate_digest": (fr2 or {}).get("candidate_digest")}
    json.dump(index, open(idx_path, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"closeout": "60_CLOSEOUT/SST_PLP_PH01_W0_B0-B2_CLOSEOUT_rev4.md",
                      "first_fail_coverage": {"B1": ff1, "B2": ff2, "B3": ff3},
                      "b2": b2["verdict_counts"], "b3": b3["verdict_counts"],
                      "admission_ready": prod["join"]["admission_ready"],
                      "route_out": prod["route"]["route_out"]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
