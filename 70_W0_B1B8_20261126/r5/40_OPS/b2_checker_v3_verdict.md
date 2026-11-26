# B2 v3 分離 Checker Verdict

- 受檢 carrier：`463dcf33a668a9daa8f0bbf447c7dacc4c3d602bc53fa7e4866844ffbbc4b3e1`（767,859 B，實測全等，2,391 行、1,385 registry 列）
- 受檢凍結：`40_OPS/b1b2_r5_CANDIDATE_MANIFEST.tsv`＝`f2f828b9…`（22 成員，22/22 sha+bytes 全等）
- 範圍：只驗 M-01／M-02／M-03／N-01／N-02／N-04 六項 change cone；A/B/C/D/F/G/H 不重驗
- 本輪未修改任何受檢檔；未寫入 SQS-THC／FHS／知識庫；未連網、未開 GUI、未接 broker

## 00｜分離声明

- 本審查在**新 context**、唯讀、獨立 scratch 下完成，未執行 Maker 任何模組（未 import `b2_engine`／`b2_tqaep`／`b1_spec`），全部數字由自寫解析器重算。
- **同模型軸 SoD 未建立**：Checker 與 Maker 屬同一模型家族，隔離僅在 context 與寫入權限層面，不構成 model-diverse 的獨立審查。此點不得由本檔推導為技術 SoD 已成立。

## 01｜逐 finding 表

| ID | 宣稱修法 | 獨立重算結果 | 判定 | 依據 file:line |
|---|---|---|---|---|
| **M-01** | E00 POS 改以 carrier `TECH54具名設計合約` 的 `SelectedDesign`／`SelectedVersion` 作獨立原據，比對 leading token | 自解析 carrier:1416 起 54 個 block，8/8 E00 unit 的設計選型與 carrier 值相同（含 TECH-004／005 的複合字串以 leading token 相等）。**spec 自身 payload 當 oracle 的自比已不存在**，oracle 為另一份文件（工具合約載體）。 | **CLOSED**（就「自比」而言） | `b2_engine.py:171-194`（`tech54_index`）、`:348-368`（E00 分支）；carrier:1420/1438/1456/1474/1492/1510/1528/1549 |
| **M-02** | guard 改回 spec 宣告的 `STATE_CONFLICT` 並以該碼作 PASS 條件 | `guard_design_selection()` 兩條分支皆回 `DENY` + `first_fail=STATE_CONFLICT`；TQAEP NEG 的 PASS 條件同時要求 `DENY` 與 `first_fail=="STATE_CONFLICT"`；spec 八列 NEG case 的 FirstFail 欄實測均為 `STATE_CONFLICT`；NEG 8/8 PASS。 | **CLOSED** | `b2_engine.py:380-390`；`b2_tqaep.py:125-126`；spec B2:105043/105045/105047/105049/105051/105053/105055/105057 |
| **M-03** | notes／closeout 的 HOLD 分解改由 `verdict_counts` 生成 | 總數對得上（91 = `verdict_counts.HOLD`），但**成因文字仍與 artifact 相反**：closeout 稱「E00 僅 1 案之 carrier 無 SelectedDesign」，而同檔 artifact 的 `actual.carrier_design_selection` 正是 `REUSE_INTERNAL_DESIGN`（carrier:1549 有該欄）；另有 17 個 ROUTE **NEG** HOLD 未列項。 | **PARTIAL** | `60_CLOSEOUT/SST_PLP_PH01_W0_B2_CLOSEOUT_r5.md:53-59`；`40_OPS/b1b2_r5_MAKER_NOTES.md:114`；`b2_r5_tqaep.json` case `B2.POS.TOOL_R2_TECH54__TECH-008` |
| **N-01** | `resolve_tool_row()` 以 Q1／Q2 雙前綴解析，唯一命中或雙邊一致才採用 | 54 條 route 全部 join 成功（不再 0/54）：52 條 Q1／Q2 完全一致，2 條（TECH-040、TECH-044）僅因 Q1 儲存格被 carrier 自身以 `…` 截斷而不一致。 | **CLOSED** | `b2_engine.py:197-214`；carrier Q1:442/446 與 Q2:959/963 |
| **N-02** | 加 `rows_total`（440/513/378/54） | `rows_total` 四值正確且等於 carrier 標題宣告（carrier:13/457/974/1356）與實測列數；**但 bucket 加總仍為 420／493／378／54，Q1、Q2 各缺 20 列、合計 40 列**（皆為 `REFERENCE/EVAL_ONLY`、`EVAL_ONLY_COMPARATOR` 等原子前綴值），bucket 仍不切分 `rows_total`。 | **PARTIAL**（原缺陷未除，只多了一個可見的對帳欄） | `b2_tqaep.py:194-200`；`b2_r5_tqaep.json.requiredness_distribution` |
| **N-04** | receipt `checked_values` 增 `applicability_evidence` | B3 收 1,351 拒 114；`requiredness=NOT_APPLICABLE` 的收據 **523 筆，缺 evidence 0 筆**；`checked_values` 確含 `applicability_evidence`；無 evidence 的 N/A 會被 `missing` 攔下。 | **CLOSED** | `b2_engine.py:457-458,473-476`；`b2_tqaep.py:162-170`；`b2_r5_receivers.json` |

