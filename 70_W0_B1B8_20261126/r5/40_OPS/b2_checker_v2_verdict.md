# B2 v2 分離 Checker Verdict

## 0｜分離声明與範圍

- **身分**：本輪為**分離唯讀 Checker**，與 Maker 不同 context／session；**未 import 任何 Maker 模組**（自寫 stdlib 解析器：carrier 表列、`UNIT_BEGIN` JSON、compact-JSON SHA）。
- **SoD 限制（明列）**：分離只建立在 context／session 分離；Checker 與 Maker 同屬**同一模型軸**，**同一模型軸之 SoD 未建立**，本 verdict 不構成 R16 獨立驗證、不是原 Reader 接受。
- **受檢範圍**：只驗 B2 v2 的 change cone = D-5／TT-UP-2 的欄位映射，以及由它改變的案級 verdict。R1–R3 已關閉項**不重驗**；v1 Checker 已列 but 本輪未變動者（F-01／F-03／F-06）標為 out-of-scope carryover，不計入 mandatory。
- **寫入**：僅本檔與 `b2_checker_v2_recompute.json`。受檢檔、受檢源碼、知識庫、SQS-THC、FHS 全程唯讀；無網路、GUI、broker、lease。
- **方法**：無法重算者標 NOT_VERIFIED（本輪無此類項）。

## 1｜A–H 重算表

| # | 項目 | expected（Maker／spec 宣稱） | observed（本 Checker 獨立重算） | 判定 |
|---|---|---|---|---|
| **A** | carrier 第 7–9 行四維度宣告；四節標題行號／列數 | 第 7 行宣告 Q1 Requiredness／Q2 AdmissionDecision／Q3 Kind applicability／Q4 Golden；標題 13/457/974/1356；440/513/378/54 | carrier `463dcf33…4b3e1`／767,859 B 全等；第 7 行四維度原文在；`## R3-REGISTRY-Q1｜440列`@13、`Q2｜513列`@457、`Q3｜378列`@974、`Q4｜54列`@1356；自解析列數 440/513/378/54＝**1,385** | **PASS** |
| **B** | 1,385 列 payload 與 spec unit 逐列比對 | 每列 key／row／line／payload 全等 | **1,385/1,385** payload_sha 相等、q_row.payload 逐值相等、source_row 相等、`carrier=Lnn` 精確命中；分歧 0。Q1(idx2)↔Q2(idx5) 以 440 個同尾 key 配對，requiredness 分類分歧 **0**（僅 TECH-040/044 兩列 Q1 儲存格被 carrier 截斷成「…」） | **PASS** |
| **C** | Q3/Q4 是否真的沒有 requiredness 欄 | 無此欄→`NOT_APPLICABLE`＋section 行號 | Q3 8 欄＝kind×aspect／applicability／rationale／owner／PH-W／EXPECTED_NOT_OBSERVED／source_ref／M_EVID；Q4 10 欄＝gold／desc／input／expected／neg／edge-sec／disposition／EXPECTED_NOT_OBSERVED／ref／L1 anchor。**無任何 requiredness 欄**；抽 20 列無一欄存 requiredness 值。註：Q3 `idx1` 有 `CONDITIONAL`×94，那是**適用性**，若用「掃全列找原子」會誤判——本輪的固定索引法不讀它。`NOT_APPLICABLE` 有 carrier:974／carrier:1356 原據，非避重 | **PASS** |
| **D** | AUTHOR_DESIGN_ONLY 原子前綴規則 | 以 HARD/SOFT/CONDITIONAL/OPTIONAL/EVAL_ONLY/REFERENCE 前綴判合法，保留原字串 | 分類結果：STRICT 788、NA 標記 91、**前綴規則才通過 40**、UNBOUND 34、Q3/Q4 結構性 NA 432。前綴規則只作用在**已宣告的單一索引**上，故不會把非 requiredness 欄誤判成 requiredness（Q3 idx1 的 94 個 `CONDITIONAL` 未被讀）；`N_A`／`ROUTE_ONLY…` 被顯式排除；34 個策略值（`BASE_REQUIRED_*`/`REUSE_*`/`DEFER_*`/`BLOCKED_REPO`/截斷值）仍判 UNKNOWN→HOLD。效應是**放寬值詞彙、收緊未知值** | **PASS_WITH_NOTE**（保守且可逆→non-mandatory，見 N-02） |
| **E** | 2,930 案 verdict | PASS 2,786／HOLD 144／FAIL 0；B3 1,351/114；B5 0/1,465 | 逐案重算**總數與分佈完全一致**（Q POS 1,351+34、Q NEG 1,385、HARD 18+18、E00 7+7／1+1、ROUTE 54+54）。HOLD 144＝34 Q（17 列×2 namespace）＋108 ROUTE（兩側）＋2 E00。**但**：Q POS 綁 spec payload_sha（真外部承諾）可；HARD POS 為「unit 陳述 vs carrier 列」兩份記錄可；**E00 POS 7 案為自比**、**E00 NEG 7 案 first_fail 與 spec 期望不符** | **FAIL** |
| **F** | B3／B5 接收 | B3 收 1,351 拒 114；B5 收 0 拒 1,465；不得把 draft 寫成 ACK | 數字相符。B3 拒 114＝UNKNOWN 96（34 Q＋54 ROUTE＋8 E00）＋source_row 缺 18；其中 80 案（HARD/E00/ROUTE）根本無法被 B3 消費。B3 收的 1,351 內含 **523 個 `NOT_APPLICABLE`**，receipt **沒有** applicability evidence 欄位（只在程式內當 gate）。decision 只出現 `ACCEPT_FOR_DRAFT`／`REJECT`，**無 ACK** | **PASS_WITH_NOTE** |
| **G** | manifest `902e579c…` | 成員 sha/bytes 與實檔一致；freeze 收據不在 manifest 內 | 實測 `902e579c456b…16333`／2,174 B；22 成員 sha 與 bytes **全等**；`b1b2_r5_candidate_freeze.json` **不在**名單（名單內 `b1b2_freeze.py` 是產製腳本，非收據） | **PASS** |
| **H** | 禁止宣稱掃描 | 不得把 HOLD／NA 當 PASS、不得宣稱 B2_ACCEPTED／已安裝 | `B2_ACCEPTED` 只出現在否定句（0 次肯定）；tqaep `claim_ceiling` 明寫「HOLD/PARTIAL are never PASS」；無 INSTALLED／license／ABI 已完成字樣；receivers 全部 `ACCEPT_FOR_DRAFT`。**但**：523 個 NA 列導出的 1,046 案被計入 PASS 2,786（有分佈與逐案註記，但**總數未拆分**）；closeout §05 的 HOLD 構成與 artifact 不符（見 M-03） | **PASS_WITH_NOTE** |

