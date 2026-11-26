# B2 分離 Checker Verdict（r5）

## 0｜Scope 與 Checker 身分

- **受檢對象**：`spec_delta_r5/CODEX_FINAL`（FINAL_SPEC_MANIFEST.tsv＋B2 實質正文 12,549,483 bytes）、carrier `SST_PLP_共用實質正文_工具合約_2026-11-23_r2.md`、Maker 產物 `20_DEV/b1_r5/b2_engine.py`、`20_DEV/b1_r5/b2_tqaep.py`、`40_OPS/b2_r5_tqaep.json`、`40_OPS/b2_r5_receivers.json`。
- **Checker 身分**：分離唯讀 context，與 Maker 不同 session；**未 import 任何 Maker 模組**，以自寫 stdlib 解析器重算（UNIT_BEGIN／R5_CASE_PARAMETERS／carrier 表列／compact-JSON SHA）。
- **SoD 限制（明列）**：本次分離只建立在 **context／session 分離**；Checker 與 Maker 同屬同一模型軸，**同一模型軸之 SoD 未建立**，本 verdict 不構成 R16 獨立驗證或原 Reader 接受。
- **寫入範圍**：僅本檔與 `b2_checker_r5_recompute.json`；受檢檔、受檢源碼樹、知識庫、SQS-THC、FHS 全程唯讀；無網路、GUI、broker、lease。
- **方法**：無語義猜測；無法重算者標 NOT_VERIFIED（本輪無此類項）。

## 1｜重算表 A–F

| # | 項目 | expected（Maker／spec 宣稱） | observed（本 Checker 獨立重算） | 判定 |
|---|---|---|---|---|
| **A** | manifest 四檔 raw SHA256／bytes | 4 檔全等；manifest 自身 `3c816deb…bfa046`／666 bytes | 4/4 SHA 與 bytes 全等；manifest 自身亦全等 | **PASS** |
| **B** | Unit／Case 集合與 kind 分佈 | 1465 unit、2930 case；`d54bdd4a…8634e8`／`30592c71…6dd5`；Q 1385／HARD 18／E00 8／ROUTE 54；unit.case_ids 全在 case 表 | 1465／2930；uid set `d54bdd4a…8634e8`；cid set `30592c71…6dd5`（由 unit.case_ids 與 R5_CASE_PARAMETERS 兩路各自算出同值）；kind 1385/18/8/54；缺漏 0、orphan 0、每 unit 恰 2 case | **PASS** |
| **C** | carrier 身分＋Q 原列逐列核對 | raw `463dcf33…4b3e1`／767859 bytes；R3-REGISTRY-Q* 列 1385；1385 案 key／row／payload_sha 全等 | SHA／bytes 全等；2,391 physical lines 中 Q 列 1385（Q1 440／Q2 513／Q3 378／Q4 54）；**verified 1385／mismatch 0／missing 0**；1,385 條實體行 1:1 用盡、無重複 key | **PASS** |
| **D** | TQAEP 逐案 | case_count 2930；verdict_counts 與逐案一致；無 orphan；PASS 真滿足原義務 | 算術一致（PASS 2788＋PASS_PRESERVED 18＋HOLD 124＝2930；orphan 0；case 表與 params 雙向 0 差集）→ **算術 PASS**；**PASS 語義 FAIL**（見 F-01／F-02／F-03） | **FAIL** |
| **E** | B3／B5 接收 | B3 接受 1385、B5 全拒 1385；不得把拒絕寫成接受、不得把 draft 當 ACK | 數字相符但**正確性 FAIL**：B3 的 mandatory `requiredness` 有 991/1385 非 requiredness 值（見 F-04）；B3／B5 只收到 1385，非 spec 要求的 1465 union（見 F-05）；B5 全拒方向正確 | **FAIL** |
| **F** | 禁止宣稱掃描 | 不得宣稱 B2_ACCEPTED／工具已安裝／license-ABI 已核／B5 選型完成 | 四類皆未宣稱（`INSTALLED` 0、`license` 0、`abi` 0、無選型完成字樣；`B2_ACCEPTED` 僅出現在否定句 claim_ceiling） | **PASS** |

### D 的四個質疑（逐一回答）

1. **1385 Q POS 的 PASS 是否只靠 payload SHA 相等就夠？**
   機械重算是真的（1,385/1,385 逐 key／row／physical line／compact-JSON SHA 全等），**但不足以支撐產品 Case 的 PASS**。該 Case 在 §06.0（正文 L105166）列尾是 `EXPECTED_NOT_OBSERVED`，§05.R5_PARAMETERS/B2.U0081 是 `actual=NOT_EXECUTED`、`runtime_baseline=UNBOUND_ORIGINAL_FIXTURE`、`carrier_result=EXACT_ORDERED_JSON_EQUAL_NOT_SEMANTIC_ACCEPTANCE`；spec §06.0（L105001）明言本輪未執行產品 Case，§06.R5.1（L107945）「它可驗文件完整性，不是原 runtime valid fixture…setup 不成立不得 NEG PASS」。原義務「Q 原列逐欄保持」在文件層被滿足，在產品層未被執行；且 carrier 第 4 欄（當期規範狀態）不在 payload 內、Q1–Q4 維度語義亦未評，與附錄 §03（L103）「只證文件保全及載體讀取，不是更底層 requiredness 語義或原 Reader 接受」一致。以 `PASS` 命名即為高報（F-01）。
