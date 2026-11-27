# SST_PLP_PH01_W0 B0–B2 CLOSEOUT rev2｜B3 准入（2026-11-27_r7）

- 產生：`2026-11-27T16:07:30+0800`；由 `20_DEV/r7/r7_closeout_gen_rev2.py` 從收據生成
- Subject／Wave：`SST/SQS-THC/PH01/E00`／`P1-W00M`；活動 SPEC `2026-11-27_r7_Native-first_CODEX_FINAL`
- 凍結：`65ef7a75107d0bb57401194e37bb8dd2b989efbee173d10d76f78b6ed4e1f7df`（`r7_candidate_freeze.<rev>.json`，45 成員，supersedes `45d41c592ef3e89b…`）
- 權利：window `WIN-3657818f0331`／`CLOSED`／ceiling `HOST_OPERATIONS`／ops_used `0`
- 宣稱上限：`B0_COMPLETE`／`B1_ACCEPTED`／`B2_ACCEPTED`／`B3_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` **均未成立**；`FIN_ORDER=DENY`

## 0｜撤回表（rev1 主張 → 實測 → rev2 處分）

rev1 經分離 Checker 判 **REJECT（10 條 mandatory）**。逐條更正，凡收據無法支撐的敘述一律撤回。

| # | rev1 主張 | 實測 | rev2 處分 |
|---|---|---|---|
| M1 | 凍結候選不可變 | `r7_freeze.py` 以 `w` 就地覆寫；Checker 讀取期間 digest 由 `68162489…` 變 `45d41c59…`，腳本亦在查核中被改 | 凍結改**寫一次**：無 `--revision` 時拒絕覆寫，新修訂為新檔並記 `supersedes`。6816 版僅存於公開 commit `64747d6`，本檔不假造「已還原」 |
| M2 | 未處理與 SPEC §7 `REMOTE_PUBLICATION_HOLD` 的衝突 | r7 入口 §7 為**撰寫輪**狀態；本輪薄 PROMPT §6 明令發布，A6 blocked_effects 未列 publish | 新增 §7 發布授權對帳；不以沉默帶過 |
| M3 | B3 `273 ready`／`273 ROUTE_OUT` | `ready` 只等於 source-bound；owner 365/365 為字面 `#`、ratification 全 `CANDIDATE_NOT_RATIFIED`、route `first_fail` 全 null | 拆為 `source_bound_ready`＝273、`admission_ready`＝**0**、`route_out`＝**0**；無 owner 一律 `ROUTE_OWNER_UNBOUND` |
| M4 | 「首切片 preimage ABSENT」與收據矛盾 | admission 的 `preimage_state` 是寫入後快照；slice1 產品收據被 guard 測試覆寫 | admission 分列 `preimage_state_at_first_slice`／`postimage_state_at_this_run`，並自報 slice1 收據遺失 |
| M5 | 44 案只有一份判定 | `b3_r7_neg_mutations.json` 曾寫 `PASS_REFUSAL: 44`，與 reconcile 的 44 HOLD 互斥 | 該收據改記 `REFUSAL_EXECUTED`＋`superseded_by: b3_r7_neg_reconcile.json`；判定權只在 reconcile |
| M6 | B2 requiredness 判定可稽核 | 40 案以「atom＋作者限定詞」形狀放行、34 案同形狀卻 UNKNOWN，規則未宣告 | 限定詞形狀改 `AUTHOR_QUALIFIER_UNRATIFIED`→HOLD；PASS 2786、HOLD 144 |
| M7 | 跨收據計數一致 | B2 `receivers.B3` 1351/114（mandatory 3 欄）與 B3 `join` 0/1465（含 metadata）不同義 | §4 新增對帳表，逐欄列出 mandatory 集合差異 |
| M8 | 權利與時間已量測 | 收據無 `checked_at`；consumer 內嵌 authority `expires_at=2026-11-27T01:08` 卻稱 live；`ops_used=0` | consumer 加 `ENVELOPE_AUTHORITY_EXPIRED` fail-closed；本輪 window 已關，三端為 `RIGHTS_UNVERIFIED`（更嚴），該分支**本輪未行使** |
| M9 | FirstFail 雙極性已比對 | B2 無 `expected_first_fail` 欄 | 三批收據加 `expected_first_fail`／`observed_first_fail`／`first_fail_matches`；覆蓋見 §3 |
| M10 | 文件數字與收據一致 | CLOSEOUT 引 45d41c59 為「凍結候選」、HANDOFF 重現指令 `--include-docs` 與凍結相反、建議把 `DIRECT_CLAUSE_SHA_MISMATCH` 映射成原碼 | 全部更正；「映射成原碼」改為「實作三個原 FirstFail 判定，不得改標籤」 |

