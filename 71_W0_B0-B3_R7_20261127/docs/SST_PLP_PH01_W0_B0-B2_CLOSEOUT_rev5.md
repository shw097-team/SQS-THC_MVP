# SST_PLP_PH01_W0 B0–B2 CLOSEOUT rev5｜B3 准入（2026-11-27_r7）

- 產生：`2026-11-27T19:17:56+0800`；由 `20_DEV/r7/r7_closeout_gen_rev5.py` 從收據生成
- Subject／Wave：`SST/SQS-THC/PH01/E00`／`P1-W00M`；活動 SPEC `2026-11-27_r7_Native-first_CODEX_FINAL`
- 凍結：`46bc8680f84f8b29d6d48a3ce0259e0870782ead3ef68cdfd452bfcb7e089fbe`（`r7_candidate_freeze.rev11.json`，70 成員；supersedes 10 版：45d41c592ef3…, 3718ee03c60e…, ad830f6bd9d9…, 65ef7a75107d…, 38f20921b7da…, 04d63bbb6f14…, c7baa16eaa88…, 690af85b87c9…, 64125152833e…, 816119811b66…）
- 權利：window `WIN-5afc943249a6`／`CLOSED`／ceiling `READ_ONLY_PROBE`／ops_used `0`
- 宣稱上限：`B0_COMPLETE`／`B1_ACCEPTED`／`B2_ACCEPTED`／`B3_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` **均未成立**；`FIN_ORDER=DENY`

## 0｜撤回表（rev1 主張 → 實測 → rev2 處分）

rev1 經分離 Checker 判 **REJECT（10 條 mandatory）**。逐條更正，凡收據無法支撐的敘述一律撤回。

| # | rev1 主張 | 實測 | rev2 處分 |
|---|---|---|---|
| M1 | 凍結候選不可變 | `r7_freeze.py` 以 `w` 就地覆寫；Checker 讀取期間 digest 由 `68162489…` 變 `45d41c59…`，腳本亦在查核中被改 | 凍結改**寫一次**：無 `--revision` 時拒絕覆寫，新修訂為新檔並記 `supersedes`。6816 版僅存於公開 commit `64747d6`，本檔不假造「已還原」 |
| M2 | 未處理與 SPEC §7 `REMOTE_PUBLICATION_HOLD` 的衝突 | r7 入口 §7 為**撰寫輪**狀態；本輪薄 PROMPT §6 明令發布，A6 blocked_effects 未列 publish | 新增 §7 發布授權對帳；不以沉默帶過 |
| M3 | B3 `273 ready`／`273 ROUTE_OUT` | `ready` 只等於 source-bound；owner 365/365 為字面 `#`、ratification 全 `CANDIDATE_NOT_RATIFIED`、route `first_fail` 全 null | 拆為 `source_bound_ready`＝273、`admission_ready`＝**18**、`route_out`＝**18**；無 owner 一律 `ROUTE_OWNER_UNBOUND` |
| M4 | 「首切片 preimage ABSENT」與收據矛盾 | admission 的 `preimage_state` 是寫入後快照；slice1 產品收據被 guard 測試覆寫 | admission 分列 `preimage_state_at_first_slice`／`postimage_state_at_this_run`，並自報 slice1 收據遺失 |
| M5 | 44 案只有一份判定 | `b3_r7_neg_mutations.json` 曾寫 `PASS_REFUSAL: 44`，與 reconcile 的 44 HOLD 互斥 | 該收據改記 `REFUSAL_EXECUTED`＋`superseded_by: b3_r7_neg_reconcile.json`；判定權只在 reconcile |
| M6 | B2 requiredness 判定可稽核 | 40 案以「atom＋作者限定詞」形狀放行、34 案同形狀卻 UNKNOWN，規則未宣告 | 限定詞形狀改 `AUTHOR_QUALIFIER_UNRATIFIED`→HOLD；PASS 2766、HOLD 164 |
| M7 | 跨收據計數一致 | B2 `receivers.B3` 1351/114（mandatory 3 欄）與 B3 `join` 0/1465（含 metadata）不同義 | §4 新增對帳表，逐欄列出 mandatory 集合差異 |
| M8 | 權利與時間已量測 | 收據無 `checked_at`；consumer 內嵌 authority `expires_at=2026-11-27T01:08` 卻稱 live；`ops_used=0` | consumer 加 `ENVELOPE_AUTHORITY_EXPIRED` fail-closed；本輪 window 已關，三端為 `RIGHTS_UNVERIFIED`（更嚴），該分支**本輪未行使** |
| M9 | FirstFail 雙極性已比對 | B2 無 `expected_first_fail` 欄 | 三批收據加 `expected_first_fail`／`observed_first_fail`／`first_fail_matches`；覆蓋見 §3 |
| M10 | 文件數字與收據一致 | CLOSEOUT 引 45d41c59 為「凍結候選」、HANDOFF 重現指令 `--include-docs` 與凍結相反、建議把 `DIRECT_CLAUSE_SHA_MISMATCH` 映射成原碼 | 全部更正；「映射成原碼」改為「實作三個原 FirstFail 判定，不得改標籤」 |

