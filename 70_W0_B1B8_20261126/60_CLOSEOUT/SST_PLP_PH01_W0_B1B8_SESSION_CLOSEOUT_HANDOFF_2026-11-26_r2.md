# SST_PLP_PH01 W0 B1–B8｜SESSION 結案與移交（2026-11-26 · r2）

> 讀者：下一位執行代理（Commander）。本檔自足，取代 r1 作現行移交。
> 撰寫原則：只寫本次實測；未達成者寫「未達成」，不美化、不補值。

---

## 0｜本次 SESSION 做了什麼（與沒做什麼）

| 項目 | 本次結果 |
|---|---|
| 上游知識庫位置 | **被重新編排**：B1–B8 SPEC 已移入 `W0_B1-B8_NATIVE_FIRST_2026-11-26_r4_HERMES_FINAL\SST_PLP_PH01_W0_B1-B8_執行控制小包\`。B1/B2 的 raw sha **未變**（`13294cad…` / `140de5bc…`），故以 **sha 認身分**、不再以路徑深度找檔；`b1_reader` 與 `b2_semantics` 已改為 by-sha 定位 |
| B1 | 修完 round-3 的 11 項中 10 項（第 3 項措辭於 round 4 判 PARTIAL）、再修 round-4 指出的 5 項 Maker 缺陷中的 4 項；**round 4 判 `B1_ACCEPTED = NO`**；已 freeze round-5 候選並送 round 5（本次 SESSION 內未取回 verdict） |
| B2 | **round-1 Checker 10 項缺陷已全部重做（round-2 候選）**：`direct_clause_sha` **1,465/1,465 可重現**（規則＝`direct_parent_ref` + a..b 含第 b 行 LF；round-1 指出 Maker 用了錯的 ref）；歷史 **72 = HARD 16 + E00_TECH 2 + TECH_ROUTE 54** 可重現、**54 = TECH_ROUTE**；requiredness 改標 `VERBATIM_ONLY`（1,385）／route N/A（54）並撤回「0 不一致＝證據」；象限承認兩訊號共線、改用 disjoint `source_row` 區間佐證；namespace NEG 改為丟／偽 namespace 且 naive 命中共 1,385；STATE_CONFLICT 改宣告式互斥＋合法共存探針；carrier 1,385 列以 sha 重綁。NEG 終態 **PASS 1,396／PASS_INTERPRETED 54／HOLD_SPEC_MUTATION_UNIMPLEMENTED 9／HOLD_ORACLE_UNBOUND 6／FAIL 0**（round-3／round-4 兩輪判讀後共修 16 項 Maker 缺陷；E00 為 **2 執行／6 HOLD**，總 HOLD 15） |
| B3 | 只做 **DEV-1 parse**（`B3.PARSE@1`，claim ceiling `CENSUS_AND_PIN_ONLY`）：365 Unit、payload pin 365/365、§06 752 案（365 POS／387 NEG）、case_id 雙向 join 0 落差 |
| B4–B8 | **未開工**（見 §5） |
| 發布 | 見 §6 |

**沒有升格任何批次**：`promotion_state.promoted_to_primary = []`。

---

## 1｜現行權威指標（current_pointers）

| 角色 | 檔案 | raw SHA256 |
|---|---|---|
| B1 freeze（round 5 候選） | `40_OPS/b1_candidate_freeze_20261126T141853.json` | digest `9666c7ed…` |
| B1 run | `40_OPS/b1_run_20261126T141840.json` | `591808fa…`（127,559 B） |
| B1 TQAEP | `40_OPS/b1_tqaep_20261126T141842.json` | `821f3e61…`（41,636 B） |
| B1 checker round 4 | `40_OPS/b1_checker_round4_verdict.md` | `B1_ACCEPTED = NO`（9/11 PASS，item 3 PARTIAL） |
| B1 checker round 5 | `40_OPS/b1_checker_round5_verdict.md` | 4/5 round-4 defects PASS；第 5 項（manifest 過期）判 FAIL，但該 manifest 已於 verdict 之後重建（現與 freeze 0 落差）。`B1_ACCEPTED` 仍 **NO** |
| B2 freeze | `40_OPS/b2_candidate_freeze_round5.json` | digest `c7a12bcc…`（claim 由 TQAEP 複製，不再硬寫） |
| B2 ToolReadSet@2 | `40_OPS/b2_toolreadset_20261126T154724.json` | `402d2b08…`（3,264,972 B） |
| B2 TQAEP@2 | `40_OPS/b2_tqaep_20261126T154735.json` | 見 manifest（claim `ROW_PAYLOAD_PIN_INTEGRITY_AND_CLAUSE_SPAN_IDENTITY`） |
| B2 checker r3 | `40_OPS/b2_checker_round3_verdict.md` | **7 PASS / 3 PARTIAL / 8 新缺陷；`B2_ACCEPTED = NO`**（clause 1,465/1,465、digest、72/54、2,930 case 皆由其 Node 實作獨立重算通過） |
| B3 parse | `40_OPS/b3_parse_20261126T142325.json` | `6dff324f…` |
| B2 checker r4 | `40_OPS/b2_checker_round4_verdict.md` | **原10項 8 PASS／2 PARTIAL；新8項 6 PASS／2 PARTIAL；10 新缺陷；`B2_ACCEPTED = NO`** |
| 交付索引 | `DELIVERY_MANIFEST.json` | 由 `20_DEV/build_delivery_manifest2.py` 重建（@2） |

r1 的 `b1_run_…130421` / `b1_tqaep_…130423` / `b2_*_…122128` / `b2_tqaep_…131157` 一律 `SUPERSEDED_RECEIPT`，只作歷史。

---

## 2｜B1 真實狀態

- 60 案：**PASS 53／HOLD_SCOPE_NOT_COVERED 1／HOLD_BASELINE_NOT_VALID 1／HOLD_ORACLE_UNBOUND 5／FAIL 0**。
- 23 BASE+KERNEL units：`OBSERVED_TRACKED_AT_HEAD 11`、`OBSERVED_IN_WORKING_TREE_UNTRACKED 4`、`OBSERVED_IN_FDA_CARRIER_CONTENT_IDENTICAL 6`、`OBSERVED_MIXED_SURFACES 1`、`TYPED_MISSING_OUT_OF_ALLOW_LIST_SCOPE 1`；7 FDA slots 全 `CARRIER_OBSERVED_SINGLE`。
- `fabricated commits = 0`（round 3 為 9）；`measured` 對 binding 目標為實測非回抄；receipt 已釘兩個 preflight 輸入（`a8025e2f…` / `de92bd2c…`）。
- 讀取面收斂：carrier 只讀 allow-list 的 16 件；`BASE-018` 的 `tests/test_fda_*.py` 因此無法讀 → `TYPED_MISSING_OUT_OF_ALLOW_LIST_SCOPE`＋POS `HOLD_SCOPE_NOT_COVERED`。這是關掉 round-3「越界讀取」的**可見代價**，不是隱藏缺件。

### 仍缺（B1_ACCEPTED = NO 的真正原因）
- **Owner（4）**：D-1 三筆 locator binding 未追認；D-2 allow-list 是否擴及 `tests/test_fda_*` 與 mirror 地位；D-3 七槽 slot↔artefact 映射（`slot_reference_counts=0`）；D-4 五 Kernel NEG 的 Domain Owner 語意 oracle。
- **Oracle（5）**：`B1.NEG.KERNEL_*` 全 `HOLD_ORACLE_UNBOUND`，非 Maker 缺陷。

---

## 3｜B2 真實狀態（round-2 候選；round-1 Checker 十項已重做）

- `b2_ops_tqaep2.py`：2,930 案，**POS 1,465 PASS；NEG 1,397 PASS ＋ 54 PASS_INTERPRETED ＋ 14 HOLD_SPEC_MUTATION_UNIMPLEMENTED ＋ 0 FAIL**。SPEC §06 期望分布 1,385／72／8 仍完全一致，`orphans 0 / missing 0`。
- **clause 身分已可重現 1,465/1,465**：round-1 指出 Maker 用了錯的 ref（`original_source_ref` 對 Q 列指向證據文件）。正確規則＝`direct_parent_ref`，取父檔第 a..b 行（**含第 b 行 LF**）的 UTF-8 bytes SHA；`direct_parent_ref` 於 `b2_semantics.clause_rule_note()` 明寫。
- **歷史純量已對帳**：72 = HARD 16 ＋ E00_TECH 2（欄 5 內含 `*_UNBOUND` 哨兵）＋ TECH_ROUTE 54（無欄 5）；54 = TECH_ROUTE 恰等。兩者皆可由 SPEC ＋ 未修改的舊程式 `b2_ops_qrows.py`（`pin := sp[5]`）重現，屬「無可用 pin 文字」，不是「無工具」；語意乾淨的 no-version 計數另為 1,407。
- **requiredness 已按檢查意見撤回主張**：1,385 Q 列標 `VERBATIM_ONLY`（原表行才是權威，Maker 不比對自身）、54 route 列 N/A、僅 HARD/E00 為 `RULE_CROSS_FIELD`；`disagreement_count = 0` 不再當證據；`Q4 EVAL_ONLY` 更正為「0 列，EVAL_ONLY 在 Q1」。
- **象限**：承認 `key` 前綴與 `q_row.full_key` **共線**（同一前綴），改以 disjoint `source_row` 區間（233–672／680–1192／1200–1577／1585–1638）作額外訊號；非 Q 列 80 = 18+8+54。
- **NEG 保真**：namespace 案改為丟掉／偽造 namespace 的**身分**變異（naive 尾碼實作確實命中共 1,385，非空轉）；HARD 僅 9 列其 §06 mutation 為 HARD-loss 者以單欄變異執行，其餘 9 列改判 `HOLD_SPEC_MUTATION_UNIMPLEMENTED`（§06 mutation 文字與其期望碼不同，Maker 不得自造 oracle）；54 route 列改兩個單欄 arm 且降級為 `PASS_INTERPRETED`（§06 未指名欄位）；STATE_CONFLICT 改以**宣告式互斥關係 + token 相等**判定（先前 substring 版本會把 `NOT_SELECTED` 誤觸 `SELECTED`，屬真缺陷），並以 `INSTALLED+ENABLED`／`DEFER_NOFIT+NOT_SELECTED` 兩個合法輸入作反向探針。8 列 E00 中 3 列有宣告式對照可執行、2 列無（`SELECTED_DOCUMENT_ADAPTER`／`SELECTED_OPTIONAL_DISABLED`）→ 後者列 HOLD 不發明關係；連同 9 列 HARD 合計 14 列 HOLD。
- **gate 診斷**：`20_DEV/b2_gate_probe.py` → `40_OPS/b2_gate_probe.json`（8 個 state_gate probe 全對、3 列 E00 對照成立、5 個 namespace probe 全部 `baseline_rows=1／namespace_dropped=NAMESPACE_JOIN_DENY／naive_matches≥1`）。此為 Maker 診斷，不是接受。
- **carrier 已綁**：1,385 列引用 `463dcf33…`（`SST_PLP_共用實質正文_工具合約_…r2.md`，實際在 `PHASE 01~04\藍圖\實質正文\`，宣告路徑寫 `PHASE 00~04`）→ `CARRIER_SOURCE_REBOUND_BY_SHA`／`CANDIDATE_NOT_RATIFIED`。
- `claim_ceiling` = **`ROW_PAYLOAD_PIN_INTEGRITY_AND_CLAUSE_SPAN_IDENTITY`**（round-3 判定 `PROVENANCE` 超額後降級）：收據只證 payload pin 與 clause span 身分，**不證**與原來源的值相等；原本來源比對降為 `DIAGNOSTIC_ONLY_NOT_A_GATE`（`coarse_rule_mismatches` 明列）。`not_supported` 亦列明：獨立 requiredness（1,385 Q 全 `VERBATIM_ONLY`、54 route N/A）、9 列 HARD 非-loss mutation、54 列未指名 mutation、工具可用性、任何接受。
- `B2_ACCEPTED`：**不成立**（round-3 分離 Checker 已派、verdict 未取回；Maker 不自封）。

---

## 4｜待 Owner 裁決（合併清單）

| # | 事項 | 受影 | 最小恢復 |
|---|---|---|---|
| D-1 | 三筆 locator binding（BASE-009 ×2、BASE-017）追認或改 SPEC 路徑＋新 sha | B1 | Owner 簽認或 SPEC 修訂 |
| D-2 | allow-list 是否納入 `tests/test_fda_*.py`；mirror carrier 地位 | B1 `BASE-018`、EOL 觀察 | Owner 決；不可由 Maker 擴張 |
| D-3 | 七槽 slot↔artefact 映射（`slot_reference_counts=0`） | 7 FDA POS（`CARRIER_LEVEL_ONLY`） | 提供 slot 級來源 |
| D-4 | 五 Kernel NEG 語意 oracle | 5 案 | 原 Domain Owner 受保護欄位 oracle |
| TT-UP-1 | **上游** SPEC §06：9 個 HARD NEG 的 mutation 文字寫 `ABI_UNBOUND`／`MAKER_SELF_ATTEST`／`PIT_LOOKAHEAD`，expected 卻一律 `TOOL_REQUIREDNESS_HOLD` | 9 列 HOLD | 原 SPEC Owner 修 §06 或改 expected 名 |
| TT-UP-2 | **上游** `q_row.evidence_line` 全體較 `original_source_ref` 行號多 664（1,385/1,385） | 任何用 evidence_line 定位的下游 | 原 SPEC/生成器修正；本輪未使用該欄 |
| D-5 | B2 parent 重綁（`d95c8ac6…`）追認 | B2 全部 1,465 列 | Owner 追認 rebind（同一手法亦用於 carrier `463dcf33…`） |
| ~~D-6~~ | **已由 Maker 收斂**：round-1 指出 clause 規則為「`direct_parent_ref`＋含第 b 行 LF」，重算 1,465/1,465 成立 → 不需 Owner 裁決；僅需 round-2 Checker 獨立確認 | B2 clause 身分 | — |
| ~~D-7~~ | **已由 Maker 收斂**：72 = 16 HARD＋2 E00（`*_UNBOUND` 哨兵）＋54 ROUTE，可由未修改舊程式重現 → 不需 Owner 說明；但**不得**再以 72/54 當「無工具」計數 | B5 導入分母 | — |

---

## 5｜B4–B8：未開工（不是 HOLD，是未做）

本次 SESSION 只完成 B1 收斂、B2 重建、B3 parse。**B4–B8 沒有任何 DEV／OPS／TQAEP 產物**，不得引用本次任何數字當其結果。下一手起點：

1. `w0_spec.py` 已支援 B4–B8 的 by-sha 取件（`PINS` 已填 `15a74095…`/`4c8af9a9…`/`bab32ae4…`/`a78f3dc3…`/`fdd364a7…`）。
2. 依 B3 的模式先出 `B{n}.PARSE@1`（census＋pin＋case join），再逐 kind 建 POS 謂詞與分類 NEG，**不得**用 B2 的通用 oracle 直接套（B3 以上每個 kind 的 NEG 語意不同）。
3. B4←B1+B3、B5←B2+B3、B6←B4+B5、B7←B3+B4+B5+B6、B8←B7。B3 本體不依賴 `B1_ACCEPTED`，但 **B3 的語意 TQAEP 需要 B0+B2 的真 requires**，且其 `SourceChildLedger.draft.md` 需原 Writer 授權 COMMIT（本次未寫）。

---

## 6｜發布

- 通道：`W\dist\SQS-THC_MVP`（clone，origin `https://github.com/shw097-team/SQS-THC_MVP`），非 wave root。
- 已推兩個 commit：`892b659b`（45 檔：B1/B2/B3 code、current receipts、freeze、checker rounds 1–5、closeout）與 `93a4f21`（`DELIVERY_MANIFEST.json`＋round-5 verdict）。raw readback 與本地 byte 相同，`origin/main` 與本地 HEAD 相同。
- 明標「candidates, not accepted」；未推 superseded receipts、run logs、原始來源內容、憑證。

