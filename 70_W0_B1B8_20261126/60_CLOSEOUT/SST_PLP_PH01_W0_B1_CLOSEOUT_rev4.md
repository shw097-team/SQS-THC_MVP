# SST_PLP_PH01_W0_B1_CLOSEOUT_rev4

> 取代 `_rev3`（rev 1–3 全留 LastGood，不刪）。rev 4 依 Owner 2026-11-26 裁決，改寫三處：六 FDA NEG 逐槽真測（不再一律 lease HOLD）、五 KERNEL NEG 分帳、`content_sha256_lf` 不得取代原 raw pin。
- subject `SST/SQS-THC/PH01/E00`｜OriginalWave `P1-W00M`｜BID `1`｜`SOURCE_READ`｜`write_set=[]`｜`preimage=N/A`｜`FIN_ORDER=DENY`
- 窗口 `WIN-4e4b8cdc56c7`（`usable=true`，ceiling `REPOSITORY_WRITE`，`ops_used=0`）

## 0｜本輪相對 rev3 的變更

| rev3 | rev4 |
|---|---|
| 六 FDA NEG 一律 `FDA_LEASE_WINDOW_ORACLE_UNBOUND` → HOLD | **逐槽 typed 靜態檢測**，各回原 SPEC 首拒（§3.1）；僅 `broker_live_submit` 為 DENY invariant |
| 五 KERNEL NEG 一律 `SEMANTIC_ORACLE_UNBOUND` → HOLD | **`SECOND_WRITER` 不變量真檢**（§3.2）；作者 10 條細規未核另列為獨立 limitation，不再混為同一 HOLD |
| BASE 缺件只記 `TYPED_MISSING` | 行的 `first_fail` 改為 SPEC 原碼 **`BASE_ROW_MISSING`** |
| 以 `content_sha256_lf` 作 content pin | **原 raw SHA／bytes／receipt 全數保留**；`content_sha256_lf` 只用於等價比對，不取代 source pin、簽署或原資格綁定（§2） |

60 案結果：**PASS 60／FAIL 0／HOLD 0**（`40_OPS/b1_tqaep_20261126T121851.json`，`9b0e9bc7…`）。

## 1｜規格身份

B1 正文 185,197 B，raw SHA256 `13294cada156a2c0beb485bb940a316dd540173273c90dc721570604ca4a3753`（＝PROMPT pin）；16 件配對 `16/16` 相等。A5 round 6 全通過、`other_diffs=0`；**限制：Checker 與 Commander 同模型**，僅 session 分離。

## 2｜FDA carrier：工程 primary 選定，但身份雙軌保留

| 項 | carrier A `FHS/Fabric/FABRIC/fabric-desktop-automation` | carrier B `Fabric-rebind-publish/FABRIC/fabric-desktop-automation` |
|---|---|---|
| 角色 | **本波 Brownfield 重用與取證 primary** | mirror 對照 |
| 來源身份 | 路徑、15 件 raw SHA256、bytes、reorg receipt 全保留 | 同，全保留 |
| EOL | LF | CRLF |
| raw SHA256 | 15/15 與 B 不同 | 15/15 與 A 不同 |
| `content_sha256_lf` | 15/15 與 B **相同** | 同 |
| reorg receipt | `manifest_sha256=d35bef59…`、52 entries、checker 175/175 | 同值 |
| git 可綁 | 否（無 `.git`／無 tag） | 否 |

**身份規則（依 Owner 指示）**：
1. 兩份 carrier 各自的**原 raw SHA256／bytes／receipt 一律保留**，不因等價而合併或刪除任一。
2. `content_sha256_lf` **僅作內容等價比對**；它不是 source pin、不是 raw pin、不是簽署、也不是原資格綁定。
3. 下游（B4／B6）若要引用 carrier 實體，必須**同時**記 raw SHA256 與 `content_sha256_lf`，並註明所選 EOL 慣例。
4. 工程 primary 選定 **≠** canonical promotion ≠ `SourceFreezeRatified` ≠ 產品資格採納。
5. 七 FDA Slot 與五 action class 維持 **M:N**；已知映射不冒七槽 runtime qualification。

