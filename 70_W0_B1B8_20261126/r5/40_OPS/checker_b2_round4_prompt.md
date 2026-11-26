你是分離的 VERIFY / SECURITY Checker（唯讀）。你不修改任何檔案，只讀取並輸出裁決。

## 你的位置
Wave root：`C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/70_W0_B1B8_20261126`
你是 B2 的第 4 輪 Checker（前三輪凍結件已被取代，只判本輪）。第 1 輪 verdict 在 `40_OPS/b2_checker_round1_verdict.md`（已存在，請先讀）。
第 1 輪提出 10 項 Maker 缺陷；本輪候選已依該 10 項重做。你的工作是獨立重算並判定每一項是否成立，而不是接受 Maker 的敘述。

## 候選（凍結）
- `40_OPS/b2_candidate_freeze_round4.json`（candidate_digest 見該檔；規則：依 path 排序、`"<sha>  <path>"`、LF 串接、無尾端 LF、兩空格）
- 程式：`20_DEV/b2_reader/{b2_semantics.py,b2_parse.py,b2_ops_qrows2.py,b2_ops_tqaep2.py}`
- 收據：`40_OPS/b2_toolreadset_20261126T153100.json`、`40_OPS/b2_tqaep_20261126T153235.json`
- 上游 SPEC（唯讀，請以此為 oracle）：`C:/Projects/Agent_Workspace/知識庫/SQS/【1】SST_PLP_PH01-04/SST_PLP_PH01_W0_B0-B8/W0_B1-B8_NATIVE_FIRST_2026-11-26_r4_HERMES_FINAL/SST_PLP_PH01_B1-B8_執行控制小包/SST_PLP_PH01_W0_B2_執行控制小包_實質正文_2026-11-26_r4_Native-first_HERMES_FINAL.md`（若路徑不存在，請以 raw sha256 `140de5bc…` 在該樹下自行定位，不要改檔）

