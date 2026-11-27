# SESSION CLOSEOUT｜SST PH01 W0 B0–B3（2026-11-27）

- 產生：2026-11-27T19:52:36+0800；由 `20_DEV/r7/r7_session_closeout.py` 從收據生成
- 本 SESSION 範圍：r7 活動 SPEC 下的 B0 閉合、B1／B2 必要差額、B3 產品語義與准入評估、交付與發布
- 宣稱上限：`B0_COMPLETE` 成立；`B1_ACCEPTED`／`B2_ACCEPTED`／`B3_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` **不成立**；`FIN_ORDER=DENY`

## 1｜本 SESSION 的實質結論

| 批 | 狀態 | 憑據 |
|---|---|---|
| B0 | `COMPLETE`／`accepted=true` | 當期 descriptor 續期、真 `SourceReadSet/2`、三端 ACCEPT／CURRENT、自測 12/12、產品案 137/137×2（Ran 137 tests in 372.718s / OK） |
| B1 | `PARTIAL_PARK_UNTIL_DELTA` | 60 案 PASS 32／HOLD 18／PARTIAL 5／PASS_SOURCE_BOUND 5；逐 key 對帳 11／1／4／6／1 |
| B2 | `PARTIAL` | 2,930 案 PASS 2766／HOLD 164；案級比對 46、相等 26、分歧 20 |
| B3 | `ReadyAtom=false`／`ReadyExecute=false` | 752 案 PASS_SOURCE_BOUND 688／HOLD 22／PASS 42；NEG PASS 42／HOLD 2；`admission_ready=90/273` |

## 2｜升格（候選 → 主用）核對

本輪**有**升格：B0 的接受證據由候選升為主用，並記入 `DELIVERY_INDEX.promotion_state.promoted_to_primary` 與 `40_OPS/PROMOTION_RECORD.json`。

| 項目 | 路徑 | bytes | sha256 | 依據 |
|---|---|---:|---|---|
| B0 descriptor renewal | `40_OPS/b0_descriptor_renewal.json` | 1,332 | `b63234ef78253ded…` | window WIN-5afc943249a6, ceiling READ_ONLY_PROBE, only authorization/usage/time changed |
| B0 current SourceReadSet/2 | `40_OPS/b0_current_sourcereadset.json` | 5,429 | `2a226d27b1559dc7…` | exit 0, 2 sources, 14 authority fields, missing=[], write_set=[] |
| B0 three-end receive | `40_OPS/r7_consumer_receipts.json` | 10,007 | `e5beb6c873c240bb…` | B1/B2/B3 ACCEPT, currency CURRENT (usage_evidence_sha equals the live receipt) |
| consumer self-test | `40_OPS/r7_consumer_selftest.json` | 1,905 | `be596df8214e0174…` | 12/12 arms, including ENVELOPE_AUTHORITY_EXPIRED |
| B0 product case suite | `40_OPS/b0_product_test_2026-11-27.log` | 244 | `8d008cc40fc5c051…` | 137 tests OK, bounded temp root, TMPDIR unset |

**未升格（不連帶）**：

| 批 | 原因 |
|---|---|
| B1 | 本輪無可解新差額（PARK 條件未變） |
| B2 | 20 個 ROUTE 案的產品碼與 SPEC 宣告 FirstFail 不同，需具權裁定 |
| B3 | 183/273 source-bound atom 無 owner 宣告；requiredness 無跨批載體 |

### 先前錯置與更正

| 錯置 | 實際 | 更正 |
|---|---|---|
| `DELIVERY_INDEX.phase_status.B0 = HOLD_RIGHTS_CURRENCY`、`accepted.B0=false`、blockers 仍寫「B0 SourceReadSet/2 currency」 | B0 已於本輪閉合 | 由 `r7_layers.py` 依收據重算為 `COMPLETE`／`accepted.B0=true`，blockers 改列 B2／B3 真差額 |
| 未版本化 `40_OPS/r7_candidate_freeze.json`（digest `68162489…`）仍看起來像「現行」 | 它是 Checker 判過的第一版，現已 superseded | 分層標為 `SUPERSEDED`；現行候選只在 `40_OPS/r7_candidate_freeze.rev12.json` |
| `40_OPS/r7_checker_verdict.md` 被當作對「現行候選」的判決 | 它判的是 digest `68162489…`（rev1 base） | 分層改為 `VERDICT_SUPERSEDED`；現行候選**無** Checker verdict |
| 文件 rev1–rev5 與現行 rev6 混放 | 舊版仍會被誤引 | 分層 `DOC_HISTORY`（12 檔），現行文件只由 `DELIVERY_INDEX.current_pointers` 指向 |

## 3｜工程衛生（本輪實際處置）

| 層 | 檔數 | 說明 |
|---|---:|---|
| PRIMARY | 44 | 引擎、preflight、現行文件、發布紀錄 |
| CURRENT_CANDIDATE | 26 | 本輪候選收據（含 12 個 freeze／9 個 manifest 中的現行版） |
| SUPERSEDED | 19 | 舊 freeze／manifest，保留供稽核，不得引用為現行 |
| VERDICT_SUPERSEDED | 1 | 對舊 digest 的 Checker 判決 |
| DOC_HISTORY | 12 | 舊版 CLOSEOUT／HANDOFF／BOOTSTRAP |
| LOCAL_ONLY | 1 | `b0_current_sourcereadset.json`（權利窗內讀值，不上推） |
| EFFECT | 2 | `b3_ledger/` 兩份草稿（產品寫入，非輸入） |

刪除：`20_DEV/.tmp_tests`（測試產物，可重建）、`$TMPDIR` 內本輪探針檔（`b0req.json`、`*.out`／`*.err`／`b0tests.log`）；`__pycache__`／`*.pyc` 無（`-B` 執行）。**未刪**任何收據、凍結版本或草稿：皆為稽核鏈或權利證據。

## 4｜發布

| 項目 | 值 |
|---|---|
| Repo | `https://github.com/shw097-team/SQS-THC_MVP`（public） |
| 交付樹 commit | `743a47813fc70e8da7dc843a56be90e61432546a` |
| 凍結 | `r7_candidate_freeze.rev14.json`／`2d061f71fe42fe22…`（83 成員） |
| 排除 | `b0_current_sourcereadset.json`（LOCAL_ONLY）、`b3_r7_product.json`、`b3_r7_tqaep.json`（逐字條文） |
| 發布 ≠ 接受 | 發布只散布可散布的衍生證據；接受狀態見 §1 |

## 5｜不宣稱

- 除 B0 外未宣稱任何批次接受；`ReadyAtom=false`（90/273）。
- 現行候選（40_OPS/r7_candidate_freeze.rev12.json）**未經**分離 Checker；既有 verdict 只適用於 `68162489…`。
- 未動任何 active pin、未升格 B3 任何項目、未關閉任何 edge。
