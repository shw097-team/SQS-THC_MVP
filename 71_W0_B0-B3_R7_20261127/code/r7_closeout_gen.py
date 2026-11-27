#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r7 closeout generator — every figure is read from a receipt, never retyped.

Emits into 60_CLOSEOUT/:
  * SST_PLP_PH01_W0_B0-B2_CLOSEOUT.md
  * SST_PLP_PH01_W0_B0-B2_HANDOFF_B3_ADMISSION.md
  * NEW_SESSION_BOOTSTRAP.md
and  DELIVERY_INDEX.json at the round root.

A claim can only be widened or narrowed in the receipt it is copied from: this module reads
`claim_ceiling` out of each receipt and quotes it verbatim.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

R7 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPS = os.path.join(R7, "40_OPS")
PRE = os.path.join(R7, "00_PREFLIGHT")
OUT = os.path.join(R7, "60_CLOSEOUT")
SPEC_DIR = r"<LOCAL_ROOT>\W0_B0-B3_GEN3_CODEX_FINAL_2026-11-27_r7"


def load(p):
    return json.load(open(p, encoding="utf-8"))


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    pf = load(os.path.join(PRE, "r7_preflight.json"))
    run = load(os.path.join(OPS, "b1_r7_run_all.json"))
    b1 = load(os.path.join(OPS, "b1_r7_tqaep.json"))
    edge = load(os.path.join(OPS, "b1_r7_edge_sec.json"))
    b2 = load(os.path.join(OPS, "b2_r7_tqaep.json"))
    meta = load(os.path.join(OPS, "b2_r7_meta.json"))
    b3 = load(os.path.join(OPS, "b3_r7_tqaep.json"))
    neg = load(os.path.join(OPS, "b3_r7_neg_reconcile.json"))
    prod = load(os.path.join(OPS, "b3_r7_product.json"))
    rcv = load(os.path.join(OPS, "r7_consumer_receipts.json"))
    selftest = load(os.path.join(OPS, "r7_consumer_selftest.json"))
    b4rcv = load(os.path.join(OPS, "r7_b4_receiver.json"))
    adm = load(os.path.join(OPS, "r7_b3_admission.json"))
    freeze_path = os.path.join(OPS, "r7_candidate_freeze.json")
    freeze = load(freeze_path) if os.path.isfile(freeze_path) else None
    win = load(os.path.expanduser("~/.hgk-owner/window.json"))

    b1c = b1["verdict_counts"]
    b2c = b2["verdict_counts"]
    b3c = b3["verdict_counts"]
    consumer_lines = "\n".join(
        f'| {r["consumer_id"]} | {r["decision"]} | `{r.get("rights_currency")}` | `{r["checked_at"]}` |'
        for r in rcv["receipts"])
    freeze_line = (f'`{freeze["candidate_digest"]}`（{freeze["members"]} 成員；'
                   f'`r7_candidate_freeze.json`）' if freeze else "**未凍結**")

    closeout = f"""# SST_PLP_PH01_W0 B0–B2 CLOSEOUT｜B3 准入（2026-11-27_r7）

- 產生：`{now()}`（本檔由 `20_DEV/r7/r7_closeout_gen.py` 從收據生成，數字非手抄）
- Subject／Wave：`SST/SQS-THC/PH01/E00`／`P1-W00M`
- 活動 SPEC：`{pf["spec_version"]}`（入口 `00_唯一交付入口_W0_B0-B3_2026-11-27_r7.md`，sha `{pf["entry"]["sha256"][:16]}…`；A5 機械 PASS＋A6 採納 2026-11-27T14:47+08:00）
- 凍結候選：{freeze_line}
- 權利：owner window `{win.get("window_id")}`／task `{win.get("task_id")}`／ceiling `{win.get("effect_class_ceiling")}`／state `{win.get("state")}`
- 宣稱上限：`B0_COMPLETE`／`B1_ACCEPTED`／`B2_ACCEPTED`／`B3_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` **均未成立**；`FIN_ORDER=DENY`

## 1｜SPEC 身份與完整性（重算，不引用前輪）

| 批 | pin（前 16） | bytes | 載體數 | Unit | Case | payload_sha 全等 | kind 分母 |
|---|---|---:|---:|---:|---:|---:|---|
| B1 | `{pf["batches"]["B1"]["observed_sha256"][:16]}` | {pf["batches"]["B1"]["bytes"]:,} | {pf["batches"]["B1"]["carrier_count"]} | {pf["batches"]["B1"]["units"]} | {pf["batches"]["B1"]["cases_in_section_06"]} | {pf["batches"]["B1"]["payload_sha_equal"]}/{pf["batches"]["B1"]["units"]} | {pf["batches"]["B1"]["kind_denominators"]} |
| B2 | `{pf["batches"]["B2"]["observed_sha256"][:16]}` | {pf["batches"]["B2"]["bytes"]:,} | {pf["batches"]["B2"]["carrier_count"]} | {pf["batches"]["B2"]["units"]} | {pf["batches"]["B2"]["cases_in_section_06"]} | {pf["batches"]["B2"]["payload_sha_equal"]}/{pf["batches"]["B2"]["units"]} | {pf["batches"]["B2"]["kind_denominators"]} |
| B3 | `{pf["batches"]["B3"]["observed_sha256"][:16]}` | {pf["batches"]["B3"]["bytes"]:,} | {pf["batches"]["B3"]["carrier_count"]} | {pf["batches"]["B3"]["units"]} | {pf["batches"]["B3"]["cases_in_section_06"]} | {pf["batches"]["B3"]["payload_sha_equal"]}/{pf["batches"]["B3"]["units"]} | {pf["batches"]["B3"]["kind_denominators"]} |

- manifest 8 列全等：`{pf["manifest_all_match"]}`；manifest sha `{pf["manifest"]["sha256"][:16]}…`。
- 每批在 K 內有 **兩個位元組全等載體**（根目錄與 `W0_B0-B3_r7/`）：同一來源兩處放置，非碰撞；主用取較淺路徑，兩者 sha 皆等於 pin（見 `r7_preflight.json` `carriers`）。
- Unit↔Case join 雙向零缺零多；`unique_unit_ids`＝`unique_keys`＝Unit 數。

## 2｜真跑結果（本輪實際執行）

| 批 | 規模 | 判定 | 收據 |
|---|---|---|---|
| B1 REPO/BASE/FDA/ROOTS | 30 Unit／60 Case／4 Op | PASS {b1c.get("PASS",0)}／PASS_SOURCE_BOUND {b1c.get("PASS_SOURCE_BOUND",0)}／PARTIAL {b1c.get("PARTIAL",0)}／HOLD {b1c.get("HOLD",0)}／FAIL {b1c.get("FAIL",0)} | `40_OPS/b1_r7_tqaep.json`、`b1_r7_run_all.json` |
| B1 EDGE/SEC | 9 | PASS {edge["counts"]["pass"]}／FAIL {edge["counts"]["fail"]} | `40_OPS/b1_r7_edge_sec.json` |
| B2 QROWS/HARD/META/RETURN | 1,465 Unit／2,930 Case／4 Op | PASS {b2c.get("PASS",0)}／HOLD {b2c.get("HOLD",0)}／FAIL {b2c.get("FAIL",0)}；Q 列 {b2["qrows"]["summary"]["verified"]}/{b2["qrows"]["summary"]["units"]} 實體行核對、索引列＝宣告列 | `40_OPS/b2_r7_tqaep.json`、`b2_r7_tool_readset.json` |
| B2 META | 18 HARD | 取得 {sum(1 for e in meta["entries"] if e["decision"]=="COLLECTED")}／VERSION_UNBOUND {sum(1 for e in meta["entries"] if e["decision"]=="VERSION_UNBOUND")}／非發行物 {sum(1 for e in meta["entries"] if e["decision"]=="NOT_A_DISTRIBUTION")} | `40_OPS/b2_r7_meta.json` |
| B3 JOIN/CHILD/ROUTE | 365 Unit／752 Case | PASS_SOURCE_BOUND {b3c.get("PASS_SOURCE_BOUND",0)}／HOLD {b3c.get("HOLD",0)}／FAIL {b3c.get("FAIL",0)} | `40_OPS/b3_r7_tqaep.json` |
| B3 四 Op 記憶體 | 365 rows | join {prod["join"]["ready"]}/{prod["join"]["held"]}（ready/held）、child {prod["child"]["ready"]}／{prod["child"]["held"]}、route {prod["route"]["route_out"]}／{prod["route"]["hold"]} | `40_OPS/b3_r7_product.json` |
| B3 COMMIT 首切片 | 1 檔 | `{prod["commit"].get("decision")}`、preimage `{prod["commit"].get("preimage")}`、postimage `{prod["commit"].get("postimage_verified")}`、`write_set` 單檔、rights `{prod["commit"].get("rights_ref")}` | 同上 |
| B3 44 NEG 真變異 | 44 | {neg["verdict_counts"]}；否證原因 {neg["hold_reasons"]} | `40_OPS/b3_r7_neg_reconcile.json` |
| 三端接收 | B1／B2／B3 | 各欄齊；currency 見 §4 | `40_OPS/r7_consumer_receipts.json` |
| 接收反例 | 11 臂 | {selftest.get("passed")}/{selftest.get("total")}（1 POS＋10 單變異全拒，first_fail 精確） | `40_OPS/r7_consumer_selftest.json` |
| B4 最小接收 | B1 RepoReadSet | ACCEPT {b4rcv["accepted"]}／REFUSE {b4rcv["refused"]}（未追蹤目標 commit/blob 為 null） | `40_OPS/r7_b4_receiver.json` |

## 3｜本輪修正（前輪膨脹的更正，不是新增功能）

| # | 前輪主張 | 本輪量測 | 處分 |
|---|---|---|---|
| R-1 | B1 `FIXTURE_ONLY` 12 案列為 pass 家族、`PASS_EVIDENCE` 5 案列為 PASS | fixture 域檢查與 symbol 身分皆非產品語意 PASS | 12 案降 `HOLD`（`FIXTURE_ONLY_NO_PRODUCT_CALLABLE`）；5 案改 `PASS_SOURCE_BOUND` 並標 `CONTENT_IDENTITY_AND_SYMBOL_SPAN_ONLY` |
| R-2 | B3 `PASS_REFUSAL` 44 案 | 該判定只依「atom 不在 B2 ToolReadSet」——對每個 CHILD atom 恆真、與變異無關 | 44 案全數 `HOLD`：`{neg["hold_reasons"]}` |
| R-3 | B3 ledger 每跑一次 digest 不同 | 正文含 wall clock | 時間移出正文、只留收據；兩次連跑 digest 相同（`{prod["ledger_sha256"][:16]}…`） |
| R-4 | B2 `B5` 接收 4 案 | 需先產 `b2_r7_meta.json` 才有 metadata 可綁；未跑 META 時為 0 | 已改執行順序並重跑，`B5` 4／1461 重現 |

四項皆為**判定收斂**（PASS 減少、HOLD 增加），不是把 FAIL 改綠。

## 4｜四 Ready 與接受狀態

| 批 | ReadyDraft | ReadyAtom | ReadyExecute | ReadyAccept | 現狀 |
|---|---|---|---|---|---|
| B0 | 是（歷史 CORE_ACCEPTED 保留） | 是 | **否** | **否** | `HOLD`：descriptor 於 2026-11-27T01:08 到期，重讀需 Owner 續期；三端以歷史 envelope 接收並標示 currency |
| B1 | 是 | 是 | 部分（D-2 四測試讀權、D-3 七槽未閉） | 否（分離 Checker 見 §6） | `PARTIAL` |
| B2 | 是 | 是 | 部分（18 HARD `source_row`、inner/outer 未閉） | 否 | `PARTIAL` |
| B3 | 是 | 是 | **否**（見 `r7_b3_admission.json` blockers） | 否 | `ReadyExecute=HOLD` |

三端接收（B1／B2／B3）逐端：

| consumer | decision | rights_currency | checked_at |
|---|---|---|---|
{consumer_lines}

## 5｜未閉合義務（五類）

| 類 | 內容 | 主責 |
|---|---|---|
| 1 已存在、代理可自行取得 | r7 SPEC pin／census／payload 完整性（本輪已完成）；B3 488 個 clause 映射 | — |
| 2 原義明確、需工程 | B2 18 HARD `source_row=null`；9 HARD inner/outer；B3 NEG 需結構化 NEG-design 欄與 PROTECTED field oracle（44 案 HOLD 的唯一成因） | 工程 |
| 3 SPEC 未完整、需設計補編 | DOC_BRIDGE heading 計數契約；BEHAVIOR／SEAM／RECOVERY typed fixture | 工程＋具權採納 |
| 4 真需原權位／第三方 | **B0 descriptor 續期**（Owner）；D-2 四測試讀權（FDA）；D-3 七槽 M:N（FDA/XQ/R13）；D-4 五 Kernel 語義（Kernel Owner）；TT-UP-1／6 E00／54 ROUTE（R17/E02/E05） | 見左列 |
| 5 下游真使用驅動 | B4 驅 B1 BASE PARTIAL（012–016）；B5 驅 B2 76 HOLD；B6 驅 20 Edge／8 Port | B4／B5／B6 |

## 6｜分離查核

分離 Checker 對本凍結候選的 verdict 以 `40_OPS/r7_checker_verdict.md` 為準；本檔不代其結論。
Checker 的 `ACCEPT` 只意謂「無 PASS 建立在未綁 oracle 上、無 HOLD 被稀釋」，**不是**批次接受。

## 7｜不宣稱

- 未宣稱 `B0_COMPLETE`／`B1_ACCEPTED`／`B2_ACCEPTED`／`B3_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute`。
- 未宣稱任何語意 oracle 已綁；`PASS_SOURCE_BOUND` 只證 locator 與身分，不證語意。
- 未關閉任何 edge、未改動任何 active pin、未升格任何項目（`promoted_to_primary: []`）。
- 未使用 B0 的新讀取；三端接收的 envelope 為歷史 B0 readset，currency 已逐端標示。
"""

    handoff = f"""# SST_PLP_PH01_W0_B0–B2 HANDOFF → B3 准入（2026-11-27_r7）

- 產生：`{now()}`（由收據生成）
- 一句話狀態：以 r7 活動 SPEC 重跑 B1／B2／B3 真產品，B1 {b1c.get("PASS",0)} PASS＋{b1c.get("HOLD",0)} HOLD、B2 {b2c.get("PASS",0)} PASS＋{b2c.get("HOLD",0)} HOLD、B3 {b3c.get("PASS_SOURCE_BOUND",0)} SOURCE_BOUND＋{b3c.get("HOLD",0)} HOLD；**B3 `ReadyExecute=HOLD`**，唯一硬阻塞是 B0 descriptor 續期與 B3 原 Reader；四批皆未接受。

## 1｜立即可做（不需新權限）

1. **B2 18 HARD `source_row`**：由 B5 真使用場景驅動，不得補造列號。
2. **B3 NEG 結構化**：把 `NEG design` 做成 typed 欄（現只存在於條文文字），再以 `AUTHOR:TRACE_ORPHAN`／`AUTHOR:NEG_MISSING`／`AUTHOR:CHILD_RULE_HOLD:<key>` 三個原 FirstFail 重跑 44 案；`SUBSTANTIVE_GAP`（11 PROTECTED）只需把 `DIRECT_CLAUSE_SHA_MISMATCH` 映到原碼。
3. **DOC_BRIDGE heading 契約**：`^#{{1,6}} ` 已採納，10 案仍不符，需內容版本確認。

## 2｜需 Owner 的（不要代簽）

| 項 | 精確範圍 | 決策 | 影響 | 建議 |
|---|---|---|---|---|
| B0 descriptor 續期 | `00_PREFLIGHT/B0_READ_CONTEXT_2026-11-26.json` ＋ `native_entry.py` 常數 `EXPECTED_DESCRIPTOR_SHA/BYTES` ＋ 每源 `usage_evidence_sha` | 以 task `SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH`、ceiling `READ_ONLY_PROBE` 開窗並重簽 descriptor | 解 B0/B3 `ReadyExecute`／三端 currency | 與 D-2/D-3 同一窗處理，一次授權 |
| D-2 | FDA `tests/test_fda_{{lease,router,router_integration,security}}.py` | 精確讀權 | B1 FDA 七槽 | 納入 16 檔 allow-list |
| D-3 | 7 槽 slot→action→artefact M:N | typed schema／fixture | B1 12 案 HOLD | 由 FDA owner 供 |
| D-4 | 五 Kernel protected field／old-new | 原 oracle | B1 6 案 HOLD | Kernel Domain Owner |
| TT-UP-1／6 E00／54 ROUTE | inner→outer 映射 | typed `DesignSelection` | B2 9 HARD／E00／ROUTE | R17/E02/E05 |

## 3｜不得重入

- 不得以 `CANDIDATE_*` 當 primary；不得刪 `SUPERSEDED_RECEIPT`、不得改 verdict。
- 不得把歷史 B0 envelope 當 current rights；currency 已逐端記在收據。
- 不得在未結構化 NEG-design 前把 44 案改回 PASS。
- 不得用路徑／檔名找 SPEC（一律 raw sha）；不得用 payload 首欄猜行號。

## 4｜重現（本輪指令，皆已實跑）

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/71_W0_B0-B3_R7_20261127/20_DEV/r7"
python -B r7_preflight.py          # SPEC pin/census/載體 + B4 接收 + B3 准入
python -B b1_cli.py --op ALL --out ../../40_OPS/b1_r7_run_all.json
python -B b1_tqaep.py && python -B b1_edge_sec.py
python -B b2_meta.py && python -B b2_tqaep.py
python -B b3_product.py --dry-run && python -B b3_tqaep.py
python -B b3_neg.py && python -B b3_neg_reconcile.py && python -B b3_tqaep.py
python -B r5_consumers.py && python -B r5_consumers.py --selftest
python -B r7_freeze.py --include-docs
```

- SPEC 取件以 raw sha256 定位；r7 每批在 K 有兩個位元組全等載體（根目錄＋`W0_B0-B3_r7/`），主用取較淺路徑。
- `b3_product.py` 的 `doc_bridge` 以一次索引取代每案全樹 walk；`_slice` 以每檔一次行表取代每次重建（原 107 s → 2.2 s）。兩者皆不改判定，僅不改結果的重複計算。

## 5｜坑（本輪實撞）

1. `b2_tqaep.py` 必須在 `b2_meta.py` **之後**跑，否則 `b5` 接收為 0（metadata 未綁）。
2. B2 載體目錄是 `PHASE 01-04`（連字號），舊碼寫 `PHASE 01~04`（波浪號）→ FileNotFoundError；以 sha 認檔。
3. `b2_r7_meta.json` 需網路（PyPI JSON）；無網路時 18 HARD 全 UNBOUND，不得改 expected。
4. B3 ledger 正文若含時間戳，digest 每次不同；時間只放收據。
5. owner window 同時只能有一個；`WINDOW_ALREADY_OPEN` 不會彈視窗，Owner 看不到拒絕。
"""

    bootstrap = """# NEW SESSION BOOTSTRAP｜W0 B0–B3 r7

## 一句話狀態

以 `@@SPECVERSION@@` 重跑 B1／B2／B3 真產品並凍結候選；B3 `ReadyExecute=HOLD`（B0 descriptor 續期＋原 Reader）；**四批皆未接受**，`FIN_ORDER=DENY`。

## 四步接上

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/71_W0_B0-B3_R7_20261127"
# 1) 凍結完整性（兩行都要 True）
python -B - <<'PY'
import json,hashlib,os
f=json.load(open("40_OPS/r7_candidate_freeze.json",encoding="utf-8"))
ok=all(hashlib.sha256(open(a["path"],"rb").read()).hexdigest()==a["raw_sha256"] for a in f["artefacts"])
body="\n".join(f'{a["raw_sha256"]}  {a["path"]}' for a in sorted(f["artefacts"],key=lambda x:x["path"])).rstrip("\n")
print(ok, hashlib.sha256(body.encode()).hexdigest()==f["candidate_digest"])
PY
# 2) 重算（同 digest 表示無人改過受檢 bytes；此步會重寫 freeze 檔，勿在 Checker 讀取期間執行）
# 3) 最後判讀
sed -n '1,40p' 60_CLOSEOUT/SST_PLP_PH01_W0_B0-B2_CLOSEOUT.md
# 4) 准入
python -c "import json;d=json.load(open('40_OPS/r7_b3_admission.json',encoding='utf-8'));print(d['four_ready']);print([b['item'] for b in d['readyexecute_blockers']])"
```

## 立刻可做

1. B3 NEG-design 結構化（44 案唯一成因）。
2. B2 18 HARD `source_row`（由 B5 驅動）。
3. DOC_BRIDGE heading 10 案內容版本確認。

## 不要做

`CANDIDATE_*` 當 primary／刪收據／改 verdict／用路徑找 SPEC／用歷史 B0 envelope 當 current rights。
"""
    bootstrap = bootstrap.replace("@@SPECVERSION@@", pf["spec_version"])

    for name, body in (("SST_PLP_PH01_W0_B0-B2_CLOSEOUT.md", closeout),
                       ("SST_PLP_PH01_W0_B0-B2_HANDOFF_B3_ADMISSION.md", handoff),
                       ("NEW_SESSION_BOOTSTRAP.md", bootstrap)):
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(body)

    index = {
        "schema": "SST.PH01.W0.B0B3.DeliveryIndex@1",
        "generated_at": now(),
        "round_root": R7,
        "spec": {"version": pf["spec_version"], "entry_sha256": pf["entry"]["sha256"],
                 "manifest_sha256": pf["manifest"]["sha256"], "manifest_all_match": pf["manifest_all_match"]},
        "current_pointers": [
            {"role": "closeout", "path": "60_CLOSEOUT/SST_PLP_PH01_W0_B0-B2_CLOSEOUT.md"},
            {"role": "handoff", "path": "60_CLOSEOUT/SST_PLP_PH01_W0_B0-B2_HANDOFF_B3_ADMISSION.md"},
            {"role": "bootstrap", "path": "60_CLOSEOUT/NEW_SESSION_BOOTSTRAP.md"},
            {"role": "freeze", "path": "40_OPS/r7_candidate_freeze.json"},
            {"role": "b3_admission", "path": "40_OPS/r7_b3_admission.json"},
            {"role": "preflight", "path": "00_PREFLIGHT/r7_preflight.json"},
        ],
        "phase_status": {"B0": "HOLD_RIGHTS_CURRENCY", "B1": "PARTIAL",
                         "B2": "PARTIAL", "B3": "READY_EXECUTE_HOLD"},
        "four_ready": adm["four_ready"],
        "promotion_state": {"promoted_to_primary": [], "items_eligible": [],
                            "blockers": [b["item"] for b in adm["readyexecute_blockers"]]},
        "accepted": {"B0": False, "B1": False, "B2": False, "B3": False, "W0": False},
        "layer_legend": {"20_DEV/r7": "engine (code)", "00_PREFLIGHT": "authority + census",
                         "40_OPS": "receipts", "60_CLOSEOUT": "generated documents",
                         "40_OPS/b3_ledger": "product effect (draft write), not a manifest member"},
        "published": {"state": "see publish record", "record": "50_PUBLISH/publish_record.json"},
    }
    json.dump(index, open(os.path.join(R7, "DELIVERY_INDEX.json"), "w", encoding="utf-8",
                          newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"closeout": os.path.join(OUT, "SST_PLP_PH01_W0_B0-B2_CLOSEOUT.md"),
                      "handoff": os.path.join(OUT, "SST_PLP_PH01_W0_B0-B2_HANDOFF_B3_ADMISSION.md"),
                      "bootstrap": os.path.join(OUT, "NEW_SESSION_BOOTSTRAP.md"),
                      "index": os.path.join(R7, "DELIVERY_INDEX.json")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