## 0.5｜本輪增量（rev5）

| # | 項目 | 實測 | 收據 |
|---|---|---|---|
| N-1 | B0 descriptor 續期 | 舊 `2064685a…` 封存，新 `ad78641547abfb41…`（3670 B），僅改 authorization／usage_evidence／時窗 | `b0_descriptor_renewal.json` |
| N-2 | B0 當期真讀取 | `SST.B0.SourceReadSet/2`、2 源、R/P/M 齊、14 authority 欄、`missing=[]`、`write_set=[]`、exit 0 | `b0_current_sourcereadset.json` |
| N-3 | 三端真接收 | B1／B2／B3 皆 `ACCEPT`、currency `CURRENT`（usage_evidence_sha 等於現行收據 sha） | `r7_consumer_receipts.json` |
| N-4 | 接收自測 | 12/12，含新增 `AUTHORITY_EXPIRED → ENVELOPE_AUTHORITY_EXPIRED`（上一輪未行使的分支） | `r7_consumer_selftest.json` |
| N-5 | B0 產品案 | **137/137 OK**（`env -u TMPDIR`、TMP=TEMP=20_DEV/.tmp_tests） | 本輪實跑，見 CLOSEOUT §2 |
| N-6 | 凍結寫入紀律 | 拒絕前不寫任何檔；每次修訂獨立 manifest；supersedes 為完整鏈 | `r7_freeze.py`、rev5 收據 |
| N-7 | B1 逐 key 對帳 | 11 追蹤於 pin、1 目錄未追蹤、4 磁碟未追蹤、6 外部 allowlist、1 在 allowlist 外（D-2） | `b1_r7_base_reconcile.json` |
| N-8 | B2 差額對帳 | 144 HOLD＝34 作者限定詞＋110 UNKNOWN；限定詞清單（EVAL_ONLY_*／REFERENCE_*）已列 | `b2_r7_qualifier_delta.json` |
| N-9 | B3 NEG 重建 | 44 案：**42 PASS**（宣告碼相符）、2 HOLD（owner／requiredness 無結構載體）；判定已移入產品 callable | `b3_r7_neg_mutations.json`（v2） |
| N-10 | B3 TQAEP | 688 SOURCE_BOUND／42 PASS／22 HOLD | `b3_r7_tqaep.json` |

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
| B2 | 1,465／2,930／4 Op | PASS 2766／HOLD 164／FAIL 0；Q 列 1385/1385 | `b2_r7_tqaep.json` |
| B2 META | 18 HARD | COLLECTED 2／UNBOUND 7／非發行物 9 | `b2_r7_meta.json` |
| B3 | 365／752 | PASS_SOURCE_BOUND 688／HOLD 22／FAIL 0 | `b3_r7_tqaep.json` |
| B3 四 Op | 365 rows | source_bound_ready 273／admission_ready **18**；child 22／92；route source_bound 273／route_out **18** | `b3_r7_product.json` |
| B3 COMMIT | 1 檔 | rev2 執行時 window 已關→`DRY_RUN`／`None`；既有 draft 為歷史效果，不重寫 | 同上 |
| B3 44 NEG | 44 | 執行 44 案、判定 {'PASS': 42, 'HOLD': 2} | `b3_r7_neg_reconcile.json` |
| 三端接收 | B1／B2／B3 | `ACCEPT`／`None`（見 §5） | `r7_consumer_receipts.json` |
| 接收自測 | 12 臂 | `12/12 PASS`（baseline `None`） | `r7_consumer_selftest.json` |
| B4 最小接收 | B1 RepoReadSet | ACCEPT 6／REFUSE 29 | `r7_b4_receiver.json` |

## 3｜FirstFail 雙極性覆蓋（M9）

| 批 | Case | 宣告 expected 數 | 實際比對數 | 相等 |
|---|---:|---:|---:|---:|
| B1 | 60 | 60 | 6 | 6 |
| B2 | 2930 | 1465 | 0 | 0 |
| B3 | 752 | 387 | 42 | 42 |

`first_fail_matches` 為 null 表示該案沒有 observed first-fail（POS 案常態），不是「比對通過」。

## 4｜跨收據對帳（M7）

