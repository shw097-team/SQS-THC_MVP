# SST_PLP_PH01_W0 B0–B2 CLOSEOUT｜B3 准入（2026-11-27_r7）

- 產生：`2026-11-27T15:45:36+0800`（本檔由 `20_DEV/r7/r7_closeout_gen.py` 從收據生成，數字非手抄）
- Subject／Wave：`SST/SQS-THC/PH01/E00`／`P1-W00M`
- 活動 SPEC：`2026-11-27_r7_Native-first_CODEX_FINAL`（入口 `00_唯一交付入口_W0_B0-B3_2026-11-27_r7.md`，sha `21c27fbb4f40c82b…`；A5 機械 PASS＋A6 採納 2026-11-27T14:47+08:00）
- 凍結候選：`45d41c592ef3e89b755a05a7db28798fee044c8e1a81a867b1528e7e00af71b2`（41 成員；`r7_candidate_freeze.json`）
- 權利：owner window `WIN-3657818f0331`／task `SST_PLP_PH01_W0_B0-B3_R7_ACCEPT`／ceiling `HOST_OPERATIONS`／state `OPEN`
- 宣稱上限：`B0_COMPLETE`／`B1_ACCEPTED`／`B2_ACCEPTED`／`B3_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` **均未成立**；`FIN_ORDER=DENY`

## 1｜SPEC 身份與完整性（重算，不引用前輪）

| 批 | pin（前 16） | bytes | 載體數 | Unit | Case | payload_sha 全等 | kind 分母 |
|---|---|---:|---:|---:|---:|---:|---|
| B1 | `28437e1b249291f9` | 266,543 | 2 | 30 | 60 | 30/30 | {'BASE': 18, 'KERNEL': 5, 'FDA': 7} |
| B2 | `acd3282319116142` | 12,552,061 | 2 | 1465 | 2930 | 1465/1465 | {'HARD': 18, 'E00_TECH': 8, 'TECH_ROUTE': 54, 'Q_SOURCE_ROW': 1385} |
| B3 | `c1c9c5326a36c1e0` | 1,577,104 | 2 | 365 | 752 | 365/365 | {'CHILD': 11, 'DOC_BRIDGE': 92, 'H1_ROUTE': 81, 'CHILD_ROUTE': 90, 'BEHAVIOR_ROUTE': 73, 'PROTECTED': 11, 'RECOVERY': 2, 'AUTHORITY_SEAM': 5} |

- manifest 8 列全等：`True`；manifest sha `2e4db2d2c2bd6d52…`。
- 每批在 K 內有 **兩個位元組全等載體**（根目錄與 `W0_B0-B3_r7/`）：同一來源兩處放置，非碰撞；主用取較淺路徑，兩者 sha 皆等於 pin（見 `r7_preflight.json` `carriers`）。
- Unit↔Case join 雙向零缺零多；`unique_unit_ids`＝`unique_keys`＝Unit 數。

## 2｜真跑結果（本輪實際執行）

| 批 | 規模 | 判定 | 收據 |
|---|---|---|---|
| B1 REPO/BASE/FDA/ROOTS | 30 Unit／60 Case／4 Op | PASS 32／PASS_SOURCE_BOUND 5／PARTIAL 5／HOLD 18／FAIL 0 | `40_OPS/b1_r7_tqaep.json`、`b1_r7_run_all.json` |
| B1 EDGE/SEC | 9 | PASS 9／FAIL 0 | `40_OPS/b1_r7_edge_sec.json` |
| B2 QROWS/HARD/META/RETURN | 1,465 Unit／2,930 Case／4 Op | PASS 2854／HOLD 76／FAIL 0；Q 列 1385/1385 實體行核對、索引列＝宣告列 | `40_OPS/b2_r7_tqaep.json`、`b2_r7_tool_readset.json` |
| B2 META | 18 HARD | 取得 2／VERSION_UNBOUND 7／非發行物 9 | `40_OPS/b2_r7_meta.json` |
| B3 JOIN/CHILD/ROUTE | 365 Unit／752 Case | PASS_SOURCE_BOUND 688／HOLD 64／FAIL 0 | `40_OPS/b3_r7_tqaep.json` |
| B3 四 Op 記憶體 | 365 rows | join 273/92（ready/held）、child 22／92、route 273／92 | `40_OPS/b3_r7_product.json` |
| B3 COMMIT 首切片 | 1 檔 | `COMMITTED`、preimage `ABSENT`、postimage `True`、`write_set` 單檔、rights `OWNER_WINDOW:WIN-3657818f0331:HOST_OPERATIONS` | 同上 |
| B3 44 NEG 真變異 | 44 | {'HOLD': 44}；否證原因 {'MUTATION_NOT_FAITHFUL:MUTATION_DELETES_NEG_CARRIER_WITH_UNIT': 12, 'MUTATION_NOT_FAITHFUL:MUTATION_NOT_DECLARED_SHAPE': 11, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:original_id': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:source_sha256': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:clause_span': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:parent': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:polarity': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:requiredness': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:owner': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:oracle': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:case': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:draft': 1, 'FIRST_FAIL_CODE_DIVERGENT': 11} | `40_OPS/b3_r7_neg_reconcile.json` |
| 三端接收 | B1／B2／B3 | 各欄齊；currency 見 §4 | `40_OPS/r7_consumer_receipts.json` |
| 接收反例 | 11 臂 | 11/11（1 POS＋10 單變異全拒，first_fail 精確） | `40_OPS/r7_consumer_selftest.json` |
| B4 最小接收 | B1 RepoReadSet | ACCEPT 6／REFUSE 29（未追蹤目標 commit/blob 為 null） | `40_OPS/r7_b4_receiver.json` |