2. **18 個 HARD 的 PASS_PRESERVED 是否被算進 PASS？**
   否——`verdict_counts` 將 PASS 2788 與 PASS_PRESERVED 18 分開，未稀釋進 PASS bucket。但 `PASS_PRESERVED` 在 B2 正文出現 **0 次**，不是 spec 的 verdict 類別；其實質是 requiredness 自比（`b2_engine.py:170-186`），依 §04.R5.MANDATORY（L107948）與 V02 應為 HOLD。此項以 F-02 列 mandatory。
3. **124 個 HOLD 是否被任何地方當成 PASS 或稀釋為 N/A？**
   否。HOLD 124＝E00 16＋TECH_ROUTE 108，逐案保留、未被寫成 PASS／N/A，亦未進入 receiver（receiver 只吃 Q）。此子項合格。
4. **逐案一致性／orphan？**
   一致：case 表 2930 與 R5_CASE_PARAMETERS 雙向 0 差集、unit_id 0 不符、verdict 合計 2930、orphan 0。

## 2｜Findings

### F-01｜mandatory｜HIGH
- **file:line**：`20_DEV/b1_r5/b2_tqaep.py:68, :76, :91`；`40_OPS/b2_r5_tqaep.json`（case_count 2930、verdict_counts）
- **事實**：2,788 個產品 Case 被寫成 PASS（Q POS 1385／Q NEG 1385／HARD NEG 18），而同一 Case 在 spec §06.0 列尾為 `EXPECTED_NOT_OBSERVED`（正文 L105166、L105167），§05.R5_PARAMETERS/B2.U0081 為 `actual=NOT_EXECUTED`、`runtime_baseline=UNBOUND_ORIGINAL_FIXTURE`；§06.R5.1（L107945）與 §06.R5.4（L107948）明定文件 baseline 不是原 runtime fixture、「只比自身不能 PASS」；§06.R5.5（L107949）要求文件層結果另名 DOC.REG.* 且**不計入 2,990 產品 Case**；附錄 §05（L131）原 claim ceiling 為 `ROW_PAYLOAD_PIN_INTEGRITY_AND_CLAUSE_SPAN_IDENTITY`。
- **影響**：文件層 carrier 定位結果被計入 2,930 產品 Case 表並以 PASS 命名，形成 95.2% 產品通過率的印象；超出 spec 自訂 ceiling，屬把未綁產品 oracle 的 key 當 PASS。

### F-02｜mandatory｜HIGH
- **file:line**：`20_DEV/b1_r5/b2_engine.py:170-186`（`observed_requiredness = original_requiredness`）、`:176`（payload_sha 僅回填）
- **事實**：18 個 HARD POS 的 observed 與 original 同源自該 unit 自己的 `source_payload`，屬 §04.R5.MANDATORY（L107948）所列「自己欄自比」；HARD 單元全程未做 payload 逐欄核對、`payload_sha` 從未重算（80 個非 Q unit 的 payload_sha 皆未被任何 op 驗證）。18 案 actual 完全相同（僅 1 種）。`PASS_PRESERVED` 非 spec verdict（正文 0 次）。V02（L51）要求真 Oracle 未具即逐 Case HOLD。
- **影響**：18 案由應為 HOLD 轉為非 HOLD，且無逐 key 鑑別力；原 HARD POS oracle「獨立原條文/原payload逐欄相等；滿足§05本key規則」（L105006）完全未被檢驗。

### F-03｜mandatory｜HIGH
- **file:line**：`20_DEV/b1_r5/b2_engine.py:194-201`（`guard_requiredness` 常數 order 表）；`20_DEV/b1_r5/b2_tqaep.py:90-92`
- **事實**：18 個 HARD NEG 一律施加 `HARD -> OPTIONAL` 並由寫死的 order 表回 DENY，18 案 actual 位元組完全相同（常數 gate）。spec §06.R5.HARD（L107955-107972）中僅 **9/18** 的原 mutation 是「原 HARD 被删除或无权启用」，另 9/18 為相異 mutation（`ABI_UNBOUND`／`SECOND_CANONICAL_PI`、`MAKER_SELF_ATTEST`、`PIT_LOOKAHEAD`、`TRACE_ORPHAN`、`NOT_RELEASED`…），從未被施加，違反 §06.R5.2（L107946）與 V02 禁常數 gate。同一 9 個 non-loss key 的 POS 註記自承 inner→outer 映射為 HOLD（`b2_tqaep.py:88-89`），NEG 卻宣 PASS 且 `first_fail=TOOL_REQUIREDNESS_HOLD`，正是 §06.R5.3（L107947）禁止的「未具映射把內層錯誤硬轉同一 wrapper」。
- **影響**：18 案 PASS 無鑑別力、與自身 POS 的 HOLD 陳述互相矛盾；原 inner functional failure 未被驗證。

