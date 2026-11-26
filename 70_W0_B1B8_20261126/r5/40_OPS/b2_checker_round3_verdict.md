## 裁決

1. **PASS** — 以 `direct_parent_ref` 的 a..b 含第 b 行 LF 重算，1,465/1,465 全中（HARD 18/18、E00_TECH 8/8、TECH_ROUTE 54/54、Q_SOURCE_ROW 1,385/1,385）；例 B2.U0001 L93–116 → `07870b8e…`、B2.U0081 L751–751 → `c7c50c0e…`（`20_DEV/b2_reader/b2_ops_qrows2.py:99-112`；`40_OPS/b2_toolreadset_20261126T150645.json:136-141`）。
2. **PASS** — 用 pinned `b2_ops_qrows.py:43-46,76-79` 重算 `pin=source_payload[5]`，得 72 = HARD 16（pin 文字含 `UNBOUND`）+ E00_TECH 2（B2.U0023 `EFFECT_UNBOUND`、B2.U0026 `EXECUTOR_UNBOUND`）+ TECH_ROUTE 54（無第 6 欄）；54 全為 TECH_ROUTE（TR:94-110）。
3. **PARTIAL** — 聚合層已標 1,385 Q `VERBATIM_ONLY`、54 route N/A，且明說 `disagreement_count=0` 不是證據、Q4 `EVAL_ONLY=0`／`EVAL_ONLY` 在 Q1；但逐案 TQAEP 仍有 **371 個 Q 列** `requiredness_applicable=true`／`checked=true`／`agree=true`，用同一個 `source_payload[2]` 自比（`40_OPS/b2_tqaep_20261126T150657.json:4484-4490`；`b2_ops_tqaep2.py:44-51,108-132`），所以「1,385 全 VERBATIM_ONLY」在執行層未完全成立（TR:84-89）。
4. **PASS** — 已承認 `key_namespace_prefix` 與 `q_row.full_key` 共線，改以 disjoint `source_row` 區間 Q1 233–672／Q2 680–1192／Q3 1200–1577／Q4 1585–1638 佐證；我重算 440/513/378/54，四區間確互斥（TR:45-70）。
5. **PASS** — mutation 以 `{"key": tail}` 丟 namespace、`{"key":"WRONG-NS::"+tail}` 偽造 namespace，1,385/1,385 naive 都命中 1 列；`join_rows` 以 tail_index 拒絕而非只看 selector 形狀（`b2_semantics.py:290-312`；`b2_ops_tqaep2.py:152-175`；TQ:4524-4528）。但 tail_index 只取最後一段 `ROW=n`，見新增缺陷 7。
6. **PASS** — 18 HARD 中 9 列 §06 為 HARD-loss 的以單欄 `declared_requiredness=EVAL_ONLY` 執行（U0001、U0010、U0012–18），其餘 9 列（U0002–9、U0011）改判 `HOLD_SPEC_MUTATION_UNIMPLEMENTED`；TQAEP tally 9 PASS／9 HOLD（`b2_ops_tqaep2.py:177-191`；TQ:63-66；SPEC:44339-44373）。
7. **PASS** — 54 TECH_ROUTE 全改兩個單欄 arm（`declared=HARD`；`claimed_enable=True`），baseline 為 `None`，全部 `PASS_INTERPRETED` 而非 PASS（`b2_ops_tqaep2.py:192-206`；TQ:64-66；SPEC:44391-44497）。
8. **PASS** — `state_gate` 以 token 相等 + `EXCLUSIVE_PAIRS` 宣告式互斥判定，8/8 probe 全對，`INSTALLED+ENABLED` 與 `DEFER_NOFIT+NOT_SELECTED` 均為 `None`，非恆真（`b2_semantics.py:351-376`；`40_OPS/b2_gate_probe.json:4-84`）；E00 列數拆分另有問題，見新增必判。
9. **PARTIAL** — namespace 案已改 `baseline_rows`（TQ:4524），POS 也暴露 `requiredness_applicable`／`checked`／`agree`（TQ:4487-4490）；但 371 個 Q 列是 `true/true/true` 而非 `false/false/null`，型別修正只在 1,014 prose Q 與 54 route 生效（`b2_ops_tqaep2.py:44-51,108-132`）。
10. **PASS** — 463dcf33… 以 sha 解析到實際 `PHASE 01~04\藍圖\實質正文\SST_PLP_共用實質正文_工具合約_2026-11-23_r2.md`（767,859 B），1,385 Q 列全標 `CARRIER_SOURCE_REBOUND_BY_SHA` + `CANDIDATE_NOT_RATIFIED`（TR:142-143,2345-2350；`b2_ops_qrows2.py:121-133`）。