### E 的三個子問題（逐一回答）

1. **抽 30 個 PASS 是否真滿足原 predicate？** — 抽 32 案（Q1/Q2/Q3/Q4 各 5、HARD 4、E00 4、ROUTE 4）。Q 類 20 案全部通過 line/key/row/SHA 四項，requiredness 皆來自宣告索引或結構性 NA → 成立。HARD 4 案為 carrier idx2 與 unit 陳述兩份記錄相等 → 成立（但 payload 逐欄一段未驗）。**E00 4 案全部不成立**：`actual` 只有 `design_selection`，其值即 spec 自己 payload 的字串，沒有與任何外部記錄比對。ROUTE 4 案全 HOLD（原因錯誤，見 N-01）。
2. **144 HOLD 是否真屬 oracle 未具而非產品失敗？** — 34 Q 是：來源值為作者策略詞或被 carrier 截斷（`REUSE_EXISTING_PROVIDER_FIRST / FDA_FO…`），不可猜。2 E00 是（TECH-008 無 selection 字樣）。**108 ROUTE 不是**：全部因 route key 缺 Q namespace 而查不到 carrier 列，屬映射失敗，非 oracle 未具。
3. **closeout 的 110 是否對得上？** — 對不上。寫的是「18 HARD＋8 E00＋54 ROUTE」，實測是「108 ROUTE＋2 E00」；18 HARD 全部是 PASS。

## 2｜Findings

