## 裁決

1. **PASS** — 我以 `direct_parent_ref` 的 `a..b`（含第 b 行 LF）自算全部 **1,465/1,465** 的 `direct_clause_sha`，四 kind 全等（HARD 18、E00 8、ROUTE 54、Q 1,385），span 1,465 個全異；例 `B2.U0001` L93–116=`07870b8e…`、`B2.U0081` L751–751=`c7c50c0e…` 與宣告值相同（`20_DEV/b2_reader/b2_semantics.py:173-185`；`40_OPS/b2_toolreadset_20261126T145652.json:137-141`）。
2. **PASS** — 依 pinned 舊碼 `pin := source_payload[5]`、缺欄或含 `UNBOUND` 即計（`b2_ops_qrows.py:76-79`）重算得 **72 = HARD 16 + E00_TECH 2 + TECH_ROUTE 54**；E00 兩列正是 `B2.U0023 EFFECT_UNBOUND`、`B2.U0026 EXECUTOR_UNBOUND`，route payload 只有 2 欄；無欄 5 者 **54 且全為 TECH_ROUTE**（舊 TQAEP `b2_ops_tqaep.py:89`；`…145652.json:94-110`）。
3. **PARTIAL** — kind 層已標 `VERBATIM_ONLY`、route 標 N/A、已聲明 `disagreement_count=0` 不得當證據，Q4 也改正為 0 列（EVAL_ONLY 17 列全在 Q1）；但 TQAEP 仍把 **371 個 Q 列**判成 `requiredness_applicable=true / checked=true / agree=true`，比的卻是同一個 `source_payload[2]`（`b2_semantics.py:240-241,258-264`；`b2_ops_tqaep2.py:44-51,108-113`；`…145701.json:8281-8287`），且 TR 的 prose 864 與 TQAEP 的 N/A 1,014 不一致（`…145652.json:84-89`；`…145701.json:29225-29231`）。
4. **PASS** — 已改 `two_collinear_key_signals_agree_plus_source_row_ranges`、明文「NOT independent」，並列 disjoint 區間；我重算 440/513/378/54 與 233–672／680–1192／1200–1577／1585–1638 完全一致（`…145652.json:45-70`；`b2_ops_qrows2.py:189-212`）。
5. **PASS** — mutation 真的丟/造 namespace（`ECP_TECH43::…::ROW=233`、`WRONG-NS::…`），naive tail join **1,385/1,385 都命中 1 列**，oracle 對 dropped/forged 均回 `NAMESPACE_JOIN_DENY`、exact-key baseline_rows=1（`b2_semantics.py:290-318`；`…145701.json:4557-4573`）。
6. **PASS** — 18 HARD 中 **9 列**以單欄 `declared_requiredness=EVAL_ONLY` 執行（baseline=None），其餘 **9 列**已改判 `HOLD_SPEC_MUTATION_UNIMPLEMENTED`（tally 9），不再記 PASS（`b2_ops_tqaep2.py:176-191`；`…145701.json:62-66,101-110,149`）。
7. **PASS** — 54 route 全為 `PASS_INTERPRETED`，兩臂（`declared_requiredness=HARD`；`claimed_enable`）各自單欄、baseline=None，§06 原文確為「改一個受保護欄位」未指名欄位（`b2_ops_tqaep2.py:192-206`；`…145701.json:1257-1273`）。
8. **PASS** — 已用宣告式 `EXCLUSIVE_PAIRS` 取代「任意兩相異狀態」，8 列 baseline=None、加 counterpart 後 `STATE_CONFLICT`，且 `INSTALLED+ENABLED → null` 探針存在（`b2_semantics.py:210-216,329-343,352-362`；`…145701.json:860-873`）；惟比對用子字串，另有新增缺陷（見下）。
9. **PASS** — namespace NEG 已改用 `baseline_rows: 1`（1,385 筆），POS 已暴露 `requiredness_applicable/checked/reason`，非適用者 `requiredness_agree=null`（1,014 Q + 54 route）（`…145701.json:1240-1241,4569,8284-8287`）。
10. **PASS** — `463dcf33…` 以 sha 解析到 `PHASE 01~04\藍圖\實質正文\…r2.md`（767,859 B），**1,385/1,385** 標 `CARRIER_SOURCE_REBOUND_BY_SHA`／`CANDIDATE_NOT_RATIFIED`、`declared_path_has_stale_segment=true`；我另核 carrier 內容 key/source_row/payload/status **1,385/1,385 逐欄相等**（`b2_ops_qrows2.py:121-133`；`…145652.json:2344-2350`）。

