# SST_PLP_PH01_W0_B0–B2 HANDOFF → B3 准入（2026-11-27_r7）

- 產生：`2026-11-27T15:45:02+0800`（由收據生成）
- 一句話狀態：以 r7 活動 SPEC 重跑 B1／B2／B3 真產品，B1 32 PASS＋18 HOLD、B2 2854 PASS＋76 HOLD、B3 688 SOURCE_BOUND＋64 HOLD；**B3 `ReadyExecute=HOLD`**，唯一硬阻塞是 B0 descriptor 續期與 B3 原 Reader；四批皆未接受。

## 1｜立即可做（不需新權限）

1. **B2 18 HARD `source_row`**：由 B5 真使用場景驅動，不得補造列號。
2. **B3 NEG 結構化**：把 `NEG design` 做成 typed 欄（現只存在於條文文字），再以 `AUTHOR:TRACE_ORPHAN`／`AUTHOR:NEG_MISSING`／`AUTHOR:CHILD_RULE_HOLD:<key>` 三個原 FirstFail 重跑 44 案；`SUBSTANTIVE_GAP`（11 PROTECTED）只需把 `DIRECT_CLAUSE_SHA_MISMATCH` 映到原碼。
3. **DOC_BRIDGE heading 契約**：`^#{1,6} ` 已採納，10 案仍不符，需內容版本確認。

## 2｜需 Owner 的（不要代簽）

| 項 | 精確範圍 | 決策 | 影響 | 建議 |
|---|---|---|---|---|
| B0 descriptor 續期 | `00_PREFLIGHT/B0_READ_CONTEXT_2026-11-26.json` ＋ `native_entry.py` 常數 `EXPECTED_DESCRIPTOR_SHA/BYTES` ＋ 每源 `usage_evidence_sha` | 以 task `SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH`、ceiling `READ_ONLY_PROBE` 開窗並重簽 descriptor | 解 B0/B3 `ReadyExecute`／三端 currency | 與 D-2/D-3 同一窗處理，一次授權 |
| D-2 | FDA `tests/test_fda_{lease,router,router_integration,security}.py` | 精確讀權 | B1 FDA 七槽 | 納入 16 檔 allow-list |
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
