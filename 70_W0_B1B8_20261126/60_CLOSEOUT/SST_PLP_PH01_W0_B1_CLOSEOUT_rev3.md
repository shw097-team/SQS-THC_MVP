# SST_PLP_PH01_W0_B1_CLOSEOUT_rev3

> 取代 `_rev2`（rev 1／rev 2 保留為 LastGood，不刪）。rev 3 新增：FDA 碰撞裁決（§2）、60 原 Case 實跑（§4）、EDGE／SEC（§5）。
- subject `SST/SQS-THC/PH01/E00`｜OriginalWave `P1-W00M`｜BID `1`｜effect `SOURCE_READ`｜`write_set=[]`｜`preimage=N/A`｜`FIN_ORDER=DENY`
- 2026-11-26（Asia/Taipei）｜Commander HERMES desktop｜敘述語言：繁中
- 授權窗口 `WIN-4e4b8cdc56c7`（`REPOSITORY_WRITE`、scope `sqs_thc_ph01_e00,w0_b1_b8_construction`、TTL 至 19:25:31、`max_ops=40`）；口令由 Owner 本人輸入，代理未接觸。

## 1｜規格身份

| 項 | 實測 |
|---|---|
| B1 正文 | 185,197 B；raw SHA256 `13294cada156a2c0beb485bb940a316dd540173273c90dc721570604ca4a3753`（＝啟動 PROMPT pin） |
| 16 件配對 | manifest `16/16` 相等；`W/docs` 副本 byte-identical |
| A5 round 6 | 全項通過、`other_diffs=0`、census 2165U／4447C／0 parse error；**限制：Checker 與 Commander 同模型**，僅 session 分離 |

## 2｜FDA 碰撞裁決：不是 build 分歧，是 EOL 差異

依 Owner 指示，以 `FABRIC/` 為優先研究候選、`Fabric-rebind-publish/` 為對照候選，執行最小必要差額鑑定。

| 檢項 | 結果 |
|---|---|
| 兩份 carrier 是否 git repo | 否（無 `.git`、無 tag／commit 可綁） |
| 15 件 artefact 存在性 | 兩份皆 **15/15** |
| 15 件 raw SHA256 | 兩份**全數不同** |
| 15 件 LF 正規化後 SHA256 | 兩份**全數相同** |
| 整目錄（25 檔）LF 正規化比對 | 檔名集合相同、**content-differing = 0** |
| 換行慣例 | `FABRIC/` = **LF**；`Fabric-rebind-publish/` = **CRLF** |
| 兩份 reorg receipt | `manifest_sha256` 皆 `d35bef595fb300f697c5133f8b02dfd22115b44ac028fda729a1f36f88fcb122`、`manifest_entries=52`、`checker_after=175/175 PASS` |
| matrix 版本沿革 | 兩份 header 相同：`subject_digest=FDA-MATRIX-20260813-LIVE-QUALIFICATION-V2`、`promoted_at=null`、`prior_matrix_digest=null`、`rollback_matrix_digest=null` → 無 promotion lineage 可據以分版本 |
| execution binding 識別 | 兩份 `binding_id/project_id/stage_id/gate_id/kanban_board_id` 相同 |
| asset registry | 兩份 `updated_at`／`upgrade_source` 相同 |

**裁決**：`authority_collision.verdict = IDENTICAL_MODULO_EOL`；`byte_level_differences=15`、**`content_level_differences=0`**。

依此，原 H-B1-01「需 Owner 指名 canonical build」**不成立**——無實質內容分歧，不需 Owner 裁決。依 SPEC「同尾碼異 namespace 禁 join」只在內容不同時成立；此處內容相同。

**工程選定**（可回溯、非按日期）：
- **primary research binding** = `FHS/Fabric/FABRIC/fabric-desktop-automation`（LF；與 repo EOL 慣例一致，且 Owner 指定為優先候選）。
- `Fabric-rebind-publish/FABRIC/fabric-desktop-automation` 記為 **CRLF mirror**，內容等價已證。
- 兩者的 **content pin**（15 件 `content_sha256_lf`）逐檔記錄於收據 `ops.B1.FDA.carrier_inventory`；B4／B6 應引用 content pin，不得以 raw SHA 差異誤判為版本衝突。
- 未混合兩份拼成 build；未修改任一原件。

### 2.1｜七 Slot ↔ 五 action class 實體映射

| SPEC slot | carrier 實體 | 判定 |
|---|---|---|
| `watch_ui` | `fda_router.py` + `xq_native_adapter.py`；`XQ_LAUNCH_LOCATE` | 實作詞彙不同，語義對應成立 |
| `radar_signal` | `fda_router.py` 路由規則；`XQ_LOG_EXPORT_READBACK` | 對應成立 |
| `xs_compile` | `XQ_PAPER_CONFIG` / `XS_COMPILE_PASS` / `XS_COMPILE_FAIL_READBACK` | 1:N |
| `xs_backtest` | `XS_COMPILE_PASS` + `fda_lease.py` fencing | 對應成立 |
| `at_simulated_order` | `XQ_PAPER_CONFIG` | 對應成立 |
| `broker_external_event_read` | `XQ_LOG_EXPORT_READBACK` | 對應成立 |
| `broker_live_submit` | **無對應 action class**；matrix 明載 `live_broker: DENY_ALWAYS` | `DENY_INVARIANT` 成立（設計使然） |