## 02｜重算表 1–8

| # | 項目 | 自算結果 | 判讀 |
|---|---|---|---|
| 1 | E00 選型 vs carrier | carrier TECH54 block 54/54 解析成功；8/8 單位值與 carrier `SelectedDesign` 相同；Maker 記 7 PASS／1 HOLD。**1 HOLD 為偽**：TECH-008 被 `"SELECTED" in x` 過濾器濾成空集合（`b2_engine.py:351-352`），carrier:1549 實有 `REUSE_INTERNAL_DESIGN`。 | 自比已除，但**計數錯**；且見 03 節 M1（7 PASS 超過 spec 上限 2） |
| 2 | STATE_CONFLICT | guard 回 `STATE_CONFLICT`（兩分支）＋TQAEP PASS 條件要求該碼＋spec 八列 FirstFail 皆 `STATE_CONFLICT`；NEG 8/8 PASS | 一致，通過 |
| 3 | HOLD 分解 | 自 `cases` 重分類：Q POS 34、ROUTE POS 39、ROUTE NEG 17、E00 POS 1，合 91＝`verdict_counts.HOLD` | 總數對、成因文字錯（M-03） |
| 4 | 22 條 source_defects | 抽 6 條（TECH-004/013/019/021/037/053）回 carrier 逐條核：route 的 POS 欄**逐字等於** carrier Q1 值（carrier:406/415/421/423/439/455）。全量檢：54 條 route 中 52 條 POS 欄與 carrier 逐字相同，另 2 條（040/044）route 文字整段缺失。**真來源不一致 0 條**，22 條全為 Maker 比較規則錯（`REQ_VOCAB` 僅 6 個基礎類別，缺 `REFERENCE`／`EVAL_ONLY_*`／`DEFER_*`／`REUSE_*`）。 | Maker 規則錯，非來源缺陷 |
| 5 | distribution rows_total | 440／513／378／54 正確；bucket 加總 420／493／378／54，**Δ 20／20／0／0**，共 40 列未入 bucket | PARTIAL（N-02 未真正關閉） |
| 6 | B3 receipt evidence | N/A 收據 523，缺 evidence 0；`checked_values` 含 `applicability_evidence`（Q1/Q2 為 carrier 自陳 `N_A` 標記，Q3/Q4 為 section 行號） | 通過 |
| 7 | manifest `f2f828b9…` | 22/22 成員 sha256＋bytes 全等；manifest 自身 sha＝`f2f828b9…`；`b1b2_r5_candidate_freeze.json` **不在**成員內（符合宣稱）。**註**：受檢的 `SST_PLP_PH01_W0_B2_CLOSEOUT_r5.md` 亦不在成員內，其位元組不受該 digest 綁定。 | 通過（附註） |
| 8 | 掃新缺陷 | 無 HOLD 計入 PASS（91 全在 HOLD）；source_defects 未計入 PASS；`B2_ACCEPTED=NO` 三處一致。新缺陷見 03 節。 | 見下 |