## 1｜SPEC 身份（重算）

| 批 | pin | bytes | 載體 | Unit | Case | payload_sha 全等 | kind 分母 |
|---|---|---:|---:|---:|---:|---:|---|
| B1 | `28437e1b249291f9` | 266,543 | 2 | 30 | 60 | 30/30 | {'BASE': 18, 'KERNEL': 5, 'FDA': 7} |
| B2 | `acd3282319116142` | 12,552,061 | 2 | 1465 | 2930 | 1465/1465 | {'HARD': 18, 'E00_TECH': 8, 'TECH_ROUTE': 54, 'Q_SOURCE_ROW': 1385} |
| B3 | `c1c9c5326a36c1e0` | 1,577,104 | 2 | 365 | 752 | 365/365 | {'CHILD': 11, 'DOC_BRIDGE': 92, 'H1_ROUTE': 81, 'CHILD_ROUTE': 90, 'BEHAVIOR_ROUTE': 73, 'PROTECTED': 11, 'RECOVERY': 2, 'AUTHORITY_SEAM': 5} |

manifest 8 列全等 `True`；sha `2e4db2d2c2bd6d52…`。每批在 K 有兩個位元組全等載體。

## 2｜真跑結果（rev2 數字）

| 批 | 規模 | 判定 | 收據 |
|---|---|---|---|
| B1 | 30／60／4 Op | PASS 32／PASS_SOURCE_BOUND 5／PARTIAL 5／HOLD 18／FAIL 0 | `b1_r7_tqaep.json` |
| B1 EDGE/SEC | 9 | PASS 9／FAIL 0 | `b1_r7_edge_sec.json` |
| B2 | 1,465／2,930／4 Op | PASS 2786／HOLD 144／FAIL 0；Q 列 1385/1385 | `b2_r7_tqaep.json` |
| B2 META | 18 HARD | COLLECTED 2／UNBOUND 7／非發行物 9 | `b2_r7_meta.json` |
| B3 | 365／752 | PASS_SOURCE_BOUND 688／HOLD 64／FAIL 0 | `b3_r7_tqaep.json` |
| B3 四 Op | 365 rows | source_bound_ready 273／admission_ready **0**；child 22／92；route source_bound 273／route_out **0** | `b3_r7_product.json` |
| B3 COMMIT | 1 檔 | rev2 執行時 window 已關→`NOT_COMMITTED`／`OWNER_WINDOW_CLOSED`；既有 draft 為歷史效果，不重寫 | 同上 |
| B3 44 NEG | 44 | 執行 44 案、判定 {'HOLD': 44} | `b3_r7_neg_reconcile.json` |
| 三端接收 | B1／B2／B3 | `REJECT`／`RIGHTS_UNVERIFIED`（見 §5） | `r7_consumer_receipts.json` |
| 接收自測 | 11 臂 | `HOLD_BASELINE_NOT_VALID`（baseline `RIGHTS_UNVERIFIED`） | `r7_consumer_selftest.json` |
| B4 最小接收 | B1 RepoReadSet | ACCEPT 6／REFUSE 29 | `r7_b4_receiver.json` |

## 3｜FirstFail 雙極性覆蓋（M9）

| 批 | Case | 宣告 expected 數 | 實際比對數 | 相等 |
|---|---:|---:|---:|---:|
| B1 | 60 | 60 | 6 | 6 |
| B2 | 2930 | 1465 | 0 | 0 |
| B3 | 752 | 387 | 44 | 0 |

`first_fail_matches` 為 null 表示該案沒有 observed first-fail（POS 案常態），不是「比對通過」。

## 4｜跨收據對帳（M7）

| 量 | 收據 | 語義 | 可直接相比 |
|---|---|---|---|
| B2 `receivers.B3` accepted 1317／rejected 148 | `b2_r7_tqaep.json` | mandatory = tool_key, source_row, requiredness（3 欄） | 否 |
| B2 `receivers.B5` accepted 4／rejected 1461 | 同上 | mandatory 加 metadata, missing（4 欄） | 否 |
| B3 join `with_mandatory` 0／`with_missing` 1465 | `b3_r7_tqaep.json` | 以 metadata 為 mandatory（B5 級） | 否 |
| B2 HOLD 144 | 同上 | 逐案判定（含 requiredness 不可分類者） | — |

