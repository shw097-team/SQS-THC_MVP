## 裁決

### 第 1 輪 10 項（只判本輪凍結件）

1. **PASS** — 以 `direct_parent_ref` 的「a..b 含第 b 行 LF」規則重算 **1,465/1,465**（HARD 18/18、E00_TECH 8/8、TECH_ROUTE 54/54、Q_SOURCE_ROW 1,385/1,385），24 個跨 kind 樣本全中；例 B2.U0001 L93–116=`07870b8e…`、B2.U0081 L751=`c7c50c0e…`、B2.U0027 L697=`21aac4b7…`（`20_DEV/b2_reader/b2_ops_qrows2.py:112-120`、`b2_semantics.py:173-185`、`40_OPS/b2_toolreadset_20261126T153100.json:136-141`）。
2. **PASS** — 以被釘住舊碼 `pin=source_payload[5]` 重算 **72 = HARD 16 + E00_TECH 2（U0023 `EFFECT_UNBOUND`、U0026 `EXECUTOR_UNBOUND`）+ TECH_ROUTE 54（payload 只有 2 欄）**；`len(sp)<=5` 恰為 **54 route**（`20_DEV/b2_reader/b2_ops_qrows.py:76-79`、`b2_ops_qrows2.py:146-176`、TR:94-110）。
3. **PARTIAL** — 1,385 Q 已標 `VERBATIM_ONLY`、54 route 標 N/A、Q4 `EVAL_ONLY=0`（17 列在 Q1）都成立；但 **ToolReadSet 每列仍以同一欄自比並輸出 `requiredness_agree: true`（1,385 列）**，只有 TQAEP POS 改成 false/null（`b2_ops_qrows2.py:52-54`、`TR:72-90,2684` 對比 `b2_ops_tqaep2.py:42-52`、`TQ:4574-4577`）。
4. **PASS** — 已明說 key namespace 與 `q_row.full_key` 共線（full_key = key 去掉 `::ROW=n`），並列 disjoint `source_row` 233–672／680–1192／1200–1577／1585–1638；我重算 440/513/378/54 且四段不重疊（`TR:33-70`、`b2_ops_qrows2.py:202-216`、`b2_semantics.py:272-291`）。
5. **PASS** — mutation 真正用 `{"key": tail}`（丟 namespace）與 `{"key":"WRONG-NS::"+tail}`（偽造 namespace）；1,385/1,385 baseline=1、naive=1、兩者皆 `NAMESPACE_JOIN_DENY`，非空轉；80 個非 Q key 全回 `[]`（`b2_semantics.py:294-330`、`b2_ops_tqaep2.py:160-190`、`TQ:4612`）。
6. **PASS** — 18 HARD 中 9 列（U0001、U0010、U0012–U0018）以單欄 `declared_requiredness=EVAL_ONLY` 執行，baseline=None；其餘 9 列改判 `HOLD_SPEC_MUTATION_UNIMPLEMENTED`，不再 PASS（`b2_ops_tqaep2.py:208-230`、`TQ:71-76`）。
7. **PASS** — 54 route 已拆成 `declared=HARD` 與 `claimed_enable=True` 兩個單欄 arm，baseline=None，全部標 `PASS_INTERPRETED` 而非 PASS（`b2_ops_tqaep2.py:232-244`、`TQ:1261`）。
8. **PASS** — `state_gate` 改 token 相等＋靜態互斥表；`INSTALLED+ENABLED`、`DEFER_NOFIT+NOT_SELECTED` 均為 None，`HARD+EVAL_ONLY` 才是 CONFLICT（`b2_semantics.py:213-220,337-376`、`40_OPS/b2_gate_probe.json:4-84`）。
9. **PASS** — namespace 案已用 `baseline_rows=1`；POS 每列有 `requiredness_applicable/requiredness_checked`，Q 列 `requiredness_agree=null`（`b2_ops_tqaep2.py:194`、`TQ:4612,4574-4577`）。
10. **PASS** — 463dcf33… 以 sha 解析到 `PHASE 01~04\藍圖\實質正文\…_2026-11-23_r2.md`（767,859 B）；1,385 Q 全部 `CARRIER_SOURCE_REBOUND_BY_SHA`＋`CANDIDATE_NOT_RATIFIED`，declared path 仍為 `PHASE 00~04`（`b2_ops_qrows2.py:121-133`、`TR:142-143`）。

### 本輪新增 8 項