### 本輪新增必判

- **STATE_CONFLICT token 相等：PASS（機制）** — 8/8 probe 全對；`NOT_SELECTED` 單獨不再觸發，`SELECTED+NOT_SELECTED` 才觸發；`INSTALLED+ENABLED` 合法共存。gate 非恆真，且對 `SELECTED_OPTIONAL_DISABLED`／`SELECTED_DOCUMENT_ADAPTER` 不會因子字串誤判。惟互斥表是 Maker 宣告，不是 SPEC 宣告（`b2_semantics.py:210-216`；SPEC 全樹「互斥／exclusive」0 次；§06 只給 expected `STATE_CONFLICT`，SPEC:44375-44389）。
- **8 列 E00 拆分：PARTIAL** — 實際是 **3 列執行／5 列 HOLD**（U0022、U0023、U0026 執行；U0019–21 的 `SELECTED_OPTIONAL_DISABLED` 3 列 + U0024–25 的 `SELECTED_DOCUMENT_ADAPTER` 2 列 HOLD）。Maker 的「3 執行／2 HOLD」是**狀態種類數**，不是 8 列列數；`b2_gate_probe.py:77-79` 以 `e00_rows_*` 命名卻對 5 個 distinct states 計數（`b2_gate_probe.json:146-157`）。14 = 9 HARD + 5 E00 算術正確，5 列 HOLD 也沒有被硬塞關係；但「2 HOLD」的敘述不誠實。U0026 另依賴 Maker 宣告的 `REUSE_INTERNAL_DESIGN`／`SELECTED_DESIGN_ONLY`，見下。
- **HOLD_ORACLE：不判整個 gate `HOLD_ORACLE_UNBOUND`，但 U0026 所依賴的 pair 應判 `HOLD_ORACLE_UNBOUND`** — `SELECTED/NOT_SELECTED`、`INSTALLED/NOT_INSTALLED`、`ENABLED/DISABLED` 等有自然語義；`REUSE_INTERNAL_DESIGN`／`SELECTED_DESIGN_ONLY`（及 `DEFER_NOFIT`、`REFERENCE_ONLY` 對 `SELECTED_DESIGN_ONLY`）只在 `b2_semantics.py:213-215` 宣告，SPEC／母本沒有互斥表。若採 owner-bound 准入，U0026 應降為 HOLD，E00 變成 2 執行／6 HOLD，HOLD 總數由 14 升為 15。Oracle 應由 **E02／E05／PIPD design-selection owner** 提供；HARD／EVAL_ONLY 的互斥由 **R17／OriginalConsumer** 提供。

## 重算

**Candidate digest：可完全重現**

`c669fe557dfab826da5514dbe6b7aa28ff9ff6cc41fcc3580052ca82b696de05`（6 個 artefact bytes + sha256 全符；排序後 `<sha>  <path>`、LF 串接、無尾端 LF）。Freeze：`40_OPS/b2_candidate_freeze_round3.json:40`。

**Clause identity：1,465/1,465，非抽樣**

規則：parent `d95c8ac6…` 為 LF-only，取 lines a..b inclusive，含 b 行 LF。以下 20 個 unit 全部逐位元重算相等；其餘 1,445 個亦全算，0 反例。