分母同為 1,465，mandatory 集合不同，數字不同義。SPEC §6 的「96 missing／62 unresolved」屬該版敘述，與本輪 HOLD 144 為不同量，**UNRECONCILED**，不得互相引用。

## 5｜四 Ready 與接受

| 批 | ReadyDraft | ReadyAtom | ReadyExecute | ReadyAccept | 現狀 |
|---|---|---|---|---|---|
| B0 | 是（歷史 CORE_ACCEPTED 保留） | 是 | 否 | 否 | `HOLD`：descriptor 2026-11-27T01:08 到期 |
| B1 | 是 | 是 | 部分（D-2／D-3 未閉） | 否 | `PARTIAL` |
| B2 | 是 | 是 | 部分（18 HARD source_row、inner/outer） | 否 | `PARTIAL` |
| B3 | 是 | **True**（無 owner／無 ratified atom） | 否 | 否 | `ReadyExecute=HOLD` |

三端接收（rev2，window 已關）：

| consumer | decision | first_fail | rights_currency | checked_at |
|---|---|---|---|---|
| B1 | REJECT | `RIGHTS_UNVERIFIED` | `None` | `2026-11-27T16:00:55+0800` |
| B2 | REJECT | `RIGHTS_UNVERIFIED` | `None` | `2026-11-27T16:00:55+0800` |
| B3 | REJECT | `RIGHTS_UNVERIFIED` | `None` | `2026-11-27T16:00:55+0800` |

## 6｜未閉合義務（五類）

| 類 | 內容 | 主責 |
|---|---|---|
| 1 可自行取得 | r7 pin／census／payload 完整性（已完成） | — |
| 2 需工程 | B2 18 HARD `source_row`；9 HARD inner/outer；B3 NEG-design 結構化＋owner 綁定（44 案與 `admission_ready=0` 的共同成因） | 工程 |
| 3 需設計補編 | DOC_BRIDGE heading 計數契約；BEHAVIOR／SEAM／RECOVERY typed fixture；B2 requiredness 限定詞形狀契約 | 工程＋具權採納 |
| 4 需原權位 | B0 descriptor 續期（Owner）；D-2 四測試讀權；D-3 七槽 M:N；D-4 五 Kernel 語義；TT-UP-1／6 E00／54 ROUTE | 見左列 |
| 5 下游驅動 | B4 驅 B1 BASE 012–016；B5 驅 B2 HOLD 144；B6 驅 20 Edge／8 Port | B4／B5／B6 |

## 7｜發布授權對帳（M2）

| 依據 | 內容 | 效力 |
|---|---|---|
| r7 入口 §7 | 「本次上推 未推送（`REMOTE_PUBLICATION_HOLD`）」、distribution `LOCAL_ONLY` | 記錄 **r7 撰寫輪**（A6 採納輪）的狀態 |
| 本輪薄 PROMPT §6 | 明令以 `API KEY/GITHUB-REPO_SHW097-4.txt` 一次性認證增量推至 `shw097-team/SQS-THC_MVP`，並要求 remote readback | 本輪授權來源 |
| A6 blocked_effects | B1 live submit／B2 真 ToolReadSet ACK／B3 產品 JOIN/CHILD/ROUTE/COMMIT／B0 新 source 讀取 | 未列 publish |

本輪發布以薄 PROMPT 為授權；發布物為**去識別化衍生物**（`code/`、`docs/` 重排，逐檔記 frozen 與 published 兩個 sha），LOCAL_ONLY 原件不散布。此裁量已記錄，非默示。

## 8｜不宣稱

- 未宣稱任何批次接受或 `ReadyExecute`；`admission_ready=0`、`route_out=0`。
- 未宣稱語意等價、原 Reader 已具、B2 PASS 可作准入。
- `ENVELOPE_AUTHORITY_EXPIRED` 分支本輪**未行使**（window 已關，三端先被 `RIGHTS_UNVERIFIED` 攔下）：程式 fail-closed，但沒有收據證明它會紅——下一輪必須在有窗時執行一次。
- 未改動任何 active pin、未關閉任何 edge、未升格任何項目（`promoted_to_primary: []`）。