1. **PASS** — POS 實測 1,385 Q 全為 `applicable=false/checked=false/agree=null`，只有 18 HARD＋8 E00 為 true（共 26）；U0081 為 false/null（`b2_ops_tqaep2.py:42-52`、`TQ:4574-4577`）。
2. **PASS** — E00 以 sp[2] 為 state，只走 NATURAL；實測 **2 PASS（U0022、U0023）／6 HOLD_ORACLE_UNBOUND（U0019、U0020、U0021、U0024、U0025、U0026）**，6 列皆有 `oracle_owner`，總 HOLD=15（`b2_ops_tqaep2.py:247-280`、`TQ:891`、`b2_gate_probe.json:153-155`）。
3. **PARTIAL** — 新 regex 的字母邊界確實修掉 substring 誤判（我重算 7 DECLARED，與收據一致），但其中 **U0087/U0527 的 `Apache` 是工具名「Apache Arrow」，不是 licence**；真正 licence 只有 5 個 MIT（`b2_ops_qrows2.py:88-91`、`TR:2695,23815`）。
4. **PASS** — Q 列全部 `NOT_EVALUATED_Q_ROW`＋`pin_gap`（1,385/1,385），`pin_unbound` 只剩 16 HARD，B5 的 typed gap 不再吃 Q 的 need/slot 句（`b2_ops_qrows2.py:78-79`、`TR:2404,129-133`）。
5. **PARTIAL** — TQAEP 降為 `ROW_PAYLOAD_PIN_INTEGRITY_AND_CLAUSE_SPAN_IDENTITY` 本身誠實；但 **freeze 仍寫 `ROW_PAYLOAD_PROVENANCE_AND_CLAUSE_IDENTITY`**，且 ToolReadSet 的 `original_source_comparisons=0`，TQAEP 診斷只比 1,385 Q（80 個非 Q 被 `parse_ref` 的 PARENT kind 跳過）（`40_OPS/b2_candidate_freeze_round4.json:42`、`TQ:11,39-46`、`b2_ops_tqaep2.py:147-152`、`TR:88`）。
6. **PASS** — `REQ_TOKENS` 已統一為 `S.REQ_TOKENS`（含 SOFT/CONDITIONAL）；TR prose 864＋SOFT 41＋CONDITIONAL 109 = 舊 1,014，兩份收據不矛盾（`b2_semantics.py:204-207`、`b2_ops_qrows2.py:239`、`TR:87`）。
7. **PASS** — `q_index` 只收 Q 列；非 Q key 80/80 回 `[]`、unknown key 回 `[]`、drop/forge 全 DENY（`b2_ops_tqaep2.py:88-100`、`b2_semantics.py:294-330`）。
8. **PASS** — `pos_ok` 已含 `clause_repro is not False`，1,465 POS 全部 `REPRODUCED`（`b2_ops_tqaep2.py:157`、TQ POS `clause_identity`）。

### 另外必答

- **STATE_CONFLICT probe**：8/8 與 `b2_gate_probe.json` 一致，gate 非恆真；我另測 `SELECTED` 單獨、`NOT_SELECTED` 單獨、`SELECTED_OPTIONAL_DISABLED`、`INSTALLED+NOT_INSTALLED_NOT_BOUND` 等，未見誤報。殘留：`state_gate` 的 `EXCLUSIVE_PAIRS` 仍含 3 個 Maker-declared pair，probe 的 8 案中有 2 案靠它們；執行路徑（`contradicting_state`）只用 NATURAL，故不影響 E00 2 案，但 `exclusive_pairs_declared` 字樣會誤導（`b2_semantics.py:217-220`、`b2_gate_probe.json:85`）。
- **E00 3 執行／2 HOLD／14**：實測是 **2 執行／6 HOLD／15**；若 Maker 對外仍稱 3/2/14，該敘述與凍結收據不符。收據的 2/6 本身誠實，沒有為湊綠發明關係（U0026 已因只有 Maker-declared pair 而轉 HOLD）。
- **HOLD_ORACLE_UNBOUND**：我不判整個 gate 為 HOLD；namespace 1,385/1,385 已真綁定，token state gate 也結構正確。但 **54 route 是 Maker 解釋、9 HARD 未實作、6 E00 未綁定**；若要作為 B2 acceptance，應由 **R17/OriginalConsumer**（HARD requiredness）、**原 tool/disposition owner**（54 route）、**E02/E05/PIPD**（E00）提供 oracle，否則這 69 案只能算 diagnostic。
- **candidate_digest**：可完全重現，**`1dabe8cf59bbd2807f690fd1125291afc0bd845d97e09811d745e73286bd7b2b`**。
- **2930 case**：orphan=0、missing=0；POS 1,465＋NEG 1,465；NEG class **1,385/72/8**。
- **B2_ACCEPTED**：**NO**（理由見下）。

## 重算

