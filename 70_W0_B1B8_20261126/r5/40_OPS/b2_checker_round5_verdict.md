## 裁決

### 第 1 輪 10 項

1. **PASS** — 以 `direct_parent_ref` 的 a..b（含第 b 行 LF）獨立重算 **1,465/1,465**（HARD 18/18、E00 8/8、ROUTE 54/54、Q 1,385/1,385）；例 U0001 L93–116=`07870b8e…`、U0019 L525–545=`bbf0de36…`、U0027 L697=`21aac4b7…`、U0081 L751=`c7c50c0e…`（`20_DEV/b2_reader/b2_ops_qrows2.py:115-126`、`b2_semantics.py:173-185`、`40_OPS/b2_toolreadset_20261126T154724.json:137-145`）。
2. **PASS** — 用 SPEC 與未修改的舊程式 `pin:=sp[5]` 重算 **72 = HARD 16 + E00_TECH 2（U0023 `EFFECT_UNBOUND`／U0026 `EXECUTOR_UNBOUND`）+ TECH_ROUTE 54**；**54 = TECH_ROUTE 恰等**（`b2_ops_qrows.py:43,76-79`；`b2_ops_qrows2.py:152-173`；TRS:95-111）。
3. **PASS** — 1,385 Q 全標 `VERBATIM_ONLY`、54 route 標 `N/A_ROUTE`、僅 26 列 applicable/agree=true；`disagreement_count=0` 已明示「不得當證據」；Q4 `EVAL_ONLY`=0、17 列全在 Q1（TRS:72-90；TQ:20,24）。
4. **PASS** — 已承認 key prefix 與 `q_row.full_key` 共線，另以 disjoint ranges 233–672／680–1192／1200–1577／1585–1638 佐證；`source_row_ranges_disjoint` 由 ranges 計算（TRS:47-70；`b2_ops_qrows2.py:213-238`）。
5. **PASS** — mutation 真的丟／偽 namespace（`{"key": tail}`、`{"key":"WRONG-NS::"+tail}`）；1,385/1,385 baseline_rows=1、naive=1、兩者皆 `NAMESPACE_JOIN_DENY`（`b2_semantics.py:294-321`；`b2_ops_tqaep2.py:189-211`）。註：`b2_gate_probe.py` 的 naive 以 full key 自比，該 probe 空轉（見新 8）。
6. **PASS** — 18 HARD 中 9 列（U0001/U0010/U0012–U0018）以單欄 `EVAL_ONLY` 執行、baseline=None；其餘 9 列（U0002–U0009/U0011）改判 `HOLD_SPEC_MUTATION_UNIMPLEMENTED`，未 PASS（`b2_ops_tqaep2.py:208-230`；TQ:71-76）。
7. **PASS** — 54 route 改兩個單欄 arm（declared=HARD；claimed_enable=True），baseline=None，判 `PASS_INTERPRETED` 而非 PASS（`b2_ops_tqaep2.py:232-243`）。
8. **PASS** — `state_gate` 已改 token 相等；`INSTALLED+ENABLED`、`DEFER_NOFIT+NOT_SELECTED` 為 None，`HARD+EVAL_ONLY` 為 CONFLICT，故非恆真（`b2_semantics.py:213-220,358-380`；`b2_gate_probe.json:4-62`）。保留：`state_gate` 仍 OR 三個 Maker pair（見新 8）。
9. **PASS** — namespace 案已用 `baseline_rows`；POS 已曝 `requiredness_applicable`／`requiredness_checked`／`requiredness_agree`（Q 與 route 為 null，26 列 true）（`b2_ops_tqaep2.py:158-168,194`）。
10. **PASS** — carrier `463dcf33…` 以 sha 重綁（767,859 B）；1,385/1,385 標 `CARRIER_SOURCE_REBOUND_BY_SHA`／`CANDIDATE_NOT_RATIFIED`，並標 declared path 的 `PHASE 00~04` stale segment（`b2_ops_qrows2.py:134-149`；TRS:2589…）。

### Round-4 新增 10 項