## 3｜60 案逐案結果

收據 `40_OPS/b1_tqaep_20261126T121851.json`（`9b0e9bc70f7f0e9c3438ba22558996d0ff4692c021c81b2d1d57e02bff36f770`）；
reader `40_OPS/b1_run_20261126T120202.json`（`33a9c3a7…`）。

### 3.1｜六 FDA NEG：逐槽 typed 靜態檢測（各回原首拒）

| slot | mutation（原 SPEC） | POS | NEG 實得首拒 | 判定 |
|---|---|---|---|---|
| `watch_ui` | 錯窗／過期 | None（窗內、window_id=lease_ref、未過期） | **`FDA_WINDOW_HOLD`** | PASS |
| `radar_signal` | 假即時 | None | **`SIGNAL_TIME_HOLD`** | PASS |
| `xs_compile` | 缺 compiler raw | None | **`COMPILE_RAW_MISSING`** | PASS |
| `xs_backtest` | lookahead／無權 | None | **`BACKTEST_SCOPE_HOLD`** | PASS |
| `at_simulated_order` | 模擬升真成交 | None（`SIM_FILL` 且無 broker 來源欄） | **`SIM_BROKER_TYPE_DENY`** | PASS |
| `broker_external_event_read` | GUI ACK 冒 Fill | None（broker_seq／receipt／BoR 齊） | **`BROKER_FACT_MISSING`** | PASS |
| `broker_live_submit` | submit／replace／cancel | None（無 allowed POS） | **`FIN_ORDER_DENY_ALWAYS`** | PASS |

實作：`20_DEV/b1_reader/b1_fda_static.py`。每槽一個 typed detector：POS fixture 必須回 `None`，單欄變異必須回**該槽自己的碼**；碼不符即 FAIL。
**claim ceiling：`STATIC_TYPED_CONTRACT_ONLY`** —— 證的是記錄級拒錯規則，不是七槽 runtime 資格。

### 3.2｜五 KERNEL NEG：`SECOND_WRITER` 不變量（與語義未核分帳）

| kernel | canonical writer module | kernel 內 shadow writer | NEG fixture 拒錯 | 判定 |
|---|---|---|---|---|
| `fsdt` | `src/kernel/fsdt/__init__.py` | 0 | `SECOND_WRITER` | PASS |
| `temporal` | `src/kernel/temporal/__init__.py` | 0 | `SECOND_WRITER` | PASS |
| `knowledge` | `src/kernel/knowledge/__init__.py` | 0 | `SECOND_WRITER` | PASS |
| `harness` | `src/kernel/harness/__init__.py` | 0 | `SECOND_WRITER` | PASS |
| `capability` | `src/kernel/capability/__init__.py` | 0 | `SECOND_WRITER` | PASS |

檢法：掃 `src/kernel/**/*.py` 中宣告 `KERNEL_OWNER_ID` 的模組，必須恰為該 kernel 的 `__init__.py`；再以自造 shadow-writer 宣告作單變異，斷言回 `SECOND_WRITER`。受保護欄位的突變則由 payload pin 守住（改一欄即 pin 不符）。

**獨立 limitation（不作為本案結論）**：`SEMANTIC_ORACLE_UNBOUND` —— 作者 10 條 Kernel 細規未經原 Owner 核可，故「語義是否正確」仍未被獨立 Oracle 證實。這是**另一項義務**，不把本案降級為 HOLD，也不因本案 PASS 而視為已閉合。

### 3.3｜18 BASE NEG：`BASE_ROW_MISSING`

兩子變異自合法 baseline 單改：
1. **DELETE**：抽掉全部 locator → 該 unit 落 `TYPED_MISSING_ABSENT_IN_TREE_AND_DISK`，**行的 first_fail = `BASE_ROW_MISSING`**（reader v4 已改，不再是自訂碼）。
2. **declared/remote → local qualified**：僅用 HEAD tree 重解、移除磁碟面 → untracked 單元**不得**升級為任何 `TRACKED_*`。