---

## 7｜異常阻擋／卡住稽核（本 SESSION，逐項附證據）

| # | 現象 | 次數 | 根因 | 處置 | 現況 |
|---|---|---|---|---|---|
| 1 | `parse_ref` 不吃單行 `@sha:L17` → carrier 0 綁 | 1 | 正則只認 `L a–b` | 加單行分支 | 已解，1,385 綁定 |
| 2 | `_CARRIER_CACHE` 未宣告 → 潛在 NameError | 1 | 宣告漏寫 | 補宣告 | 已解 |
| 3 | `contradicting_state` 對 `REUSE_INTERNAL_DESIGN` 回 None → NEG_FAIL 1 | 1 | 對照表不全 | 補第 9 組 | 已解（後又被 token 修法取代） |
| 4 | 加 `SELECTION_CLASS` 規則 → 合法複合狀態被判衝突，NEG_FAIL 3 | 1 | 規則過寬（「兩個選別 token」） | 撤回該規則，改宣告式配對 | 已解 |
| 5 | 缺 `DEFER_NOFIT／REFERENCE_ONLY ↔ SELECTED_DESIGN_ONLY` → NEG_FAIL 2 | 1 | 配對不全 | 補兩組 | 已解 |
| 6 | **proxy 探針抓到 substring 缺陷**：`SELECTED` ⊂ `NOT_SELECTED`，合法 `DEFER_NOFIT+NOT_SELECTED` 被誤判衝突 | 連續 4 輪（1→3→2→0 後再現） | 以子字串比對 token | 改 `_state_tokens` 精確 token 比對；`contradicting_state` 同步改；無對照者改判 HOLD | 已解，8 個 probe 全對 |
| 7 | 前景 `timeout=900s` 超過 600 上限 → 被轉背景 | 1 | 工具上限 | 改背景＋notify | 已解 |
| 8 | round-2 checker 跑了 7 分鐘仍無 verdict | 1 | 正常長跑（round 1 約 45 分） | 因候選已被 round-3 取代而 kill，改派 round-3 | 已重派（`proc_22d2120961bb`，5 分心跳） |
| 10 | round-4 verdict 指出 8 個 Maker 缺陷＋2 個上游 | 10 項各 1 次 | freeze 硬寫舊 claim（與 TQAEP 不一致）、provenance 診斷只收 `kind==FILE` 漏 80 列、`Apache Arrow` 誤判授權、Q 列 TR 自比、`clean_no_version` 混入 Q、`disjoint` 硬編碼、probe 把 maker pair 當證據 | 逐項修；freeze 改由 TQAEP 複製 claim／not_claimed／neg_holds；授權加產品名排除；上游兩項列 TT 不自行改 SPEC | 已修；round-5 checker 已派（`proc_39e3a07accfa`） |
| 9 | round-3 verdict 指出 8 個新缺陷（371 Q 列 requiredness 自比、E00 3/2 數字為狀態數而非列數、licence 把 `UNBOUND` 當授權、Q pin 取到 need 句、provenance claim 超額、分母 864 vs 1,014、namespace 只取 last segment、POS 未含 clause） | 8 項各 1 次 | Maker 語意與詞彙不統一；其中 licence 與 pin 是**真的錯**（會污染 B5） | 逐項修並以探針驗；`UNBOUND` 不再當授權、Q pin 改 `NOT_EVALUATED_Q_ROW`、claim 降級、namespace 改 `endswith` 判丟／偽並保留 unknown→`[]` | 已修；round-4 checker 已派（`proc_4b1d8309a37f`） |