| unit | kind | parent span | 我的 sha256 |
|---|---|---|---|
| B2.U0001 | HARD | L93–116 | `07870b8e9197a2de6e87c7e3a84f33862fe16101656d286e5f3197aeb3faee69` |
| B2.U0002 | HARD | L117–140 | `b5093c0250c58abdde44122fb3270795c22a136292e0d46de5fa7c08f013a3e7` |
| B2.U0003 | HARD | L141–164 | `25beda9dd3186b102548cd601f4fb82549d4d519530bebee88af95ffc3ccbc40` |
| B2.U0004 | HARD | L165–188 | `7808507be779ef807879fe03548eeb53be2985c0927145f7589ebe6d60bba37f` |
| B2.U0005 | HARD | L189–212 | `e8cb8f2d5639acd5ee597747a49d5dd3d13af38d73373e3a9bf5166f030a72c2` |
| B2.U0019 | E00_TECH | L525–545 | `bbf0de363874f0f6e261def3f5f85d9af3a7d6ae318f3509b4759c4f05787b42` |
| B2.U0020 | E00_TECH | L546–566 | `b30011eb8f81f3e2f04a19df5ccb2a32a3ead0ba078235407f64b548daf683d0` |
| B2.U0021 | E00_TECH | L567–587 | `b34a102545b4c5b282223db3d59e3bf963368c5d50d81ed2480676758dd14e9d` |
| B2.U0022 | E00_TECH | L588–608 | `5130a50de0ea3fd90e8316e8591a9f2c1db70900797962160622d6356d36c1a6` |
| B2.U0023 | E00_TECH | L609–629 | `efec9165b79f9e513057308508aac576270f8256e58fa31686d929f64bebcc7b` |
| B2.U0027 | TECH_ROUTE | L697–697 | `21aac4b70d4726c283698a125dad0daadbfd6f43436fd2ea7f3d5a2ffcf37b98` |
| B2.U0028 | TECH_ROUTE | L698–698 | `e33fe4c90d6a6c7048879f3daf523293c8c13132c18d051950b10c80975bbf94` |
| B2.U0029 | TECH_ROUTE | L699–699 | `e067b9e2b80ee498916899f6130cd472e362f25ce45f36c6ba3ac46dfd4c9963` |
| B2.U0030 | TECH_ROUTE | L700–700 | `a2d41f126a209fd8b6ec2a061277fbe622d8b7facaeec87e0c7522e91fda7132` |
| B2.U0031 | TECH_ROUTE | L701–701 | `3ff39feb149c73129b4e8fffabe4fb54e79c90530bdf808e5121c03de0244ccd` |
| B2.U0081 | Q_SOURCE_ROW | L751–751 | `c7c50c0e0943fe0d7b1cd621b5b5ba312e45be7f6f0e5fe1c490cae7f1a8dd6e` |
| B2.U0082 | Q_SOURCE_ROW | L752–752 | `2e2bddc51945a548b72fc6050a5c2419a63a504ca5f6c34f0369adc13f5aa62d` |
| B2.U0083 | Q_SOURCE_ROW | L753–753 | `bcb80263d15de82fed942d94982e6ef060c8fad68b661dacd71ce08e8bf816c7` |
| B2.U0084 | Q_SOURCE_ROW | L754–754 | `dcc6c3afc76d6c2e4630d05c6d66ee19abb70baa2573887964d0d0a50f476a04` |
| B2.U0085 | Q_SOURCE_ROW | L755–755 | `1910b48f46ccafbdc89fe5f0e46f07c5a7e6f2b35382aa21c5d3989fbd4742e9` |

**72 / 54 歷史重建**

| predicate | count | by kind |
|---|---:|---|
| `pin = source_payload[5]`；absent 或含 `UNBOUND` | **72** | HARD 16、E00_TECH 2、TECH_ROUTE 54 |
| `len(source_payload) <= 5` | **54** | TECH_ROUTE 54 |

E00 兩列：`B2.U0023` = `EFFECT_UNBOUND`；`B2.U0026` = `EXECUTOR_UNBOUND`。舊 `b2_ops_qrows.py` sha256 = `B9BAD6A1…`，未修改。

**Class 分布／2930 case**

- NEG：`NAMESPACE_JOIN_DENY 1,385` / `TOOL_REQUIREDNESS_HOLD 72` / `STATE_CONFLICT 8`。
- POS 1,465 + NEG 1,465 = **2,930** unique case ID；orphan = **0**、missing = **0**。
- 與 SPEC §06 的 2,930 列逐 ID 對齊；TQAEP `census` 亦為 1,385/72/8（TQ:44-60）。

**Requiredness 重算**

- Q_SOURCE_ROW 1,385：`requiredness_applicable=false` **1,014**、`true` **371**；`requiredness_checked=true` **371**、`agree=true` **371**。
- TECH_ROUTE 54：`false/false/null`。
- Q4 `EVAL_ONLY` = **0**；`EVAL_ONLY` 17 列全在 **Q1**。
- ToolReadSet 說 `verbatim_only_rows=1,385`（TR:86），但 TQAEP 逐案有 371 列 checked（TQ:4484-4490），兩者不一致。

**Pins**