## 3｜本輪修正（前輪膨脹的更正，不是新增功能）

| # | 前輪主張 | 本輪量測 | 處分 |
|---|---|---|---|
| R-1 | B1 `FIXTURE_ONLY` 12 案列為 pass 家族、`PASS_EVIDENCE` 5 案列為 PASS | fixture 域檢查與 symbol 身分皆非產品語意 PASS | 12 案降 `HOLD`（`FIXTURE_ONLY_NO_PRODUCT_CALLABLE`）；5 案改 `PASS_SOURCE_BOUND` 並標 `CONTENT_IDENTITY_AND_SYMBOL_SPAN_ONLY` |
| R-2 | B3 `PASS_REFUSAL` 44 案 | 該判定只依「atom 不在 B2 ToolReadSet」——對每個 CHILD atom 恆真、與變異無關 | 44 案全數 `HOLD`：`{'MUTATION_NOT_FAITHFUL:MUTATION_DELETES_NEG_CARRIER_WITH_UNIT': 12, 'MUTATION_NOT_FAITHFUL:MUTATION_NOT_DECLARED_SHAPE': 11, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:original_id': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:source_sha256': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:clause_span': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:parent': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:polarity': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:requiredness': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:owner': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:oracle': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:case': 1, 'MUTATION_NOT_FAITHFUL:MUTATION_APPLIED_TO_WRONG_FIELD:draft': 1, 'FIRST_FAIL_CODE_DIVERGENT': 11}` |
| R-3 | B3 ledger 每跑一次 digest 不同 | 正文含 wall clock | 時間移出正文、只留收據；兩次連跑 digest 相同（`1861ca3ab35aa71f…`） |
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
| B1 | ACCEPT | `ENVELOPE_MINTED_UNDER_A_DIFFERENT_WINDOW` | `2026-11-27T15:40:58+0800` |
| B2 | ACCEPT | `ENVELOPE_MINTED_UNDER_A_DIFFERENT_WINDOW` | `2026-11-27T15:40:58+0800` |
| B3 | ACCEPT | `ENVELOPE_MINTED_UNDER_A_DIFFERENT_WINDOW` | `2026-11-27T15:40:58+0800` |

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

## 7｜發布（衍生物，非接受）

- 若 `50_PUBLISH/publish_record.json` 存在，以下由該收據生成；未存在時為 `NOT_PUBLISHED`。

- Repo：`https://github.com/shw097-team/SQS-THC_MVP`（public）／branch `main`
- commit：`a0745127d9894750ad6dbd7740872fed760d5a0d`（前一 HEAD `24a59f5cbc12a5fc5a2dfcb4a5cf879b4628c515`）
- 已發布 48 檔／5,931,953 bytes；LOCAL_ONLY 排除 2 檔（40_OPS/b3_r7_product.json, 40_OPS/b3_r7_tqaep.json）
- readback：5/5 匿名 raw 取回與 staged 檔 sha256 全等
- `this record names a074512, the commit that carries the superseding tree (digest 45d41c59…); a later doc-only commit that updates final_head_at_readback advances HEAD by one, which is recorded in the field itself rather than chased`

## 8｜不宣稱

- 未宣稱 `B0_COMPLETE`／`B1_ACCEPTED`／`B2_ACCEPTED`／`B3_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute`。
- 未宣稱任何語意 oracle 已綁；`PASS_SOURCE_BOUND` 只證 locator 與身分，不證語意。
- 未關閉任何 edge、未改動任何 active pin、未升格任何項目（`promoted_to_primary: []`）。
- 未使用 B0 的新讀取；三端接收的 envelope 為歷史 B0 readset，currency 已逐端標示。