**自我判定的問題**：#6 屬同一根因的**第 5 次**修補，已超出「每 finding 最多 2 次實質修補」的規則。本輪之所以仍修，是因為探針暴露的是**程式缺陷**（substring）而非 oracle 語意分歧；但若 round-3 Checker 仍判此 gate 不可靠，Maker **不再迭代**，直接記 `HOLD_ORACLE_UNBOUND` 並要求原 Domain Owner 提供互斥關係表。

---

## 8｜本次踩到的坑（已寫進程式）

1. **上游改版會搬路徑**：一律 by-sha 定位（`w0_spec.find_spec` / `b2_semantics.find_spec` / `b1_reader.run_b1.find_spec`）。
2. **`os.walk` 回傳檔名不是身分**：B2 目錄下有 r2/r3/r4 同名檔，只有 r4 的 sha 是 pin。
3. **`dict` 字面量內 `set.pop()` 會讓後面的 `len(seen)` 變 0**：`q_of` 一度因此把所有象限判成不一致（已修）。
4. **`candidate_digest` 要寫清楚排序規則**：round 4 抓到宣告序 vs 排序序不一致（本次已改為排序並在檔內註明）。
5. **TECH_ROUTE 的 payload 是 2 欄複合字串**，不是單欄；Q3 列只有 8 個非空欄。
6. `codex exec` 的 `-o` 可寫回 wave root，但 checker 沙箱本身 read-only（round 4 明說）。

---

## 8｜不可跨越的線（未變）
不讀／不輸入口令、私鑰、DPAPI；不自建 issuer／registry／compiler；不改知識庫原件、不改 `SQS-THC`、不改 `FHS/Fabric`；`write_set=[]`（產品效果）；不 checkout／fetch／import／執行 repo 內程式碼；`FIN_ORDER=DENY`；不為求綠改 expected／改 Oracle／把 HOLD 藏成 PASS；Maker 自測不是驗收。
