# DELIVERY_INDEX｜SQS-THC_MVP

本索引只列**波次與其真實狀態**；狀態以各波 `CURRENT.json` 與分離判定原文為準，不以檔案存在代替。

| 子樹 | 主題 | 狀態 | 固定指針 |
|---|---|---|---|
| `60_B1/` | 早期 B1 consumer（歷史接收器） | 歷史／LastGood | — |
| `70_W0_B1B8_20261126/` | B1–B8 首輪工程（r5） | 歷史；含 r5 分離 verdict（B1C-R5-F01～F03） | — |
| `71_W0_B0-B3_R7_20261127/` | B0–B3 r7 研究波 | 歷史；其 mechanical verdict 之候選曾遭就地改寫，**不得**作接受依據 | 研究錨 `b695d8d2…` |
| `72_W0_B0_R3_20261127/` | **B0 剩餘阻斷解阻與正式結案** | **`B0_COMPLETE`** | `CURRENT.json`；候選 `c1f852cd…`；`7f1665be…` |
| `73_W0_B1_20261128/` | **B1 基線核收與如實分帳** | `B1_NOT_ACCEPTED_PARTIAL`（29/60 可用、31 HOLD） | `CURRENT.json`；`ae323494…` |

## 讀取規則

1. 先讀該子樹 `CURRENT.json`：`status`、`status_basis`（判定原文路徑）、`active_chain`。
2. `90_ARCHIVE/superseded_revisions/` 內為被取代的修訂，**只作歷史**，不得作為活動指標。
3. `60_CLOSEOUT` 只保留 final：`SST_PLP_PH01_W0_B0_CLOSEOUT_HANDOFF_r34.md`＋`FREEZE_r34.json`／`FREEZE_MANIFEST_r34.tsv`＋`CANDIDATE_receiver_r34.*`。
4. 公開投影為去敏副本；本地原件的 sha 見各波 `REDACTION_NOTICE.md`，勿以公開 sha 冒充本地可信原件。
