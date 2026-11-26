# SST_PLP_PH01_W0_B1_CLOSEOUT_rev6

> 取代 `_rev5`。rev 6 依分離 Checker **round 2**（`40_OPS/b1_checker_round2_verdict.md`）逐項修正，並**更正 rev5 的一項事實錯誤**（§1）。
- 現行候選：`40_OPS/b1_run_20261126T124525.json`（`ab99941f…`）＋ `40_OPS/b1_tqaep_20261126T124526.json`（`2f216a06…`）
- **真結果：58 PASS / 2 FAIL / 0 HOLD**

## 1｜rev5 事實錯誤更正

| rev5 說 | 實況（round 2 實測） | 處置 |
|---|---|---|
| 「carrier 下無 `tests/test_fda_*` 前綴的測試檔」→ BASE-018 判為 SPEC 漂移 | **錯**。兩份 carrier 各有 4 檔：`tests/test_fda_lease.py`（4,015／4,105 B）、`test_fda_router.py`（4,028／4,119 B）、`test_fda_router_integration.py`（4,001／4,091 B）、`test_fda_security.py`（7,512／7,675 B）。收據自己的 `carrier_hits` 已列出 | 更正；reader 補 carrier glob 精確匹配 → BASE-018 現為 `OBSERVED_IN_FDA_CARRIER_CONTENT_IDENTICAL` |
| 「四支 FAIL 全部是 SPEC 路徑漂移」 | **錯**。round 2 判定：BASE-009／017 = `GENUINE_DRIFT`；BASE-012／018 = `RESOLVER_DEFECT` | 更正；兩支 reader 缺陷已修 |

## 2｜round 2 九項的處置

| # | round 2 判定 | 處置 | 現況 |
|---|---|---|---|
| 1 | `broker_live_submit` POS 未接 `run_slot`、NEG 變異為 no-op（PARTIAL） | FDA POS 分支改為實際呼叫 `FDAS.run_slot(slot)`，比對 `pos_first_fail == pos_expected`，並把 `first_fail` 記為該碼；NEG 變異由 `submit=true`（與 POS 相同）改為 `token=SUBMIT_TOKEN_PRESENT`（真變異） | 已閉合 |
| 2 | KERNEL NEG：marker 正確、scanner 共用、拒絕非常數，但 fixture 非 §06 的「改一個受保護欄位」，且 PASS 列 `first_fail=null`（PARTIAL） | 未實作 §06 宣告的語義突變（需原 Domain Owner 核定的 Oracle）；此項**未閉合**，見 §4 H-B1-10 | **未閉合** |
| 3 | U0012／U0017／U0018 精確性（PARTIAL） | 3 個真缺陷已修：carrier 升級不再只限 `ABSENT_IN_TREE_AND_DISK`（U0012 會查 carrier）；carrier glob 精確匹配（U0018）；`AGENTS.md`／`README.md` 不再誤判為 repo-root EXACT | 已閉合 |
| 4 | 9 筆 untracked 解析偽造 `commit=HEAD`（NO） | `commit` 只在 **repo-tree 精確**時給；其餘 `null` ＋ `commit_reason`（disk-only 無 commit 身分） | 已閉合（現行收據 `fabricated_commit_rows = []`） |
| 5 | 外部 carrier 無授權 allow-list；5 列 `read_domain=NONE` 與 `authority.note` 矛盾（PARTIAL） | note 只在 `EXTERNAL_CARRIER` 時聲稱越界，`NONE` 改為「no locator resolved」；allow-list 仍缺（**需 Owner／SPEC 宣告**，見 §4 H-B1-11） | 矛盾已修；allow-list **未閉合** |
| 6 | 收據可由現行碼重現 | 是（round 2 判 YES） | 已閉合 |
| 7 | rev5 關於 `tests/test_fda_*` 的陳述為假 | 見 §1 | 已更正 |
| 8 | 七個 FDA POS 僅靠共用 15-artefact 清單，`slot_reference_counts` 全為 0，無逐槽 M:N 映射 | FDA POS 收據新增 `claim_ceiling=CARRIER_LEVEL_ONLY` 與 `slot_mapping=unproven: slot_reference_counts=0 for all 7 slots`，不冒槽級資格 | 已顯性化（未取得槽級來源） |
| 9 | BASE-009/012/017/018 的 NEG 空轉（`narrowed_ok` 對 `PARTIAL` 列被強制為 true）；BASE/KERNEL NEG 列 `first_fail=null` | 認可此缺陷；未及修正（本輪額度用於 #1/#3/#4/#5）。列為受影 HOLD | **未閉合** |