七個 SPEC slot 名在 carrier 原始碼出現 **0** 次 → 印證 SPEC §04.A 自述「五 action class ≠ 七 Slot、M:N」。此為作者分解與實作詞彙落差，**不是缺件**。

## 3｜R3（B0→B1／B2／B3）當前窗口真接收

| Consumer | 結果 | 收據 SHA256 |
|---|---|---|
| B1 | `ACCEPTED`（2 entries，`R=['read']`、`M=[]`） | `2549a6fb41909fa954cccad78aa38cd11df335854b6d673dcb7b7794f77b32a6` |
| B2 | `ACCEPTED`（同 tuple） | `c01e23ec0904a40eef252cf681909bdb8c54fae8afccdf9bbf020bff8ff8ff4d` |
| B3 | `ACCEPTED`（同 tuple） | `4a06fa8ffa22a77ecf32453a6b1a54f113bdfff180216896212a77b395eee1be` |

envelope `645c73891006f6dd…`（5,429 B）；`candidate_digest=f3fa76eaa1c083af…` 與 25 檔 freeze 獨立重算相符；三份未換 `consumer_id`。

## 4｜60 原 Case 實跑（TQAEP）

收據：`40_OPS/b1_tqaep_20261126T120202.json`，`cd4ca942482512058bc05dbac22cc9b7c300afb6ecbd9efc962164c6c74dfcce`（30,3xx B）。
Reader 收據：`40_OPS/b1_run_20261126T120202.json`，`33a9c3a7ca2265f43847f9a2189e83c5c0c51fedc378be8bd180218dfcde7b1b`。

| 判定 | 數 | 說明 |
|---|---|---|
| `PASS` | **49** | 30 POS（含 7 FDA POS）＋18 BASE NEG＋1 FDA NEG（`broker_live_submit` DENY invariant） |
| `HOLD_ORACLE_UNBOUND` | **11** | 5 KERNEL NEG＋6 FDA NEG（見 §4.2） |
| `FAIL` | **0** | — |

### 4.1｜NEG 的實作方式（不是重貼期望值）

- **BASE NEG（18 案）**：兩個子變異各自從合法 baseline 單改——
  (a) *DELETE*：抽掉全部 locator → 必須落 `TYPED_MISSING_ABSENT_IN_TREE_AND_DISK`；
  (b) *declared/remote → local qualified*：只用 HEAD tree 重解（移除磁碟面）→ untracked 單元**不得**被升級為任一 `TRACKED_*`。
  兩者皆為讀取面真實變更，非字串比對。
- **FDA NEG `broker_live_submit`**：靜態可證 → 矩陣 `DENY_ALWAYS` 且**無** live-submit action class → PASS。
- **KERNEL NEG（5 案）**：變異對象是受保護語義欄，作者 10 條 Kernel 細規未經原 Owner 核可 → `SEMANTIC_ORACLE_UNBOUND`，依 SPEC §06.0 規則 1 記 HOLD，不記 PASS。
- **FDA NEG（6 案）**：變異對象是 lease／window／liveness（如「錯窗／過期」「假即時」），B1 為靜態取證、無 runtime lease oracle → `FDA_LEASE_WINDOW_ORACLE_UNBOUND`。

### 4.2｜11 筆 HOLD 的精確內容

| Case | 缺的 oracle | 解除條件 |
|---|---|---|
| `B1.NEG.KERNEL_{fsdt,temporal,knowledge,harness,capability}`（5） | 五 Kernel 細規的原 Owner 語義 Oracle | 原 Owner 以同 source/scope 核定 10 條細規並提供可反證 predicate |
| `B1.NEG.FDA_{watch_ui,radar_signal,xs_compile,xs_backtest,at_simulated_order,broker_external_event_read}`（6） | FDA lease/window/liveness runtime oracle | 受權 runtime 取證（本批禁啟 GUI）或原 FDA Owner 提供 lease 狀態 oracle |

### 4.3｜BASE 23 unit 分母（不與 FDA 7 slot 重複計）

`OBSERVED_TRACKED_AT_HEAD` 11｜`OBSERVED_IN_WORKING_TREE_UNTRACKED` 5｜`PARTIAL_TRACKED_AND_OTHER` 1（BASE-009，無缺件）｜`OBSERVED_IN_FDA_CARRIER_CONTENT_IDENTICAL` 6 → **合計 23**；FDA 7 slot 另列於 §2.1。`ABSENT_IN_TREE_AND_DISK` = **0**。