### F-04｜mandatory｜HIGH
- **file:line**：`20_DEV/b1_r5/b2_tqaep.py:126`（`req = payload[2].strip("`")`）；`20_DEV/b1_r5/b2_engine.py:232-244`（只檢查非空）
- **事實**：B3 mandatory 欄 `requiredness` 取自 `source_payload[2]`；獨立重算 **991/1385** 列的該欄不是 Q1 requiredness——Q2 513（`REUSE_SELECTED` 209／`DEFER_WITH_TRIGGER` 126／`ADAPT_WHEEL` 116／`RESEARCH_ONLY` 62）、Q3 378、Q4 54 為自由文字、Q1 另有 46 列（含 `N_A` 9、`REFERENCE/EVAL_ONLY` 3…）。receiver 僅檢查非空即 `ACCEPT_FOR_DRAFT`，故 accepted=1385／rejected=0。值亦變形：原字串 `` `\`DEFER_WITH_TRIGGER\`` `` → 送出 `\`DEFER_WITH_TRIGGER\`。§01（L83）明定 Q1 Requiredness／Q2 AdmissionDecision／Q3 Kind／Q4 Golden 四維度不能互蓋。
- **影響**：B3 的 1,385 個 draft readiness 中至少 945（68%）以錯誤語義欄位通過 mandatory 檢查；「0 拒絕」是過鬆檢查造成的假綠，而非真通過。

### F-05｜mandatory｜MED
- **file:line**：`20_DEV/b1_r5/b2_tqaep.py:119-133`
- **事實**：ToolReadSet 只由 `qres`（Q 1,385）建構後送 B3／B5；HARD 18＋E00 8＋TECH_ROUTE 54＝80 個 key 從未進入任何 receiver。spec §04.R5（L426）明定「1385＋HARD/E00/ROUTE union 精確等 1465」，§04.OPS（L313）RETURN 須把 ToolReadSet／RequirednessDelta／WheelMetadataRef 送 B3、B5。
- **影響**：B3 1385/0 與 B5 0/1385 僅覆蓋必要集合 94.5%；80 個未交付 key 既未計入拒絕、亦未計入 missing／HOLD，接收完整性被高報。

### F-06｜non-mandatory｜MED
- **file:line**：`20_DEV/b1_r5/b2_tqaep.py:73-79`
- **事實**：Q NEG 原 mutation 為「僅改原列payload/Requiredness**或**跨namespace替換」（L105167）兩個 sub-arm；Maker 只施加 namespace 替換並取得 `NAMESPACE_JOIN_DENY`，payload／requiredness 變異臂未執行，違反 §06.R5.2「多個 sub-arm 必分別單欄改」。
- **影響**：1,385 個 Q NEG PASS 各僅覆蓋一半宣告變異；PASS 廣度大於實測範圍。

### F-07｜non-mandatory｜LOW
- **file:line**：`40_OPS/b1b2_r5_candidate_freeze.json:57-61`；`40_OPS/b2_r5_tqaep.json` receivers 區塊
- **事實**：`b2_engine.py:252` 與 `b2_r5_receivers.json` 均註明 `ACCEPT_FOR_DRAFT` 非產品 ACK，但 freeze 與 tqaep 彙總只寫 `accepted:1385 / rejected:0`，未帶 draft 限定詞。
- **影響**：彙總層可能被讀成 B3 已接收；屬標示缺陷，非假 ACK。

### 其他觀察（非 finding）
- C 表的重算是真結果：1,385 列逐 key／row／physical line／payload SHA 全等，1,385 條 carrier 列 1:1 用盡、無重複 key、無未用列。缺陷在 verdict 命名與 ceiling，不在此步算術。
- B5 全拒方向正確（本輪未取得 metadata，Maker 亦未宣稱取得）；但 receiver 把空 list `missing=[]` 亦視為 mandatory 缺欄（`b2_engine.py:232`），屬語義 bug，恰好不改變 REJECT 結果。
- `PASS_PRESERVED`、124 HOLD 均未稀釋進 PASS／N/A；此二項合格。
- spec 自身：§06.R5.5 稱 DOC.REG 文件負例「可重現於配對附錄」，但 B2 證據型附錄 `DOC.REG` 出現 0 次——屬 spec 側可追溯性缺口，不計入本 verdict 之 mandatory 數。

## 3｜結論

A／B／C 三表獨立重算全等，F 表四類禁止宣稱均未出現；但 D／E 存在 5 項 mandatory 高報：2,788 個未執行產品 Case 被記為 PASS（F-01）、18 個 HARD POS 以自比記為未定義的 PASS_PRESERVED（F-02）、18 個 HARD NEG 以常數 gate 與非原 mutation 記為 PASS（F-03）、B3 以 991 列非 requiredness 值通過 mandatory 而成假綠（F-04）、RETURN 少送 80 個 key 仍宣 1385/0 接收集滿（F-05）。依「發現高報即 REJECT」之規則，本產品層不予接受。

VERDICT: REJECT
MANDATORY_FINDINGS: 5