## 3｜現行 BASE 分佈與缺失

`OBSERVED_TRACKED_AT_HEAD` 11｜`OBSERVED_IN_WORKING_TREE_UNTRACKED` 4｜`OBSERVED_IN_FDA_CARRIER_CONTENT_IDENTICAL` 6｜`PARTIAL_BASENAME_ONLY_NOT_ACCEPTED` 2

`RepoReadSet.missing` = **3 項，全部經 round 2 判為真漂移**：
1. `src/backfill_daily.py` → 實體 `data_plane/src/backfill_daily.py`（24,609 B）
2. `check_daily.py` → 實體 `data_plane/src/check_daily.py`（11,197 B）
3. `FDA_INTEROP_DISPOSITION.yaml` → 實體 `carrier/governance/FDA_INTEROP_DISPOSITION.yaml`（3,487／3,546 B）

對應 2 支 FAIL：`B1.POS.BASE-009`、`B1.POS.BASE-017`。這是 **SPEC 側宣告路徑漏寫 `data_plane/`／`governance/`**，不是功能不存在；解除需 SPEC Owner 更正路徑或顯式接受 unbound。

## 4｜HOLD

| # | 項 | 責任 | Resume |
|---|---|---|---|
| H-B1-01 | 已解除（EOL-only） | — | — |
| H-B1-09 | BASE-009／017 宣告路徑漂移（3 目標） | **SPEC Owner** | 更正路徑後重跑受影 2 案 |
| H-B1-10 | KERNEL NEG 未實作 §06 「改一個受保護欄位」；現行僅為 second-writer 靜態不變量 | 原 Domain Owner（核定語義 Oracle） | 取得 Oracle 後改為真語義突變 |
| H-B1-11 | `FHS/Fabric` 兩份 carrier 缺 per-source allow-list | **Owner** | 在 B1 receive context 宣告 carrier 允讀範圍，否則不得由 carrier 宣 OBSERVED |
| H-B1-12 | BASE／KERNEL NEG 列 `first_fail=null`；`PARTIAL` 列的 NEG 空轉 | 工程 | 下一輪修：NEG 記拒絕碼、baseline 無效即 HOLD |
| H-B1-13 | 七槽 slot 級來源未證（`slot_reference_counts=0`） | FDA Owner | 提供 slot→artefact 映射 |
| H-B1-02/03 | profile／manifest 未進 HEAD | Repo Owner | 提交或裁定 |
| H-B1-04 | 分離 Checker round 3 | 分離 session | 對 `ab99941f`／`2f216a06` 判定 |
| H-B1-05 | 無 remote | Repo Owner | 指定受權 remote |
| H-B1-06 | 20 edge UNKNOWN | 原 OPS/Repo/Host Owner | 受權 probe |

## 5｜狀態

| 狀態 | 判定 |
|---|---|
| `B1_SPEC_READY` / `B1_ENGINEERING_CANDIDATE` / `B1_PRODUCT_EXECUTED` | 成立 |
| `B1_TQAEP_EXECUTED` | 成立（58 PASS／2 FAIL，FAIL 為真漂移） |
| `B1_ACCEPTED` | **不成立**（H-B1-09／10／11／12 未閉合） |
| `B1_INPUT_READY` | 成立 |

## 6｜來源

- round 1 原文：`40_OPS/b1_checker_round1_verdict.md`（8,028 B，B1_ACCEPTED = NO）
- round 2 原文：`40_OPS/b1_checker_round2_verdict.md`（10,257 B，B1_ACCEPTED = NO；四支裁決 2 GENUINE_DRIFT／2 RESOLVER_DEFECT）
- 兩輪判定均不被 Maker 任何自述覆蓋。rev4 的「60/60」與 rev5 的「四支皆漂移」皆已撤回。