| id | mandatory | severity | file:line | 事實 |
|---|---|---|---|---|
| **M-01** | **是** | HIGH | `b2_engine.py:298-304`；`b2_tqaep.py:115-119` | 7 個 E00 POS 的 PASS 條件是「spec 自己 `source_payload` 內含 `SELECTED`/`NOT_SELECTED` 字樣」。期望值與觀測值是**同一個物件**；8 案 `compact(source_payload)==payload_sha` 全部可算且相等，卻從未驗。屬判定紀律 (1)「案級 PASS 依賴未綁 oracle 或自比」。v1 這 7 案為 HOLD，v2 改 PASS |
| **M-02** | **是** | HIGH | `b2_engine.py:315-323`；`b2_tqaep.py:120-124`；spec §06.0 E00 NEG 8 列 | 8 個 E00 NEG 的 spec 期望首錯是 **`STATE_CONFLICT`**；Maker 實際回 `TOOL_REQUIREDNESS_HOLD`×3、`DESIGN_SELECTION_DRIFT`×4，仍記 PASS。`STATE_CONFLICT` 在 `b2_engine.py`／`b2_tqaep.py` 出現 **0 次**。PASS 只檢查 `decision==DENY`，不比 first_fail。屬 (1) |
| **M-03** | **是** | HIGH | `b1b2_r5_MAKER_NOTES.md:54`；`B2_CLOSEOUT_r5.md:57-60`；`b2_r5_tqaep.json` cases | Maker 自陳「E00 6/8 typed DesignSelection/enable Oracle 未具 → 全 HOLD」，closeout §05 也把 18 HARD＋8 E00 算進 144 HOLD；artifact 卻是 14 個 E00 案與 18 個 HARD 案 **PASS**。留存風險清單因此**少列 32 案被接受**。屬 (2) 的帳目面（方向是「宣稱 HOLD、實為 PASS」） |
| **N-01** | 否 | HIGH | `b2_engine.py:252-254,285-294` | TECH_ROUTE key（`TOOL_R2_TECH54::TECH-xxx::ROUTE`）不含 Q namespace，carrier 查表**必然落空**→108 案全 HOLD「carrier value not derivable」。加上 `R3-REGISTRY-Q1::` 前綴後 54/54 可 join（17 一致／21 漂移／16 未陳述）。closeout §04「54 unit 的 requiredness 陳述與其工具列交叉核對」**未發生**。因是 HOLD 非 PASS，不列 mandatory |
| **N-02** | 否 | MED | `b2_engine.py:76-93`；`b2_r5_tqaep.json` `requiredness_distribution` | 前綴規則放行的 40 列（Q1/Q2 各 20）**不在** 分佈字典內（Q1 合計 420/440、Q2 493/513），機器可讀分佈看不到作者規則的實際作用範圍。規則本身限縮在固定索引，不會誤分類他欄，且把 34 個未知策略值留在 HOLD → 保守、可逆 |
| **N-03** | 否 | MED | `b2_engine.py:260-283` | HARD POS 是「unit input_rule 陳述 vs carrier idx2」兩份記錄（可接受），但 80 個非 Q unit 的 `payload_sha` 從未重算（實測可算且 80/80 相等），spec POS predicate 的「原payload逐欄相等」那半段未執行。HARD NEG 仍為常數 `HARD->OPTIONAL` gate（v1 F-03 遺留，不在本 cone） |
| **N-04** | 否 | MED | `b2_r5_receivers.json`；`b2_engine.py:378-379` | 523 個 `NOT_APPLICABLE` 列在 B3 為 `ACCEPT_FOR_DRAFT`，但 receipt 14 欄內**沒有** applicability evidence（gate 只在程式碼裡）→ 事後無法從收據看出為何接受。另 80 個非 Q 條目因 `source_row=None` 永遠進不了 B3 |
| **N-05** | 否 | LOW | `b1b2_r5_MAKER_NOTES.md:97`；`B2_CLOSEOUT_r5.md:70-72` | Notes 寫 freeze manifest「9ac5be40…」，實測為 `902e579c…`；closeout §06 仍寫「requiredness 全 UNKNOWN → 全拒；B2 需先補欄位映射（D-5）」，與同檔 §04 的 1,351/114 自相矛盾 |
| **N-06** | 否 | LOW | `b2_tqaep.py:88-93` | Q NEG 只執行「跨 namespace」一臂，宣告的另一臂（僅改原列 payload/Requiredness）未執行（v1 F-06 遺留） |

**out-of-scope carryover（不重新裁決、不計入 mandatory）**：v1 F-01（文件層結果命名為產品 PASS）、F-03（HARD NEG 常數 gate）、F-06（Q NEG 子臂）。三項在本輪 cone 內未改變，僅在 N-03／N-06 標註。

## 3｜結論

A／B／C 三表在 v2 被**真正修好且可獨立重算**：1,385 列逐列 key／row／line／payload SHA 全等，Q1 idx2／Q2 idx5 的映射在 440 個同尾 key 上互證、分歧 0，Q3/Q4 確無 requiredness 欄，`NOT_APPLICABLE` 有載體原據。2,930 案的總數與分佈（PASS 2,786／HOLD 144／FAIL 0）與接收數字（B3 1,351/114、B5 0/1,465）逐案重算一致，manifest `902e579c…` 22 成員全等，沒有 `B2_ACCEPTED`／已安裝／ACK 的宣稱。

不能接受的是 change cone 內被**新改成 PASS** 的 14 個 E00 案：POS 是拿 spec 自己的期望值當觀測值（payload_sha 明明可算卻不驗），NEG 是 first_fail 與 spec 期望 `STATE_CONFLICT` 不符仍記 PASS；同時 Maker 自己的缺口表與 closeout 把這批（連同 18 HARD）列在 144 HOLD 內，使留存風險清單與 artifact 相反。依「案級 PASS 依賴未綁 oracle 或自比即 REJECT」，本輪不予接受；修法很小：E00 POS 改比 `compact(source_payload)==payload_sha`，E00 NEG 補 `STATE_CONFLICT` 並比對 first_fail，closeout §05 按 artifact 重算 HOLD 構成，route 查表補 `R3-REGISTRY-Q1::` 前綴。

VERDICT: REJECT
MANDATORY_FINDINGS: 3
