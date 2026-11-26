# SST_PLP_PH01_W0_B1_CLOSEOUT_rev7

> 取代 `_rev6`。rev 7 = T1 最小差額修補（NEG 真實性／BASE-009・017 locator binding／FDA allow-list）。
- 候選：`40_OPS/b1_run_20261126T125611.json`（`9303ce87…`）＋ `40_OPS/b1_tqaep_20261126T125645.json`（`22613ebc…`）
- **真結果：PASS 54／FAIL 1／HOLD_ORACLE_UNBOUND 5／HOLD_BASELINE_NOT_VALID 0**

## 1｜T1① NEG 真實性

| 項 | 修法 | 現況 |
|---|---|---|
| `first_fail=null` 假通過 | BASE NEG 一律記 `first_fail=BASE_ROW_MISSING`；KERNEL NEG 記 `SEMANTIC_ORACLE_UNBOUND` | 已除 |
| `PARTIAL` 的 `narrowed_ok=true` 強制分支 | 改為 **baseline 有效性閘**：`missing` 非空即 `HOLD_BASELINE_NOT_VALID`，不算 PASS | 已除 |
| mutation (b) 對已 tracked 單元無法區辨 | 改為逐目標只檢查「baseline 非 TRACKED → 不得升級為 TRACKED」，並記 `applicable=false` 及原因 | 已修 |
| KERNEL NEG 冒語義驗收 | verdict 改 `HOLD_ORACLE_UNBOUND`；`declared_mutation_executed=false`、`semantic_acceptance=NOT_CLAIMED`；second-writer 掃描降為**補充靜態證據** | 已改 |

## 2｜T1② BASE-009／017 路徑差額（已閉合）

建立 `00_PREFLIGHT/b1_locator_bindings.json`（2,502 B，`a8025e2f…`），3 筆受界 binding，每筆以**完整路徑＋實測 raw SHA** 為身分，執行時重新驗 SHA：

| unit | declared | resolved | raw SHA256 |
|---|---|---|---|
| BASE-009 | `src/backfill_daily.py` | `…\SQS-THC\data_plane\src\backfill_daily.py` | `fc10f802…` |
| BASE-009 | `check_daily.py` | `…\SQS-THC\data_plane\src\check_daily.py` | `06b25b72…` |
| BASE-017 | `FDA_INTEROP_DISPOSITION.yaml` | `…\FABRIC\fabric-desktop-automation\governance\FDA_INTEROP_DISPOSITION.yaml` | `9fac4d25…` |

`ratification = CANDIDATE_NOT_RATIFIED`（只閉合 locator，不改 SPEC 路徑、不動原工程）。
結果：`RepoReadSet.missing = []`；BASE 分佈 11 tracked／4 untracked／**8** carrier-content-identical。
**未**用 basename 全域搜尋、**未**靜默替換原 pin。

## 3｜T1③ FDA 來源授權

`00_PREFLIGHT/b1_source_allowlist.json`（3,105 B，`de92bd2c…`）：`source_id=SST.FDA.PRIMARY_CARRIER`、16 個 artefact 逐檔 raw SHA、用途限 W0 B1 靜態取證、`effect=SOURCE_READ`、`write_set=[]`、範圍上限明列「除這 16 路徑外 FHS/ 其餘不在 scope」。primary carrier 的 `allow_list_declared=true`；mirror 仍 false（僅作對照）。兩份 carrier 各自 raw SHA 保留，LF 正規化 hash 只作等價證據。`CARRIER_LEVEL_ONLY`／`slot_mapping=unproven` 照保。

## 4｜唯一未閉合的 FAIL

`B1.NEG.BASE-009`：`delete_ff` 已得 `BASE_ROW_MISSING`，但 mutation (b) 仍偵測到某個 baseline 非 TRACKED 的目標在 HEAD-only 面變成 TRACKED。該單元同時含 tracked glob 與 elsewhere 目標，屬**混合面**，需要專門 fixture 才能構造乾淨的單變異。**不強行轉 PASS**，交 round 3 裁決是 fixture 缺陷或真行為問題。

## 5｜狀態

`B1_TQAEP_EXECUTED` 成立（54／1／5，全部具名）；`B1_ACCEPTED` **不成立**（1 FAIL ＋ 5 HOLD ＋ round 3 未判）。

## 6｜HOLD

| # | 項 | 責任 | Resume |
|---|---|---|---|
| H-B1-09 | **已閉合**（binding） | — | — |
| H-B1-10 | KERNEL NEG 需原 Domain Owner 語義 Oracle 才能執行 §06 宣告突變 | 原 Domain Owner | 核定 Oracle |
| H-B1-11 | mirror carrier 未納 allow-list（僅對照用途，刻意） | Owner | 若需 mirror 取證再擴 |
| H-B1-12 | BASE-009 NEG 混合面 pending | 工程／round 3 | 專用 fixture |
| H-B1-13 | 七槽 slot 級來源未證 | FDA Owner | slot→artefact 映射 |
