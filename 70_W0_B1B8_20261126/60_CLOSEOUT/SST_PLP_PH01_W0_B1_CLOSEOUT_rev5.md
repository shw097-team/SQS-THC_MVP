# SST_PLP_PH01_W0_B1_CLOSEOUT_rev5

> 取代 `_rev4`。rev 5 依分離 Checker round 1（`40_OPS/b1_checker_round1_verdict.md`）的六項阻斷逐項修正，並**撤回 rev4 的「60/60 PASS」**——那是假綠：POS oracle 未比對 `expected_first_fail`、KERNEL 拒絕面是硬編碼常數。
- subject `SST/SQS-THC/PH01/E00`｜BID `1`｜`SOURCE_READ`｜`write_set=[]`｜`FIN_ORDER=DENY`
- 現行候選：`40_OPS/b1_run_20261126T123230.json`（`d9e00256…`）＋ `40_OPS/b1_tqaep_20261126T123248.json`（`4fc86fe3…`）
- **真結果：56 PASS / 4 FAIL / 0 HOLD**

## 1｜Checker 六項阻斷的處置

| # | Checker 阻斷 | 處置 | 現況 |
|---|---|---|---|
| 1 | `broker_live_submit` POS oracle 反向（POS 應得 `FIN_ORDER_DENY_ALWAYS`） | POS fixture 改為**真的送出提交意圖**（`submit=true`、無 token／connector），POS 期望值改為該碼；harness POS 分支開始比對 `expected_first_fail` | 已閉合 |
| 2 | 5×KERNEL NEG 的「單一 Writer」不變量空轉、拒絕面是常數 | 改為**逐 kernel marker 表**（`KERNEL_OWNER_ID`／`_EXPECTED_OWNER`／`OWNER_ID`（`(?<![A-Z_])` 界定）／`HARNESS_OWNER_ID`／`_LIFECYCLE_OWNER_ID`）驅動同一 `scan()`；拒絕面是**同一 scanner** 掃到注入的第二宣告模組 | 已閉合（5/5 以真掃描取得） |
| 3 | `B1.U0012` 宣稱 OBSERVED 卻無 declared-path locator；U0017/U0018 靜默改路徑 | 新增 `_finalise()`：只有 **declared-path 精確**（含 carrier 前綴映射、glob 前綴）才 `EXACT`；basename-only 一律 `PARTIAL_BASENAME_ONLY_NOT_ACCEPTED`＋`first_fail=BASE_ROW_MISSING` | 已閉合（拒絕過度宣稱） |
| 4 | untracked 單元無法產 `CommitPathSpan`；無 `missing` 集 | 每列輸出 `missing[]`；每目標輸出 `commit`（tracked 才有）＋`commit_reason`（無 commit 身分時明示）；`RepoReadSet.missing` 具名清單 | 已閉合 |
| 5 | 六個 locator 讀自 `FHS/…`（RepoRoot 之外）而無授權證據 | 每目標加 `read_domain`（`REPO_ROOT`／`EXTERNAL_CARRIER`）、`outside_repo_root`、`authority{root, allow_list_declared, note}`；外部 carrier 明示**需要自己的 per-source allow-list** | 已閉合（缺口顯性化） |
| 6 | 無分離 Checker；receipt 早於程式、無法由現行碼重現 | 全部重跑，receipt 時間戳晚於程式；round 1 判定已入庫；round 2 已派 | 部分閉合（待 round 2） |

## 2｜四支 FAIL 的性質（不是修不好，是路徑真的不同）

| unit | declared path | 實體位置 | 判定 |
|---|---|---|---|
| `BASE-009` | `src/backfill_daily.py`、`check_daily.py` | `data_plane/src/backfill_daily.py`、`data_plane/src/check_daily.py` | 路徑漂移 |
| `BASE-012` | `FABRIC/fabric-desktop-automation/TEAM.md` | carrier `TEAM.md`（5,768 B）；repo 根另有**不同內容** `TEAM.md`（741 B） | 路徑＋內容雙重分歧 |
| `BASE-017` | `FDA_INTEROP_DISPOSITION.yaml`（根） | carrier `governance/FDA_INTEROP_DISPOSITION.yaml` | 路徑漂移 |
| `BASE-018` | `tests/test_fda_*` | carrier 下無此前綴的測試檔 | 未定位 |