- SPEC：8,016,371 B / `140de5bc1249dbb6e2d199dae336cf3a57741097aaf5cd883a7ec280e9199d3b`。
- Direct parent：2,712,933 B / `d95c8ac623112ac0bc2481a99cf19e368e661c5cbda2886d72599e29aa34fbf5`。
- Carrier：767,859 B / `463dcf33a668a9daa8f0bbf447c7dacc4c3d602bc53fa7e4866844ffbbc4b3e1`。
- 6 個 candidate artefact bytes + sha256 全符；舊 `b2_ops_qrows.py` 仍為 `B9BAD6A1…`。

**我額外重算的 provenance（供 B2_ACCEPTED 判斷）**

- Q_SOURCE_ROW：1,385/1,385 的 `full_key`、`source_row`、`carrier_line`、payload、`carrier_status` 與 carrier `463dcf33…` 的 L 行逐值相等。
- 非 Q：80/80 的 `source_payload` 與 `dd37a40b…` 的 original_source_ref 行逐欄相等。
- 但這是 checker 的重算；Maker 的 round-3 收據本身沒有做這個比較（TR:88 `original_source_comparisons: 0`）。

## B2_ACCEPTED

**NO。**

理由：

1. 這輪只把 claim 降到 `ROW_PAYLOAD_PROVENANCE_AND_CLAUSE_IDENTITY`，但沒有 product execution；parent `d95c8ac6…` 與 carrier `463dcf33…` 都仍是 `CANDIDATE_NOT_RATIFIED`。
2. Clause identity 1,465/1,465 成立；row payload 的 **pin integrity** 也成立；但「provenance」不是收據證明的：TR:88 明寫 `original_source_comparisons: 0`，收據只有 `payload_sha` 重算與 `q_row.payload == source_payload`，沒有對 `dd37`／`2cd8`／`463dcf` 逐值比對。**事實層**我獨立重算 1,465/1,465 為真，但**收據層**沒有證明，claim 標籤超額。
3. 逐案 requiredness 仍有 371 個 Q 列 `checked=true`／`agree=true` 的同一欄自比（TQ:4484-4490），與 `1,385 Q VERBATIM_ONLY` 的敘述衝突。
4. E00 是 3 執行／5 HOLD，不是 Maker 所述的 3 執行／2 HOLD；HARD 仍有 9/18 HOLD；54 route 是 `PASS_INTERPRETED` 而非原生 PASS。
5. 新增缺陷中的 `licence_state` 與 Q `pin_state` 會直接污染 B5 的 typed gaps。

**Maker claim 的超額點**

- `ROW_PAYLOAD_PROVENANCE`：收據只證明「與 SPEC 自身 `payload_sha` 一致」，不是「與原來源一致」；`original_source_comparisons=0`（TR:88）。若不加 1,465 次原來源比對，應降為 `ROW_PAYLOAD_PIN_INTEGRITY_AND_CLAUSE_SPAN_IDENTITY`。
- `claim_scope.supported` 列了 `STATE_CONFLICT`，但 8 列 E00 只有 3 列執行、5 列 HOLD（TQ:65）；若讀成 class-level supported，這是超額。`HARD_DELETION_MUTATION (9 of 18)` 有明示，較誠實；`STATE_CONFLICT` 沒有明示 3/8。
- `claim_scope.supported` 的 `ROW_PAYLOAD_AND_PROVENANCE_IDENTITY (per-unit payload_sha recomputation)` 把「hash 重算」直接等同「provenance」，是標籤錯誤。

## 新增缺陷