| 項目 | 我的獨立重算 |
|---|---|
| candidate_digest | `1dabe8cf59bbd2807f690fd1125291afc0bd845d97e09811d745e73286bd7b2b`；6/6 artefact bytes+sha256 全中 |
| clause | **1,465/1,465**，全部命中 `RAW_WITH_TERMINATOR`（a..b 含 line-b LF）；HARD 18、E00 8、route 54、Q 1,385 全數 |
| clause 樣本 | U0001 L93–116 `07870b8e9197a2de…`；U0019 L525–545 `bbf0de363874f0f6…`；U0027 L697 `21aac4b70d4726c2…`；U0081 L751 `c7c50c0e0943fe0d…` |
| 72 | **HARD 16 + E00_TECH 2 + TECH_ROUTE 54 = 72** |
| 54 | **54 = TECH_ROUTE 全部**（payload len=2，無第 6 欄）；舊碼 sha `b9bad6a1…` 未變 |
| class | NEG **1,385 NAMESPACE_JOIN_DENY / 72 TOOL_REQUIREDNESS_HOLD / 8 STATE_CONFLICT**；case 2,930 unique，orphan 0、missing 0 |
| quadrant | 440/513/378/54；source_row 233–672／680–1192／1200–1577／1585–1638，四段 disjoint |
| licence | regex 得 7 DECLARED；真正 licence **5（MIT）**，U0087/U0527 為「Apache Arrow」產品名誤判 |
| pins | SPEC 8,016,371 B / `140de5bc…`；parent 2,712,933 B / `d95c8ac6…`；carrier 767,859 B / `463dcf33…` |
| payload | payload_sha **1,465/1,465**；payload provenance 對 evidence/original 逐列 exact **1,465/1,465**（Q 1,385 對 evidence 行；非 Q 80 對 dd37a40b span） |
| Q evidence_line | `q_row.evidence_line` 全部比 `original_source_ref` 行號多 **664**（U0081: 1643 vs 979），不可作為 evidence 定位 |

## B2_ACCEPTED

**NO。**

1. **沒有 product execution**；`fin_order=DENY`，parent `d95c8ac6…` 與 carrier `463dcf33…` 仍為 `CANDIDATE_NOT_RATIFIED`。
2. **69/1,465 個 NEG 沒有照 §06 執行**：9 HARD `HOLD_SPEC_MUTATION_UNIMPLEMENTED`、6 E00 `HOLD_ORACLE_UNBOUND`、54 route `PASS_INTERPRETED`（Maker 解釋）；E00 只有 2/8 真執行。
3. **Q requiredness 仍非獨立檢查**（1,385 VERBATIM_ONLY；26 列只是同一 unit 的 cross-field），不能把 `disagreement_count=0` 當 requiredness 證據。
4. **freeze 的 claim ceiling 與 TQAEP 不一致**：freeze 寫 `ROW_PAYLOAD_PROVENANCE_AND_CLAUSE_IDENTITY`，TQAEP 只敢寫 `ROW_PAYLOAD_PIN_INTEGRITY_AND_CLAUSE_SPAN_IDENTITY`；且 ToolReadSet 自己是 `original_source_comparisons: 0`。
5. 仍有數個報告級缺陷（licence 假陽性、`clean_no_version_count` 混入 Q、非 Q provenance 被靜默跳過、TR 每列 `requiredness_agree=true`、`evidence_line` 偏移 664），不足以支撐 acceptance。
6. 正面：digest、pins、clause 1,465/1,465、payload 1,465/1,465、namespace 1,385/1,385、case census 都真實且乾淨，足以支撐較窄的 claim。

**Maker claim 的超額**：`PROVENANCE` 在本收據沒有證據鏈（雖然我用 checker 獨立重算確實 1,465/1,465 exact），`CLAUSE_IDENTITY` 實際只是 line-span/SHA identity，不是語意 clause identity；若 claim 要以凍結收據為依據，兩者都超出；若以 checker 證據為依據，provenance 可成立，但 freeze 必須改成與 TQAEP 相同或明列 checker 證據。freeze 的 `not_claimed` 也漏列 6 個 E00 HOLD。

## 新增缺陷