11. **PARTIAL** — `claim_ceiling` 與 TQAEP 完全相同、`neg_holds` 9/6 正確；但 `not_claimed` 是 7 行（多 `"B2 acceptance/completion"`），非 TQAEP 的 6 行；6 個 E00 HOLD 只出現在 `neg_holds`，未在 `not_claimed` 文句（`20_DEV/make_b2_freeze.py:42-59`；freeze:42,48-60）。
12. **PASS** — provenance 診斷已接受任何 `sha==dd37a40b…` 的 ref（含 `PARENT@`），`compared=1465`（1,385 Q + 80 non-Q），非 1,385（`b2_ops_tqaep2.py:147-152`；TQ:39-45）。
13. **PARTIAL** — licence 三態正確：DECLARED 5（MIT）／TOOL_NAME_ONLY 2（U0087/U0527 Apache Arrow）／TOKEN_ABSENT 1,458；但 `licence_unbound` 死指標未移除，仍輸出 0（`b2_ops_qrows2.py:88-99,272`；TRS:133）。
14. **PASS** — TRS 1,385 Q 全 `agree=null`、`applicable=false`、`check_mode=VERBATIM_ONLY`；僅 26 列 true，與 TQAEP 26 一致（`b2_ops_qrows2.py:52-54`；TRS:80,87；TQ:94…）。
15. **PARTIAL** — 結構欄 `clean_no_version_count.measured=75`（16 HARD+5 E00+54 route）正確；但 `conclusion` 仍寫 **1460**、`per_row_state_vs_old.B_no_version=1460**，與 75 自相矛盾（`b2_ops_qrows2.py:174-190`；TRS:113-127）。
16. **FAIL** — 對外敘述不一致：session closeout r2 line 14 正確寫 1,396/54/9/6/0、2/6/15，但 line 59 仍寫 **1,397 PASS + 54 + 14 HOLD_SPEC**、line 61 寫 **1,407**、line 65 寫 **8 state probe／3 列 E00／5 namespace probe**；收據與 probe 實為 1,396/9/6、75、7/2/3（`60_CLOSEOUT/SST_PLP_PH01_W0_B1B8_SESSION_CLOSEOUT_HANDOFF_2026-11-26_r2.md:14,59,61,65`；TQ:71-76；TRS:113；`b2_gate_probe.json`）。
17. **PASS** — `source_row_ranges_disjoint` 確由 ranges 的 min/max 重算（lambda），非硬編碼；值與實算一致（`b2_ops_qrows2.py:227-238`；TRS:68）。
18. **FAIL** — probe 仍把 Maker pair 當 gate 證據：`b2_gate_probe.json:54-61` 對 `SELECTED_DESIGN_ONLY+REFERENCE_ONLY` 期待 `STATE_CONFLICT`，而 line 105 卻把同 pair 列為 `not_used_for_cases`；`state_gate` 也仍 OR `EXCLUSIVE_PAIRS = NATURAL + MAKER`（`b2_semantics.py:220,372-380`）。另 state probe 實為 7 個（非 8）；namespace naive 以 full key 自比，`naive_matches=1` 為空轉（`b2_gate_probe.py:55-58`；json:148-165）。
19. **PASS** — SPEC §06 上游衝突（9 個 HARD NEG mutation 指名 `ABI_UNBOUND`／`MAKER_SELF_ATTEST`／`PIT_LOOKAHEAD` 等，expected 卻是 `TOOL_REQUIREDNESS_HOLD`）已列 TT-UP-1；Maker 不改 SPEC、以 HOLD 處理（session r2:57；SPEC §06；TQ:73-75）。
20. **PASS** — `q_row.evidence_line` 上游 +664 已列 TT-UP-2；我實算 1,385/1,385 `evidence_line − original_source_ref = 664`（U0081 1643−979=664），且 `20_DEV` 無任何 `evidence_line` 引用（session r2:81；`20_DEV` grep 無命中）。

### 另外必答

- **STATE_CONFLICT token 相等**：非恆真（單 state、`INSTALLED+ENABLED`、`DEFER_NOFIT+NOT_SELECTED` 均 None）；但「對 1,385 案以外也正確」**不成立**：把 `INSTALLED=UNVERIFIED,BOUND=UNBOUND` 這種合法的屬性複合字串餵入會因 BOUND/UNBOUND 兩 token 並存而誤報 `STATE_CONFLICT`；且 `SELECTED_DESIGN_ONLY+REFERENCE_ONLY` 只靠 Maker pair 才成立。故為 PARTIAL。
- **8 列 E00 的 3 執行／2 HOLD 拆分**：**與實作不符**。實作是 **2 執行（U0022/U0023）/ 6 HOLD_ORACLE_UNBOUND（U0019/U0020/U0021/U0024/U0025/U0026）**；9 HARD + 6 E00 = **15 HOLD**，不是 14。這個 2/6 拆分本身**誠實**（未為湊綠發明 Maker pair；`SELECTED_OPTIONAL_DISABLED` 3 列、`SELECTED_DOCUMENT_ADAPTER` 2 列、`REUSE_INTERNAL_DESIGN` 1 列都留在 HOLD），但 3/2/14 的外部敘述是錯的。
- **HOLD_ORACLE_UNBOUND**：E00 的 2 個 PASS 可保留（`NOT_SELECTED → SELECTED` 是自然互斥）；6 個 HOLD 正確。**不要**為把 `SELECTED_OPTIONAL_DISABLED` 拉成 PASS 而拆解複合 token，也不要使用 `EXCLUSIVE_PAIRS_MAKER_DECLARED`。若 Maker 要把 `state_gate` 當通用 oracle，則在 SPEC 宣告前應整體維持 `HOLD_ORACLE_UNBOUND`；oracle 應由 **E02/E05/PIPD design-selection owner** 提供設計選擇互斥關係，HARD requiredness 類由 **R17/OriginalConsumer** 提供。
- **candidate_digest**：可完全重現，重算值 **`c7a12bcc9f312b700502c13f25ac0c08b2f5c9975bdc4a9db369cad8490c2800`**（6/6 artefact bytes+sha256 全對）。
- **2,930 case**：orphan=0、missing=0；2,930 unique；NEG class **1,385 / 72 / 8**；POS 1,465、NEG 1,465。
- **B2_ACCEPTED**：**NO**（詳下）。

## 重算

| 項目 | 我的獨立結果 |
|---|---|
| candidate_digest | `c7a12bcc9f312b700502c13f25ac0c08b2f5c9975bdc4a9db369cad8490c2800`（與 freeze 完全一致） |
| artefact pins | 6/6 bytes + raw sha256 全對 |
| SPEC | 8,016,371 B / `140de5bc…` 完全一致 |
| parent | 2,712,933 B / `d95c8ac6…` 完全一致 |
| clause | **1,465/1,465**；HARD 18、E00 8、ROUTE 54、Q 1,385；U0001 L93–116=`07870b8e…`、U0019 L525–545=`bbf0de36…`、U0027 L697=`21aac4b7…`、U0081 L751=`c7c50c0e…` |
| 72 | **HARD 16 + E00_TECH 2 + TECH_ROUTE 54 = 72**（舊 predicate `pin:=sp[5]`，舊程式 sha `b9bad6a1…`/5,680 B） |
| 54 | **TECH_ROUTE 54/54**（`len(sp)<=5`） |
| payload | 1,465/1,465 `payload_sha` 重算一致 |
| class | **NAMESPACE_JOIN_DENY 1,385 / TOOL_REQUIREDNESS_HOLD 72 / STATE_CONFLICT 8** |
| 象限 | 440／513／378／54；ranges Q1 233–672、Q2 680–1192、Q3 1200–1577、Q4 1585–1638，全 disjoint |
| E00 NEG | 2 PASS（U0022/U0023）、6 HOLD_ORACLE_UNBOUND；HARD NEG 9 PASS + 9 HOLD_SPEC；route 54 PASS_INTERPRETED |
| licence | DECLARED 5（MIT）／TOOL_NAME_ONLY 2／TOKEN_ABSENT 1,458 |
| clean no-version | 結構欄 75（16+5+54）；但 `conclusion` 仍寫 1460 |
| probe | 7 state cases / 5 distinct E00 states / 3 namespace probes；probe naive 空轉 |

## B2_ACCEPTED

**NO。**

- 無任何 product case 執行；`fin_order=DENY`、`write_set=[]`；2,930 案是 SPEC 的 POS/NEG case，不是產品執行。
- 仍有 **15 個 HOLD**：9 HARD `HOLD_SPEC_MUTATION_UNIMPLEMENTED` + 6 E00 `HOLD_ORACLE_UNBOUND`。
- `d95c8ac6…` parent 與 `463dcf33…` carrier 仍是 `CANDIDATE_NOT_RATIFIED`；Owner D-5 追認未完成。
- Q requiredness 1,385 列仍是 `VERBATIM_ONLY`，不是獨立 requiredness。
- pin/licence/lock/B5 selection 仍屬 B5 職責。
- Maker 的實際 claim ceiling 是 `ROW_PAYLOAD_PIN_INTEGRITY_AND_CLAUSE_SPAN_IDENTITY`（比 prompt 所述的 `PROVENANCE` 更窄）；這個 ceiling 本身可支持，但 **`claim_scope.supported` 另外列了 5 項超出 ceiling 的 claim**（QUADRANT_CENSUS、CASE_CENSUS_2930、CLASS_MUTATION_NS_JOIN、HARD_DELETION_MUTATION、STATE_CONFLICT），屬 claim 帳務超額；再加上 closeout 的 1,397/14/1,407/8 等錯誤數字，不能給 acceptance。

## 新增缺陷

1. **[HIGH] 對外敘述與收據不一致**：session closeout r2 line 59 的 `1,397 PASS + 54 + 14 HOLD_SPEC`、line 61 的 `1,407`、line 65 的 `8 state probe／3 列 E00／5 namespace probe` 全部與 TQAEP/TRS/probe 不符（實為 1,396 + 9 + 6、75、7/2/3）。line 14 雖已改對，但同一文件自相矛盾。`60_CLOSEOUT/...r2.md:14,59,61,65`。
2. **[HIGH] Maker-declared pairs 仍進入 gate**：`EXCLUSIVE_PAIRS = NATURAL + MAKER`（`b2_semantics.py:220`），且 `b2_gate_probe.json:54-61` 以 `SELECTED_DESIGN_ONLY+REFERENCE_ONLY` 期待 `STATE_CONFLICT`；同檔 line 105 卻稱該 pair「not used for cases」。這使「Maker pair 不用於執行」的邊界只在 `contradicting_state` 成立，不在 `state_gate` 成立。應把 `state_gate` 的執行關係限為 NATURAL，或把該 probe 案標為非 gate。
3. **[MEDIUM] `licence_unbound` 死指標未移除**：`b2_ops_qrows2.py:272` 仍輸出，TRS:133 仍是 0；與 prompt「已移除」不符。
4. **[MEDIUM] clean no-version 文字與數值矛盾**：`measured=75`（TRS:114）但 `conclusion` 寫 1460（TRS:122）、`B_no_version=1460`（TRS:125）；code 在 `b2_ops_qrows2.py:184` 使用 `len(clean_no_version)`（含 Q）而非 75。
5. **[MEDIUM] probe 的 E00/namespace 診斷誤導**：`e00_rows` 以 state 為 key，只列 5 個 state，卻用 `e00_rows_with_declared_counterpart=2`／`hold=3` 的「rows」名稱（實際 2 PASS/6 HOLD rows）；namespace `naive_matches` 以 full key 自比，不能證明 tail-only 實作會命中（`b2_gate_probe.py:36-45,55-58`；json:146-165）。
6. **[LOW] stale docstrings**：`b2_ops_qrows2.py:6-7` 仍稱「three independent signals（H4 section…）」，實作已承認只有二個共線 key 訊號且無 H4；`b2_ops_tqaep2.py:18` 仍稱「Not claimed: clause-level identity」，但 claim_ceiling 已含 `CLAUSE_SPAN_IDENTITY`。
7. **[LOW] freeze 完整性/帳務**：`supersedes` 指 round1（freeze:47），未指 round4；`not_claimed` 多一行（freeze:49）；`b2_gate_probe.py`、`b2_gate_probe.json`、`b2_ops_qrows.py` 不在 freeze digest 內（僅 manifest 有 sha），72/54 的 oracle 與 probe 未被本輪 freeze 綁定。
8. **[LOW] `state_gate` 對屬性複合字串誤報**：`["INSTALLED=UNVERIFIED","BOUND=UNBOUND"]` 會因 BOUND/UNBOUND 兩 token 並存回 `STATE_CONFLICT`；目前未套用到 E00，故不影響本輪 8 案，但「通用正確」不成立。
9. **[INFO] q_of docstring**：`b2_semantics.py:272-289` 仍稱二個 key 訊號是「independent carriers」，與 receipt 的 collinear 說明不一致。

## 程序註記

- 本輪沒有暴露 `-o` 路徑；mount 為 read-only，故 verdict 直接內嵌輸出，未寫入任何檔案（與 round 1 相同情況）。
- 環境的 `python`／`py` 不可用（hermes python shim 找不到）；我改用 Node 24.19.0 的 `fs`／`crypto` 獨立重實作 digest、clause span、72/54、quadrant、licence、state gate 與 receipt 對帳，未執行 Maker 的 Python。
- Prompt 的 SPEC 路徑多了一段 `SST_PLP_PH01_B1-B8_執行控制小包`；實際在 `SST_PLP_PH01_W0_B1-B8_執行控制小包`。我以 raw sha256 `140de5bc…` 定位，未改檔。
- 舊程式 `b2_ops_qrows.py` 仍為 5,680 B / `b9bad6a1…`，與 round 1 pin 一致；`b2_gate_probe.py` 為 4,825 B / `96f63708…`，manifest 一致。
- 我未修改 SPEC、parent、carrier、code、任何 receipt 或 closeout。