18/18 PASS。BASE 23 unit 分母：`TRACKED_AT_HEAD` 11｜`WORKING_TREE_UNTRACKED` 5｜`PARTIAL` 1｜`FDA_CARRIER_CONTENT_IDENTICAL` 6；`ABSENT_IN_TREE_AND_DISK` = **0**。

### 3.4｜EDGE／SEC

| ID | 判定 |
|---|---|
| `EDGE.B1.NO_PRODUCT_WRITE` | PASS（HEAD 與 `sha256(status --porcelain)` 前後相同） |
| `SEC.B1.CALLER_SUPPLIED_SURFACE_REJECTED` | PASS（空 tree＋空 disk 不得回 `TRACKED_*`） |
| `SEC.B1.PAYLOAD_PIN_TAMPER_DETECTED` | PASS（baseline 相符、改一欄不符） |
| `EDGE.B1.CARRIER_EOL_VS_CONTENT_DISTINGUISHED` | PASS（byte 15／content 0） |

## 4｜狀態階梯

| 狀態 | 判定 | 依據 |
|---|---|---|
| `B1_SPEC_READY` | 成立 | pin 16/16、payload 30/30、clause 30/30 |
| `B1_ENGINEERING_CANDIDATE` | 成立 | reader v4＋case harness＋static detectors |
| `B1_PRODUCT_EXECUTED` | 成立 | 四 Op 真讀、無產品寫 |
| `B1_TQAEP_EXECUTED` | 成立（60/60 PASS，Maker 自檢） | §3 |
| `B1_ACCEPTED` | **待分離 Checker 判定** | `40_OPS/b1_checker_round1_verdict.md` |
| `B1_INPUT_READY` | 成立 | R3 三端 ACCEPTED（本窗口） |

Maker 不得自簽接受：60/60 是 Maker 自檢；`B1_ACCEPTED` 需分離 session 對**同候選**（`33a9c3a7…`＋`9b0e9bc7…`）獨立判定。

## 5｜HOLD（精確、不再籠統）

| # | 項 | 受影 | 責任 | Resume |
|---|---|---|---|---|
| H-B1-01 | **已解除**（EOL-only 差異，非 build 分歧） | — | — | 保留雙軌身份即可 |
| H-B1-02 | `sqs-*` 三 profile 僅在工作樹、未進 HEAD | BASE-006 | Repo Owner | 提交或裁定 untracked 可用 |
| H-B1-03 | runtime pack／disposition manifest 未進 HEAD | BASE-007/008 | Repo Owner | 同上 |
| H-B1-04 | 分離 Checker 判定 | `B1_ACCEPTED` | 分離 session | 審 `b1_checker_round1_verdict.md` |
| H-B1-05 | repo 無 remote | 遠端欄位 | Repo Owner | 指定受權 remote |
| H-B1-06 | 20 edge 全 `UNKNOWN` | B1.ROOTS／B4／B6 | 原 OPS/Repo/Host Owner | 受權 probe |
| H-B1-07 | 五 Kernel 作者 10 細規未核 | **語義**（非本案） | 原 Domain Owner | 核定細規後另立 Case |
| H-B1-08 | 七槽 runtime qualification 未做 | **後波**（非本案） | FDA Owner／受權 runtime | 受權 runtime 取證 |

## 6｜檔案

| 檔 | SHA256 |
|---|---|
| `40_OPS/b1_run_20261126T120202.json` | `33a9c3a7ca2265f43847f9a2189e83c5c0c51fedc378be8bd180218dfcde7b1b` |
| `40_OPS/b1_tqaep_20261126T121851.json` | `9b0e9bc70f7f0e9c3438ba22558996d0ff4692c021c81b2d1d57e02bff36f770` |
| `20_DEV/b1_reader/b1_reader2.py` | reader v4（`BASE_ROW_MISSING`、LF 正規化、carrier basename 索引、glob 三面） |
| `20_DEV/b1_reader/b1_fda_static.py` | 七槽 typed detector＋POS/NEG fixtures |
| `20_DEV/b1_reader/b1_cases.py` | 60 案 harness |
| `40_OPS/b1_checker_round1_verdict.md` | 分離 Checker 判定（產出後填） |