| 量 | 收據 | 語義 | 可直接相比 |
|---|---|---|---|
| B2 `receivers.B3` accepted 1317／rejected 148 | `b2_r7_tqaep.json` | mandatory = tool_key, source_row, requiredness（3 欄） | 否 |
| B2 `receivers.B5` accepted 4／rejected 1461 | 同上 | mandatory 加 metadata, missing（4 欄） | 否 |
| B3 join `with_mandatory` 0／`with_missing` 1465 | `b3_r7_tqaep.json` | 以 metadata 為 mandatory（B5 級） | 否 |
| B2 HOLD 164 | 同上 | 逐案判定（含 requiredness 不可分類者） | — |

分母同為 1,465，mandatory 集合不同，數字不同義。SPEC §6 的「96 missing／62 unresolved」屬該版敘述，與本輪 HOLD 164 為不同量，**UNRECONCILED**，不得互相引用。

## 5｜四 Ready 與接受

| 批 | ReadyDraft | ReadyAtom | ReadyExecute | ReadyAccept | 現狀 |
|---|---|---|---|---|---|
| B0 | 是 | 是 | 是（當期讀取＋三端接收＋137/137） | 是（本輪真跑；分離 Checker 對 B0 另判） | `B0_COMPLETE` |
| B1 | 是 | 是 | 部分（D-2／D-3 未閉） | 否 | `PARTIAL` |
| B2 | 是 | 是 | 部分（18 HARD source_row、inner/outer） | 否 | `PARTIAL` |
| B3 | 是 | **False**（347/365 Unit 未宣告 owner） | 否 | 否 | `ReadyExecute=HOLD`；18 atom 已具 owner＋source |

三端接收（rev5，當期 envelope，currency CURRENT）：

| consumer | decision | first_fail | rights_currency | checked_at |
|---|---|---|---|---|
| B1 | ACCEPT | `None` | `CURRENT` | `2026-11-27T18:10:46+0800` |
| B2 | ACCEPT | `None` | `CURRENT` | `2026-11-27T18:10:46+0800` |
| B3 | ACCEPT | `None` | `CURRENT` | `2026-11-27T18:10:47+0800` |

## 6｜未閉合義務（五類）

| 類 | 內容 | 主責 |
|---|---|---|
| 1 可自行取得 | r7 pin／census／payload 完整性（已完成） | — |
| 2 需工程 | B2 18 HARD `source_row`；9 HARD inner/outer；B3 NEG-design 結構化＋owner 綁定（44 案與 `admission_ready=0` 的共同成因） | 工程 |
| 3 需設計補編 | DOC_BRIDGE heading 計數契約；BEHAVIOR／SEAM／RECOVERY typed fixture；B2 requiredness 限定詞形狀契約 | 工程＋具權採納 |
| 4 需原權位 | B0 descriptor 續期（Owner）；D-2 四測試讀權；D-3 七槽 M:N；D-4 五 Kernel 語義；TT-UP-1／6 E00／54 ROUTE | 見左列 |
| 5 下游驅動 | B4 驅 B1 BASE 012–016；B5 驅 B2 HOLD 164；B6 驅 20 Edge／8 Port | B4／B5／B6 |

## 7｜發布授權對帳（M2）

| 依據 | 內容 | 效力 |
|---|---|---|
| r7 入口 §7 | 「本次上推 未推送（`REMOTE_PUBLICATION_HOLD`）」、distribution `LOCAL_ONLY` | 記錄 **r7 撰寫輪**（A6 採納輪）的狀態 |
| 本輪薄 PROMPT §6 | 明令以 `API KEY/GITHUB-REPO_SHW097-4.txt` 一次性認證增量推至 `shw097-team/SQS-THC_MVP`，並要求 remote readback | 本輪授權來源 |
| A6 blocked_effects | B1 live submit／B2 真 ToolReadSet ACK／B3 產品 JOIN/CHILD/ROUTE/COMMIT／B0 新 source 讀取 | 未列 publish |

本輪發布以薄 PROMPT 為授權；發布物為**去識別化衍生物**（`code/`、`docs/` 重排，逐檔記 frozen 與 published 兩個 sha），LOCAL_ONLY 原件不散布。此裁量已記錄，非默示。

## 8｜不宣稱

- **B0 例外並具名**：`B0_COMPLETE` 由本輪真跑（當期讀取、三端 CURRENT、12/12 自測、137/137 產品案、descriptor 續期）支撐；除此之外未宣稱任何批次接受。
- `ReadyExecute=false`；`admission_ready=18`、`route_out=18`（18 個 Unit 於條文宣告 Owner，其餘 347 未宣告）。
- 未宣稱語意等價、原 Reader 已具、B2 PASS 可作准入。
- `ENVELOPE_AUTHORITY_EXPIRED` 分支本輪**未行使**（window 已關，三端先被 `RIGHTS_UNVERIFIED` 攔下）：程式 fail-closed，但沒有收據證明它會紅——下一輪必須在有窗時執行一次。
- 未改動任何 active pin、未關閉任何 edge、未升格任何項目（`promoted_to_primary: []`）。