1. **[HIGH] freeze 與 TQAEP claim ceiling 互相矛盾**：freeze `ROW_PAYLOAD_PROVENANCE_AND_CLAUSE_IDENTITY`（`40_OPS/b2_candidate_freeze_round4.json:42`）vs TQAEP `ROW_PAYLOAD_PIN_INTEGRITY_AND_CLAUSE_SPAN_IDENTITY`（`TQ:11`），且 freeze `not_claimed` 未列 6 個 E00 HOLD（`:48-54`）。
2. **[HIGH] TQAEP provenance 診斷靜默漏掉 80 個非 Q 列**：規則寫「others: dd37a40b span」（`TQ:40`），但 `parse_ref` 對 `PARENT@…` 回 kind=`PARENT`（`b2_semantics.py:188-195`），程式只收 `kind=="FILE"`（`b2_ops_tqaep2.py:147-152`），所以 `compared=1385` 而非 1,465；我另行檢查 80/80 非 Q 其實 exact，但收據沒有證明。
3. **[MEDIUM] licence 假陽性**：U0087/U0527 的 `Apache` 來自工具名「Apache Arrow」，被記為 `DECLARED`（`b2_ops_qrows2.py:88-91`、`TR:2695,23815`）；真正 licence 只有 5 個 MIT。另 `licence_unbound=0` 是死指標（`licence_state` 永遠不會是 UNBOUND，`TR:132`），B5 可能誤讀成 licence 全部已解。
4. **[MEDIUM] ToolReadSet 仍保留 Q 列自比**：`requiredness_agree = req_row == req_ind`（`b2_ops_qrows2.py:54`），兩邊都取 `source_payload[2]`，1,385 列為 true（`TR:2684`）；雖然 `check_mode` 有 VERBATIM_ONLY 註記（`TR:80-89`），機器可讀欄位仍與 TQAEP 的 false/null 相反。
5. **[MEDIUM] `clean_no_version_count=1460` 混入 NOT_EVALUATED Q**：by_kind 含 `Q_SOURCE_ROW: 1385`（`TR:112-120`），語意上是「NOT_EVALUATED_Q_ROW」卻被算成「no version」，與 `pin_gap` 的「B5 must not read」相衝突；B5 若讀這個 scalar 會被污染。
6. **[MEDIUM] 敘述與收據不一致**：對外稱 E00 3 執行/2 HOLD、HOLD_SPEC_MUTATION_UNIMPLEMENTED 共 14；收據實際 2 執行/6 HOLD、共 15（`TQ:71-76`）。收據本身是對的，錯的是敘述。
7. **[LOW] `source_row_ranges_disjoint: true` 是硬編碼**（`b2_ops_qrows2.py:216`），不是由 ranges 計算；本輪值恰好為真，但這是不可回歸的宣告。
8. **[LOW] `state_gate` 仍把 3 個 Maker-declared pair 放進 `EXCLUSIVE_PAIRS`**（`b2_semantics.py:217-220`），gate probe 的 8/8 有 2 案靠它們；`exclusive_pairs_declared` 未區分 NATURAL/MAKER（`b2_gate_probe.json:85`）。token 相等也仍漏 `INSTALLED` vs `NOT_INSTALLED_NOT_BOUND` 這種複合 token。
9. **[UPSTREAM] SPEC §06 自相矛盾**：9 個 HARD NEG 的 mutation 文字寫 `ABI_UNBOUND`、`MAKER_SELF_ATTEST`、`PIT_LOOKAHEAD` 等，但 expected 欄仍是 `TOOL_REQUIREDNESS_HOLD`；Maker 只能 HOLD，應由 Owner 修 §06 或改名 expected。
10. **[UPSTREAM] `q_row.evidence_line` 全體偏移 +664**（1,385/1,385；U0081 寫 1643、實際 evidence 行 979）；本輪收據沒有使用它，但任何下游用它定位都會指到錯列。另 `direct_parent_ref`/carrier 的 stale path 仍是 Owner amendment。

## 程序註記

- 只讀分析：未修改任何檔案，未執行安裝、網路、GUI、交易；未執行 Maker 會寫收據的 Python 腳本（`b2_ops_qrows2.py`、`b2_ops_tqaep2.py`、`b2_gate_probe.py`），而是以 Node 24.19.0 的 `fs`/`crypto` 重實作 predicate 後對凍結收據核對。
- Python shim 指向不存在的 `C:\Users\user\AppData\Local\hermes\tools\python-3.14.9+20261021-win32-x64\python.exe`，`py` 也找不到安裝；因此本輪沒有 Python 執行結果可引用。
- 題目給的 SPEC 路徑 `SST_PLP_PH01_B1-B8_執行控制小包\…` 少 `W0_`，實際檔在 `SST_PLP_PH01_W0_B1-B8_執行控制小包\…`；我以 raw sha256 `140de5bc…` 解析，未改檔。
- Parent `d95c8ac6…` 實際在 `W0_B0-B8\藍圖\SST_PLP_PH01_W0_B0-B8_藍圖\…`，carrier `463dcf33…` 在 `PHASE 01~04\藍圖\實質正文\…`；兩者皆 `CANDIDATE_NOT_RATIFIED`。
- 舊程式 `20_DEV/b2_reader/b2_ops_qrows.py` 仍為 5,680 B / `b9bad6a1…`，與第 1 輪釘住值一致。
- 本輪 verdict 只代表此凍結 digest `1dabe8cf…`；若 Maker 再改任何 pinned artefact，須重新 freeze 與重算。