## 重算

- **candidate_digest 完全可重現**：依 path 排序、`"<sha>  <path>"`、LF 串接、無尾端 LF，得 `cbaeeb8111c9567628674b00b30f287f48494cbf2dba9872e312c0923a43cd6a`，與凍結值相同；6 個 artefact 的 bytes/raw sha 也全部相符。
- **Pins**：SPEC 8,016,371 B／`140de5bc…`；parent 2,712,933 B／`d95c8ac6…`；carrier 767,859 B／`463dcf33…`；blueprint 457,294 B／`dd37a40b…`；evidence 1,140,669 B／`2cd8ab8b…`。宣告路徑 `W0_B0-m`、`PHASE 00~04` 均不存在，rebind 記述正確。
- **Clause**：1,465/1,465（唯一規則＝a..b 含 b 行 LF；1,465 個 span 全異，非模板重用）。
- **72/54**：72 = HARD 16 + E00 2 + ROUTE 54；54 = 無欄 5 = TECH_ROUTE exactly；clean_no_version 1,407 = 16/5/54/1,332（與 receipt 相同）。
- **Class／case**：2,930 案（1,465 POS + 1,465 NEG），**orphan 0／missing 0**，分布仍是 **NAMESPACE_JOIN_DENY 1,385／TOOL_REQUIREDNESS_HOLD 72／STATE_CONFLICT 8**；NEG 結果 1,402 PASS + 9 HOLD_SPEC_MUTATION_UNIMPLEMENTED + 54 PASS_INTERPRETED，0 FAIL；1,402 個 NEG PASS 的 `first_fail` 無 null。
- **Quadrant**：440/513/378/54＝1,385，non-Q 80＝18+8+54。
- **Payload provenance（我自行補證）**：Q 1,385/1,385 與 evidence 2cd8 逐欄相等；non-Q 80/80 與 blueprint dd37 逐欄相等；carrier 1,385/1,385 相等；payload_sha 1,465/1,465 重算相符。
- **Requiredness**：Q 列 371 判 applicable（HARD 18、OPTIONAL 209、EVAL_ONLY 17、DEFER_WITH_TRIGGER 126、REFERENCE_ONLY 1）、1,014 判 N/A；但 371 列的 independent 值就是同一 `source_payload[2]`，屬同欄自比。

## B2_ACCEPTED

**NO。** 理由：

1. Q requiredness 仍非獨立：371/1,385 列 `requiredness_checked=true` 是同一欄自比，1,014 列 N/A，真正的原列／原表比較為 **0**；與 receipt 自稱「1,385 Q rows are VERBATIM_ONLY」直接矛盾。
2. 9/18 HARD 與 54/54 route 並未依 §06 執行（前者 HOLD、後者 `PASS_INTERPRETED`），只有 9 HARD-loss＋8 state＋1,385 namespace 是可執行證據。
3. 所有來源（parent `d95c8ac6`、carrier `463dcf33`、blueprint `dd37a40b`、evidence `2cd8ab8b`）仍是 CANDIDATE_NOT_RATIFIED；B2 未執行任何產品案例。
4. `state_gate` 的互斥判定用子字串，對 `NOT_*` 單一狀態會誤報（見新增缺陷），尚不足以支撐一般化 STATE_CONFLICT oracle。

**Maker 縮小後的 claim 是否仍有超額？** payload＋clause identity 本身可成立（我獨立驗到 1,465/1,465 值等與 1,465/1,465 clause 重現），但仍有超額／不一致：