## 5｜EDGE／SEC（本批實際承載者）

| ID | 判定 | 觀測 |
|---|---|---|
| `EDGE.B1.NO_PRODUCT_WRITE` | PASS | 前後 HEAD `9a70501a…` 相同、`sha256(status --porcelain)` 相同 |
| `SEC.B1.CALLER_SUPPLIED_SURFACE_REJECTED` | PASS | 空 tree＋空 disk 下兩個指標路徑皆不得回 `TRACKED_*` |
| `SEC.B1.PAYLOAD_PIN_TAMPER_DETECTED` | PASS | baseline pin 相符；改一欄後 pin 不相符（30 units 重算） |
| `EDGE.B1.CARRIER_EOL_VS_CONTENT_DISTINGUISHED` | PASS | byte diff 15／content diff 0，verdict 落 `IDENTICAL_MODULO_EOL` |

## 6｜狀態階梯（照 r4 分帳）

| 狀態 | 判定 | 依據 |
|---|---|---|
| `B1_SPEC_READY` | 成立 | pin 16/16、payload 30/30、clause 30/30 |
| `B1_ENGINEERING_CANDIDATE` | 成立 | reader v2＋case harness、四 Op 真跑、可重算 |
| `B1_PRODUCT_EXECUTED` | 成立 | 四 Op 真讀、無產品寫 |
| `B1_TQAEP_EXECUTED` | 成立（49/60，11 具名 HOLD） | §4 |
| `B1_ACCEPTED` | **不成立** | 缺分離 Checker 對同候選的獨立判定（§7） |
| `B1_READY_EXECUTE` | 不成立 | 同上 |
| `B1_INPUT_READY` | 成立 | R3 三端 ACCEPTED |

> 49 案 PASS 是 **Maker 自檢**。依 SPEC §06.5 與 Owner 對作者側證據的立場，Maker 不得自簽接受；`B1_ACCEPTED` 需分離 Checker 在**同候選**（`33a9c3a7…` ＋ `cd4ca942…`）重跑並獨立判定。

## 7｜殘餘 HOLD 與 Resume

| # | 項 | 受影 | 責任 | Resume |
|---|---|---|---|---|
| H-B1-01 | **已解除**（原「carrier 權威」）→ 記為 `IDENTICAL_MODULO_EOL`，改以 content pin 綁定 | — | — | — |
| H-B1-02 | `sqs-*` 三 profile 僅在工作樹、未進 HEAD | BASE-006 | Repo Owner | 提交目錄或裁定 untracked 可用 |
| H-B1-03 | `TWICT_RUNTIME_PACK_MANIFEST` 等未進 HEAD | BASE-007/008 | Repo Owner | 同上 |
| H-B1-04 | 分離 Checker 未跑 | `B1_ACCEPTED` | 工程＋分離 session | 對 `33a9c3a7…`／`cd4ca942…` 重跑 60 案 |
| H-B1-05 | repo 無 remote | 遠端欄位 | Repo Owner | 指定受權 remote |
| H-B1-06 | 20 edge 全 `UNKNOWN` | B1.ROOTS／B4／B6 | 原 OPS/Repo/Host Owner | 受權 probe |
| H-B1-07 | 5 KERNEL NEG 語義 Oracle 未綁 | 上列 5 案 | 原 Domain Owner | 核定細規 |
| H-B1-08 | 6 FDA NEG lease oracle 未綁 | 上列 6 案 | FDA Owner／受權 runtime | 提供 lease oracle 或 runtime 取證 |

## 8｜對下游的准入

- **B4 可消費**：23 BASE＋5 KERNEL 的 `RepoReadSet@2`、content pin、`UnknownPhysicalEdgeSet`（全 UNKNOWN）；FDA 以 content pin＋5 action class 詞彙作 fit-gap 起點。
- **B4 不得冒**：`B1_ACCEPTED`、五 Kernel 語義合格、任一 FHS Edge 已 OFF、FDA 七槽與 carrier 詞彙等價。
- **B2 不需等 B1**：requires 僅 `B0 SourceReadSet/2`，r6 已真接收。

## 9｜檔案與 SHA

| 檔 | SHA256 |
|---|---|
| `40_OPS/b1_run_20261126T120202.json` | `33a9c3a7ca2265f43847f9a2189e83c5c0c51fedc378be8bd180218dfcde7b1b` |
| `40_OPS/b1_tqaep_20261126T120202.json` | `cd4ca942482512058bc05dbac22cc9b7c300afb6ecbd9efc962164c6c74dfcce` |
| `20_DEV/b1_reader/b1_reader2.py` | reader v3（LF 正規化、carrier basename 索引、glob 三面解析） |
| `20_DEV/b1_reader/b1_cases.py` | 60 案 harness（POS/NEG 皆為面變更） |
| `00_PREFLIGHT/P0_precheck_2026-11-26.json` | `8256d52be84ed3ac1710ae7b24447463056b42db477922c7a65e358bf9b071f7` |