## 必判 10 項（逐項給 PASS / PARTIAL / FAIL 與證據行號）
1. **clause 身分**：第 1 輪判定 `direct_clause_sha` 可用 `direct_parent_ref` + 「a..b 含第 b 行 LF」重現。請自行以該規則重算至少 20 個不同 kind 的 unit（含 Q_SOURCE_ROW、HARD、E00_TECH、TECH_ROUTE），確認 1,465/1,465 是否真成立；若你算出不同結果，請給出反例 unit_id 與你的 sha。
2. **72 的歷史重建**：Maker 現主張 72 = HARD 16 + E00_TECH 2（欄 5 內含 `*_UNBOUND` 哨兵）+ TECH_ROUTE 54（無欄 5），並稱 54 = TECH_ROUTE。請用 SPEC + 被釘住的舊程式 `20_DEV/b2_reader/b2_ops_qrows.py`（未修改）獨立重算。
3. **requiredness**：1,385 Q 列是否已標 `VERBATIM_ONLY`、54 route 列標 N/A，且不再以 `disagreement_count=0` 當獨立證據？`Q4 EVAL_ONLY` 是否已改為「0 列、EVAL_ONLY 在 Q1」？
4. **象限**：是否已承認兩個 key 訊號共線，並改以 disjoint `source_row` 區間（Q1 233–672／Q2 680–1192／Q3 1200–1577／Q4 1585–1638）作為額外訊號？
5. **NAMESPACE_JOIN_DENY oracle**：mutation 是否真的動了 namespace 身分（丟掉 namespace／偽造 namespace），而非只改 selector 形狀？naive 實作是否確實會命中（非空轉）？
6. **HOLD mutation 保真**：18 HARD 中，§06 mutation 為 HARD-loss 的 9 列是否以單欄變異執行；其餘 9 列是否已改判 `HOLD_SPEC_MUTATION_UNIMPLEMENTED` 而非 PASS？
7. **54 TECH_ROUTE**：是否已改為兩個單欄 arm 且標 `PASS_INTERPRETED`（§06 未指名欄位），而非 PASS？
8. **STATE_CONFLICT**：是否以宣告式互斥關係判定，且有 `INSTALLED+ENABLED` 合法共存探針（使 gate 不是恆真）？
9. **報告型別**：namespace 案是否已改 `baseline_rows`；POS 是否已暴露 `requiredness_applicable`/`requiredness_checked`/`requiredness_agree=null`？
10. **carrier**：463dcf33…（`SST_PLP_共用實質正文_工具合約_2026-11-23_r2.md`，實際在 `PHASE 01~04\藍圖\實質正文\`）是否以 sha 解析並標 `CARRIER_SOURCE_REBOUND_BY_SHA`／`CANDIDATE_NOT_RATIFIED`？

## 本輪新增必判（round-3 的 8 個新缺陷，Maker 逐項處理）
1. **371 Q 列 requiredness 自比**：已改為全部 1,385 Q 列 `applicable=false/checked=false/agree=null`；僅 26 列（18 HARD＋8 E00）為 `true`。請核 POS 逐案。
2. **E00 拆分**：disposition 欄（sp[2]）為 state；只採 NATURAL 互斥（`EXCLUSIVE_PAIRS_NATURAL`），Maker 宣告的 `REUSE_INTERNAL_DESIGN/DEFER_NOFIT/REFERENCE_ONLY↔SELECTED_DESIGN_ONLY` 降為 `EXCLUSIVE_PAIRS_MAKER_DECLARED`，不再用於執行。請確認 **2 執行／6 HOLD_ORACLE_UNBOUND**（總 HOLD 15）與 oracle owner 標註。
3. **licence_state**：改為只認 `MIT|Apache|BSD|proprietary|GPL|MPL|ISC|PSF|Unlicense` 且加字母邊界（CJK 鄰接會讓 `` 失效）。請重算 DECLARED/TOKEN_ABSENT 並與你自己的 71 列比對，說明差異規則。
4. **Q 列 pin_state**：改 `NOT_EVALUATED_Q_ROW`＋`pin_gap`（sp[3] 是 need/slot 句，不是 pin）。請確認 B5 不再被污染。
5. **provenance claim**：已降為 `ROW_PAYLOAD_PIN_INTEGRITY_AND_CLAUSE_SPAN_IDENTITY`，並把原本來源比對降為 DIAGNOSTIC（coarse_rule_mismatches 明列）。請判此降級是否足夠。
6. **分母不一致**：`REQ_TOKENS` 統一為 `S.REQ_TOKENS`（含 SOFT/CONDITIONAL）。請核兩份收據的 prose 分母是否一致。
7. **namespace resolver**：`q_index` 只含 Q 列；非命中時以 `endswith` 判丟／偽 namespace，unknown key 回 `[]` 而非誤 DENY。請以非 Q key 與 unknown key 各驗一次（不得只驗 drop/forge）。
8. **POS 未含 clause**：`pos_ok` 已加 `clause_repro is not False`。

## 另外必答
- **STATE_CONFLICT 已改為 token 相等比對**（先前用 substring，`SELECTED` 是 `NOT_SELECTED` 的子字串 → 合法複合狀態被誤判）。請以 `20_DEV/b2_gate_probe.py` 的 8 個 probe 與 `40_OPS/b2_gate_probe.json` 檢驗：gate 是否仍非恆真、是否對 1,385 案以外的輸入也正確。
- **8 列 E00 拆為 3 執行 / 2 HOLD_NO_DECLARED_COUNTERPART**（`SELECTED_DOCUMENT_ADAPTER`、`SELECTED_OPTIONAL_DISABLED` 無宣告式互斥對象）→ 連同 9 列 HARD，`HOLD_SPEC_MUTATION_UNIMPLEMENTED` 共 14 列。請判此拆分是否誠實（不得為湊綠而發明關係）。
- Maker 自認這個 oracle 已用掉 4 次以上修補額度；若你認為仍不可靠，請直接判 `HOLD_ORACLE_UNBOUND` 並說明應由誰提供 oracle。

## 另外必答
- `candidate_digest` 是否可依規則完全重現？給出你的重算值。
- 2930 case：orphan / missing 是否為 0？class 分布是否仍 1385/72/8？
- 你認為 `B2_ACCEPTED` 是否成立？（Maker 主張「未成立、僅 claim `ROW_PAYLOAD_PROVENANCE_AND_CLAUSE_IDENTITY`」）若 Maker 的 claim 仍有超額，請指出。

## 邊界
- 唯一寫入 = 你的 verdict 檔（由呼叫端 `-o` 指定）。不得修改任何其他檔案。
- 不得執行任何安裝、網路、GUI、交易；純唯讀分析。
- 不確定就寫 UNKNOWN 並說明缺什麼，不要補值。

## 輸出格式
Markdown：`## 裁決`（每項一行 `1. PASS|PARTIAL|FAIL — 一句話 + 檔案:行號`）、`## 重算`（digest、clause、72/54、class 分布）、`## B2_ACCEPTED`（YES/NO + 理由）、`## 新增缺陷`（若有）、`## 程序註記`。