`RepoReadSet.missing` 共 5 項：`TEAM.md`、`FDA_INTEROP_DISPOSITION.yaml`、`check_daily.py`、`src/backfill_daily.py`、`tests/test_fda_*`。

**這是 SPEC 側的宣告路徑與實體不符**，不是功能不存在（依「找不到 ≠ 功能不存在」）。解除方式二選一：由 SPEC Owner 更正 declared path，或由 B1 receive context 顯式宣告 carrier 前綴映射。

## 3｜FDA：維持 rev4 的裁決

`IDENTICAL_MODULO_EOL`（15/15 raw 不同、15/15 `content_sha256_lf` 相同、25 檔內容差集 0），primary = `FABRIC/`（LF）、mirror = `Fabric-rebind-publish/`（CRLF）。兩份 raw SHA256／bytes／receipt 全保留；`content_sha256_lf` **只作等價比對**，不取代 source pin／raw pin／簽署／原資格綁定。七 Slot 對五 action class 維持 M:N。

FDA 七槽 POS/NEG 現況（每槽 POS／NEG 皆比對期望碼）：

| slot | POS 期望 | POS 實得 | NEG arms |
|---|---|---|---|
| `watch_ui` | `None` | `None` | `valid_until` → `FDA_WINDOW_HOLD` |
| `radar_signal` | `None` | `None` | `signal_known_at` → `SIGNAL_TIME_HOLD` |
| `xs_compile` | `None` | `None` | `script_sha` → `COMPILE_RAW_MISSING` |
| `xs_backtest` | `None` | `None` | `pit_status`／`rights_epoch` → `BACKTEST_SCOPE_HOLD` |
| `at_simulated_order` | `None` | `None` | `fill_type` → `SIM_BROKER_TYPE_DENY` |
| `broker_external_event_read` | `None` | `None` | `origin`／`broker_seq`／`broker_receipt_ref`／`book_of_record_version` → `BROKER_FACT_MISSING` |
| `broker_live_submit` | `FIN_ORDER_DENY_ALWAYS` | `FIN_ORDER_DENY_ALWAYS` | `submit` → `FIN_ORDER_DENY_ALWAYS` |

claim ceiling 仍是 `STATIC_TYPED_CONTRACT_ONLY`。

## 4｜狀態

| 狀態 | 判定 |
|---|---|
| `B1_SPEC_READY` | 成立 |
| `B1_ENGINEERING_CANDIDATE` | 成立 |
| `B1_PRODUCT_EXECUTED` | 成立 |
| `B1_TQAEP_EXECUTED` | 成立（56 PASS／4 FAIL，皆具名） |
| `B1_ACCEPTED` | **不成立**（4 支路徑漂移 + round 2 待判） |
| `B1_INPUT_READY` | 成立 |

## 5｜HOLD

| # | 項 | 責任 | Resume |
|---|---|---|---|
| H-B1-01 | 已解除（EOL-only） | — | — |
| H-B1-09 | 四支 BASE declared-path 漂移（009/012/017/018） | **SPEC Owner**（更正路徑）或 B1 context 宣告 carrier 前綴映射 | 更正後重跑受影 4 案 |
| H-B1-02/03 | profile／manifest 未進 HEAD | Repo Owner | 提交或裁定 |
| H-B1-04 | 分離 Checker round 2 | 分離 session | 對 `d9e00256`／`4fc86fe3` 判定 |
| H-B1-05 | 無 remote | Repo Owner | 指定受權 remote |
| H-B1-06 | 20 edge UNKNOWN | 原 OPS/Repo/Host Owner | 受權 probe |
| H-B1-07 | Kernel 10 細規未核（語義） | 原 Domain Owner | 核定細規 |
| H-B1-08 | 七槽 runtime qualification（後波） | FDA Owner | 受權 runtime |

## 6｜Checker round 1 的留存

`40_OPS/b1_checker_round1_verdict.md`（8,028 B）為 round 1 原文，逐項：T1 PASS、T2 PASS、T3 FAIL、T4 FAIL、T5 FAIL、T6 PASS（附 caveat）、B1_ACCEPTED = NO。此判定不被 rev4 的任何自述覆蓋。