1. **HIGH — 371 個 Q 列仍被當成 requiredness checked**：`b2_ops_tqaep2.py:44-51,108-132` 只把 prose Q 設為不適用；token Q（18 HARD、209 OPTIONAL、17 EVAL_ONLY、1 REFERENCE_ONLY、126 DEFER_WITH_TRIGGER）仍 `applicable=true`、`checked=true`、`agree=true`，且 `requiredness_independent` 就是同一個 `source_payload[2]`。例 B2.U0081（TQ:4484-4490）。這直接違反 TR:84-86 的 `VERBATIM_ONLY`，也是第 3／9 項 PARTIAL 的原因。
2. **MEDIUM — E00 拆分數字不誠實**：`b2_gate_probe.py:77-79` 的 `e00_rows_with_declared_counterpart=3`、`e00_rows_hold_no_counterpart=2` 是 **distinct state** 數，不是 8 列列數；實際 3 列執行、5 列 HOLD（`b2_gate_probe.json:146-157`；TQ:65；SPEC:44375-44389）。14 的總數是 9+5 才對。
3. **HIGH（B5）— `licence_state` 把 `UNBOUND` 當成 DECLARED**：`b2_ops_qrows2.py:82-83` 的 regex 是 `MIT|Apache|BSD|proprietary|UNBOUND`；結果 808 列 DECLARED 中有 **737 列完全沒有 licence token**，只因 payload 別處出現 `UNBOUND`。實際有 licence token 僅 71 列、無 token 1,394 列；TR:132 的 `licence_unbound=657` 嚴重低估。
4. **MEDIUM（B5）— Q 列的 `pin_state` 不是 tool pin**：`b2_ops_qrows2.py:68-69` 對 Q_SOURCE_ROW 取 `source_payload[3]`（need/slot/scope 句），不是 pin。結果 629 列因句內含 `R17-NEED-UNBOUND` 被標 UNBOUND、53 列因提到 `Hermes v0.23.3` 被標 VERSION_SHAPED；TR:130 的 `pin_unbound=645` 混入了 Q need 文字，B5 不應直接當 tool pin 缺口使用。
5. **MEDIUM — provenance claim 超額**：TR:88 `original_source_comparisons=0`；TQ:14 卻把 `payload_sha` 重算寫成 `ROW_PAYLOAD_AND_PROVENANCE_IDENTITY`。我另行重算 1,465/1,465 為真，但 Maker 收據沒有這個證據。
6. **LOW — 兩個 receipt 的 prose 定義不一致**：TR:87 `prose_rows_n_a=864`，TQAEP 則是 1,014 個 Q `applicable=false`；差 150 = SOFT 41 + CONDITIONAL 109，因 `b2_semantics.py:204-206` 的 `REQ_TOKENS` 含 SOFT/CONDITIONAL，而 `b2_ops_tqaep2.py:39-41` 不含。兩份凍結件對同一母體給不同分母，應統一或明列詞彙。
7. **LOW — namespace oracle 仍不是完整 namespace resolver**：`b2_ops_tqaep2.py:88-92` 的 `q_index` 包含全部 1,465 units（不只 Q），`b2_semantics.py:301-311` 的 tail_index 只取最後一段 `ROW=n`。把 Q key 的 `::ROW=n` 去掉會解析到 HARD 的 B2.U0001，而不是 NAMESPACE_JOIN_DENY；naive 也只是 last-segment lookup。目前的 drop/forge mutation 會被抓到，但這個 hole 未關。
8. **LOW — POS 的 `pos_ok` 不含 clause identity**：`b2_ops_tqaep2.py:121` 只計 `pin_ok and mand_ok and req_ok and q_ok`；本輪 1,465 clause 全真所以無影響，但若 clause 重算失敗，POS 仍可能 PASS。

## 程序註記

- 題目給的 SPEC 路徑 `...\SST_PLP_PH01_B1-B8_執行控制小包\...` 不存在；實際檔名多了 `W0_`，在 `...\SST_PLP_PH01_W0_B1-B8_執行控制小包\SST_PLP_PH01_W0_B2_執行控制小包_實質正文_2026-11-26_r4_Native-first_HERMES_FINAL.md`。我以 raw sha256 `140de5bc…` 在 `【1】SST_PLP_PH01-04` 樹下定位，未改檔。
- 本機 Python 3.14 shim 指向不存在的 `hermes\tools\python-3.14.9...`，無法執行 Maker 的 Python；所有重算以 Node 26.12.1 唯讀實作（SHA-256、LF span、JSON parse、case table、gate tokenisation）完成。這是獨立重寫，不是呼叫 Maker 的程式。
- 我沒有寫入任何檔案；本裁決文字交由呼叫端以 `-o` 落盤。沒有安裝、網路、GUI 或交易。
- 已核對：6 個 candidate artefact bytes+sha、digest、SPEC/parent/carrier sha、舊 `b2_ops_qrows.py` sha、1,465 clause spans、1,465 payload pins、1,385 carrier 列、80 非 Q 列、2,930 case ID。`b2_parse.py` 未單獨執行；本次 10 項不依賴它。
- 限制：`b2_gate_probe.json` 是 Maker 自述 diagnostic，我另以 Node 重跑 8 個 probe 與額外 legal/illegal pairs；`b2_gate_probe.py` 的 `e00_rows_ok` 只檢查 status ∈ {OK, HOLD}，不是「3 列 OK」的斷言，故不能作為 E00 3/2 的證據。