## 03｜新缺陷

| ID | mandatory | 嚴重度 | 內容 |
|---|---|---|---|
| **M1（新）** | **是** | **BLOCKER** | **E00 POS 7 PASS 超出 spec 自宣告上限。** spec F05 對同一批 `E00 U0019～26` 的處分是「八 typed DesignSelection 精確保留；**2 歷史證據／6 Oracle HOLD**」（spec B2:61），§04.R5 再述「6 E00未具原Oracle保HOLD，其餘2只承舊證據原範圍，**不重新宣產品執行**」（spec B2:427）。產品卻記 7 案 PASS。另：(a) POS 宣告 predicate 為「獨立原條文／原 payload **逐欄相等**」（spec B2:105042），實作只比對單一設計選型 leading token（`b2_engine.py:365-368`）；(b) `_lead()` 以 `[/,;]` 切分複合字串，與 spec「**不拆複合字串**」（B2:427）相反。→ 案級 PASS 建在 spec 明示未綁的 E00 oracle 上，屬 mandatory 第 (1) 類。 |
| N-v3-02 | 否 | HIGH | 22 條 `source_defects` 全為偽（21 條 route＋1 條 E00）。route 文字與 carrier 工具列逐字相同，卻被 `REQ_VOCAB`（`b2_engine.py:77`）6 值封閉集判成 DRIFT（`b2_engine.py:336`）。方向雖保守（記 HOLD 而非 PASS），但把「來源文件內部不一致」寫成事實，屬對外部權威的錯誤陳述。 |
| N-v3-03 | 否 | MEDIUM | TECH-008 POS HOLD 為偽，且 notes:114／closeout:58 的成因（「carrier 無 SelectedDesign」）與 artifact 自身欄位相反。 |
| N-v3-04 | 否 | MEDIUM | route 文字整段缺失時 `PRESERVED if car in stated or not stated`（`b2_engine.py:338`）會真空成立；TECH-040／044 的 route `source_payload` 只有 `["682"]`／`["686"]`。本輪因 carrier 值不可推導而落 HOLD，未造成 PASS 灌水，但屬潛在 false-PASS 路徑。 |
| N-v3-05 | 否 | LOW | carrier Q1 TECH-040／044 儲存格帶 `…` 截斷 → Q1/Q2 不一致；`resolve_tool_row` 內部回 `AMBIGUOUS`，`op_hard` 卻以 `CARRIER_ROW_ABSENT` 對外表達（`b2_engine.py:210-213,344-347`）。 |
| N-v3-06 | 否 | LOW | Q3/Q4 共 432 案及 Q1/Q2 的 91 案以 `requiredness=NOT_APPLICABLE` 記 PASS（`b2_tqaep.py:70-75`）。屬既有、有 carrier evidence 的設計，非本輪 change cone，僅記錄不重驗。 |

## 04｜結論

三項 mandatory 中，M-01／M-02 的原始缺陷已實質修好（自比已除、FirstFail 已對），M-03 仍 PARTIAL；N-01／N-04 關閉，N-02 只做了可見化未做修正。但 E00 的案級 PASS 數（7）高於 spec 對同批 8 案自宣告的上限（2 PASS／6 HOLD），且 PASS 所依的 predicate 窄於宣告 predicate、並違反「不拆複合字串」。此屬 mandatory 第 (1) 類（案級 PASS 依賴 spec 未綁的 oracle），故不得 ACCEPT；其餘 5 項列 non-mandatory 並已註嚴重度。

- 重算完整性：1–8 全部自行重算完成，無 NOT_VERIFIED 項。
- 未修改任何受檢檔；僅寫入 `40_OPS/b2_checker_v3_verdict.md`、`40_OPS/b2_checker_v3_recompute.json`。

VERDICT: REJECT
MANDATORY_FINDINGS: 1