- `claim_scope.supported` 列了 7 項，其中 5 項（quadrant/case census/NS join/HARD deletion/state conflict）超出 freeze 宣告的 ceiling（payload＋clause）；HARD 那項已自我限定 9/18，state 那項則過寬。
- 371 個 Q POS 記 `requiredness_checked=true`，是對「VERBATIM_ONLY」ceiling 的越界陳述。
- `ROW_PAYLOAD_AND_PROVENANCE_IDENTITY` 在 receipt 內只用 payload_sha 自洽證明；對來源文件的值等是**本輪 checker 補證**的（結果為真，但 receipt 未證）。
- TR 對 Q／route 列仍寫 `requiredness_agree: true`（應為 null 或 false），與 `check_mode` 的 VERBATIM_ONLY／N/A 相衝（`…145652.json:84-89` vs `2313-2316`）。

## 新增缺陷

1. **Q requiredness 旗標不實（371 列）**：`requiredness_applicable/checked=true` 但 independent 與 row 同值；例 `B2.U0148`（OPTIONAL）規則文字寫「preserved verbatim」卻 `checked=true`（`…145701.json:8281-8287`；`b2_ops_tqaep2.py:44-51,108-113`）。應全數改 false/null，或實作真正的外部比較。
2. **SOFT/CONDITIONAL 被誤稱 prose（150 列 = 41+109）**：`S.REQ_TOKENS` 含 SOFT、CONDITIONAL，但 TQAEP 的 10-token 集把它們判 N/A，理由文字卻說「not a requiredness token」（`b2_semantics.py:204-206`；`b2_ops_tqaep2.py:39-41,48-50`；`…145701.json:4809-4815`）。
3. **prose 分母不一致**：TR `prose_rows_n_a=864`（12-token 集）vs TQAEP N/A 1,014（10-token 集），同一候選兩個答案（`…145652.json:87`）。
4. **`state_gate` 子字串自我觸發**：單一 `NOT_VERIFIED` 或 `NOT_INSTALLED_NOT_BOUND` 會回 `STATE_CONFLICT`（因同時含 `VERIFIED`/`INSTALLED` 與 `NOT_*`）；反之 `SELECTED_OPTIONAL_DISABLED + SELECTED_DOCUMENT_ADAPTER` 回 None。應改為精確 token／集合相等（`b2_semantics.py:352-362`）。本批 8 列 baseline 未踩到，故 8 案結論仍真。
5. **硬編碼的「已驗證」布林**：`key_signals_are_collinear: true`、`source_row_ranges_disjoint: true` 是常數而非計算值（`b2_ops_qrows2.py:196,208`）；值本身為真，但 receipt 未由資料導出。
6. **POS verdict 不含 clause**：`pos_ok = pin ∧ mandatory ∧ req ∧ q`，`clause_repro` 僅回報不入判定（`b2_ops_tqaep2.py:121`），故 `POS_PASS 1465` 不是 clause 認證；clause 另報 1,465/1,465（我已獨立確認）。
7. **HARD §06 mutation 是 disjunction**：9 列原文為「原 HARD 被删除**或**无权启用」，只實作删除臂（`declared_requiredness=EVAL_ONLY`），「無權啟用」臂在 HARD 未被測（`b2_ops_tqaep2.py:178-183`）。
8. **`join_rows` 仍保留 selector-shape 拒絕**：任何非 `{"key":…}` 先回 DENY（`b2_semantics.py:299-300`）；本輪證據路徑已改為 tail 身分否決，但形狀分支仍在，未來易被誤讀為 namespace 證據。

## 程序註記

- 全程唯讀：以 Node 重讀 SPEC、parent、carrier、blueprint、evidence、兩份 receipt 與原始碼；**未執行** Maker 產生器（會寫 receipt），未寫入任何檔案。本輪未取得 `-o` 路徑，故裁決僅在此輸出。
- Python 在環境中不可用（venv shim 指向不存在的 `python-3.14.9…`），改以 Node 自寫 parser 重算；所有統計皆由我自己的解析器得出，未採信 receipt 數值。
- 顯示端 PowerShell 對 UTF-8 中文有亂碼，但以 Node 讀回的 JSON 內容正常（`§06`、`原 HARD 被删除` 等均完好），非檔案損壞。
- 未修改 SPEC／parent／來源／receipt／程式；舊碼 `b2_ops_qrows.py` 5,680 B／`b9bad6a1…`、`b2_ops_tqaep.py` 5,863 B／`720477ba…`，與第 1 輪釘住值一致，確認未被改動。