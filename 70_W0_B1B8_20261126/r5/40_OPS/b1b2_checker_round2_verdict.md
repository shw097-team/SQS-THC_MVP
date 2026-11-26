# B1/B2 分離 Checker Verdict — round 2（change cone）

## 0｜身分、範圍、唯讀紀律

- **受檢 change cone**：`20_DEV/b1_r5/{b1_engine.py, b1_tqaep.py}`、`20_DEV/b1_r5/{b2_engine.py, b2_tqaep.py}`，產物 `40_OPS/{b1_r5_tqaep.json, b1_r5_run_all.json, b1_r5_run_base.json, b1_r5_run_fda.json, b2_r5_tqaep.json, b2_r5_receivers.json, b1b2_r5_CANDIDATE_MANIFEST.tsv, b1b2_r5_candidate_freeze.json}`，以及 `spec_delta_r5/CODEX_FINAL`（manifest `3c816deb…bfa046`）與 carrier `463dcf33…4b3e1`。
- **本輪只判「原 finding 是否真正開合」與「修補是否引入新缺陷」**，不重開上輪已判定的 spec／digest 層。
- **SoD 声明（必須明說）**：本 Checker 與 Maker **同一模型軸**；本輪只建立 context／session 分離，**model-axis SoD 未建立**。本裁決可作技術反駁，**不能當獨立第三方（R16）**，也不構成任何原 Reader／Owner 接受。
- **方法**：全部用自寫 stdlib 解析器重算（`UNIT_BEGIN`、`R5_CASE_PARAMETERS`、carrier 註冊列、compact-JSON SHA256、`git cat-file`／`rev-parse` 唯讀）。**未 import Maker 任何模組作 oracle**；Maker CLI 只當受測產品執行兩次（`--op FDA`、`--op BASE`）。
- **唯讀紀律**：受檢檔、SQS-THC、FHS、知識庫全程唯讀（僅讀 bytes／sha／git 物件）；無網路、GUI、broker、lease。**只寫本目錄兩個檔**：本檔與 `b1b2_checker_round2_recompute.json`。
- 所有數字見 `b1b2_checker_round2_recompute.json`（下稱 RECOMPUTE）。

## 1｜逐 finding 結論表

| ID | 上輪 finding（一句） | 本輪判定 | 一句理由 |
|---|---|---|---|
| **B1-F01** | broker_live_submit 的 POS/NEG 建在常數 dict 上，spec 禁「常數冒 read control 成功」 | **PARTIAL** | NEG 的 deny 已真的由 carrier bytes 決定（YAML L24＋flip probe 分岔）；**POS 的 read-control 仍是字面常數**，且未檢 spec 指定的 POS oracle（deny invariant）。 |
| **B1-F02** | 18 BASE NEG 的 arm2 用跑後修正 oracle＋無關硬編碼 commit，pass 必然真 | **PARTIAL** | oracle 已預先宣告、foreign commit 存在性已記錄；**但 arm2 仍與 arm1 合取決定 PASS**，10/18 的 observed 是 harness 自造 status＋字面 `None`，且 `FOREIGN_AS_LOCAL_REFUSED` 在 spec 出現 **0 次**。 |
| **B1-F03** | BASE POS 無 FAIL 分支、DIRECTORY/UNTRACKED 也 PASS，與 missing_targets=10 矛盾 | **CLOSED** | 006/007/008/009/011 已改 PARTIAL、018 HOLD；PASS 案個個有非 null raw_sha；10 個 missing 與 5 PARTIAL＋1 HOLD 對得起來；FAIL 分支存在（`b1_tqaep.py:144-145`）。 |
| **B2-F1** | 2,788 案記 PASS（含 Q 列），PASS 詞義暗示語義接受 | **STILL OPEN** | 只把字改成 `PASS_VERBATIM_ROW`：**行為未變**（同一 1,385 次比對、同一桶位），仍在 2,930 產品案表形成 94.5% PASS-family；spec 對同 unit 的 `actual=NOT_EXECUTED`（B2 L46826）、`carrier_result=…NOT_SEMANTIC_ACCEPTANCE`（L46837），L429 明禁「拿 VERBATIM_ONLY 冒接收」。 |
| **B2-F2** | 18 HARD POS 用未定義 PASS_PRESERVED、observed=original 自比 | **CLOSED** | 18 POS 全 HOLD（`b2_tqaep.py:108-112`），`PASS_PRESERVED` 已從 verdict 表消失。殘留 P3：`op_hard` 仍吐 `preserved:80`／observed=original。 |
| **B2-F3** | 18 HARD NEG 常數 gate、18 案 actual 相同、僅 9/18 對應原 mutation | **CLOSED** | 18 NEG 全 HOLD（`:115-119`）並記 `mechanical_guard`；不再由常數 gate 產生 PASS。殘留 P3：18/18 guard=`NOT_APPLICABLE`，連機械臂都沒被行使。 |
| **B2-F4** | B3 取 `source_payload[2]` 當 requiredness，991/1385 非 requiredness → 假綠 1385 | **PARTIAL** | 991 的 index 錯誤已修（Q1@col2 353、Q2@col5 353 都是真的 requiredness 欄）；UNKNOWN 真的被拒（585 Q＋80 非 Q＝665）。**但 token 掃描把 Q3 的「Kind applicability」值 `CONDITIONAL` 當 requiredness，94 列照樣 ACCEPT**。 |
| **B2-F5** | RETURN 只送 1385 key，未送 80 個 HARD/E00/ROUTE | **CLOSED** | TRS＝1385＋80＝1465（`b2_tqaep.py:145-166`）；B3 total 1465、B5 total 1465，80 個非 Q key 兩邊都在。 |

## 2｜逐 finding 證據

### B1-F01｜PARTIAL
- **已真變的部分**：`b1_engine.py:467-487` 從 allow-list 指定的 `FDA_DESKTOP_CAPABILITY_MATRIX.yaml` 讀 raw bytes、先比對 pinned raw SHA，再以 `\s*live_broker:\s*(\S+)` 取行。我自行重算：該檔 `9406456db853…c863d6c4`／11,110 bytes，`live_broker` **全檔只出現 1 次**，在 **L24：`live_broker: DENY_ALWAYS`**；CLI 輸出 `policy:{value:DENY_ALWAYS,line:24,sha256:9406456d…}` 與我算的一致。
- **決策真的依賴 policy**：`b1_engine.py:503-509` `policy_value=="DENY_ALWAYS"` → `FIN_ORDER_DENY_ALWAYS`；否則 → `NO_CONNECTOR_PRESENT`。實跑 flip：`submit@DENY_ALWAYS → DENY/FIN_ORDER_DENY_ALWAYS`、`submit@ALLOW → DENY/NO_CONNECTOR_PRESENT`，**不同 first_fail** → 非常數。這部分成立。
- **未開合的部分**：POS 走的是 `action=="read"` 分支（`:500-502`），回 `ALLOW_READ_CONTROL` 是**字面常數**，不讀任何 broker/connector 狀態。`b1_tqaep.py:215-221` 的 POS PASS 條件就是 `decision=="ALLOW_READ_CONTROL"` ＋ `order_path_reached is False`（兩者皆常數）＋ policy 值回聲 → **任何 policy 值下 POS 都 PASS**。spec L510 對本 slot 的 POS 明訂「submit 的 POS 是必拒安全不變量」並禁「用常數同時冒 read control 成功」；Maker 的 POS 既用常數冒 read control，又沒檢它自己的 POS oracle（deny invariant 只出現在 NEG 案）。
- 附帶：`b1_engine.py:576` 的 `live_broker_policy` 摘要字串是字面 `"DENY_ALWAYS (submit/replace/cancel permanently refused)"`，與解析值無關。

### B1-F02｜PARTIAL
- **已修**：`b1_tqaep.py:268-272` 於模組層、`main()` 執行前宣告 `IDENTITY_STATUSES`／`ARM2_ORACLE`／`ARM2_ACCEPTED_STATUSES`／`FOREIGN_COMMIT`（不再是跑後修正）；arm2 記錄 `oracle_predeclared`、`accepted_statuses_predeclared`（4 個 status）、`foreign_commit_present_locally`（10 案 False）。我另以 `git cat-file -e 0489ac84…^{commit}` 確認該 commit 本地不存在、repo 無 remote（`git remote -v` 空）。
- **未開合**：`b1_tqaep.py:187` 仍是 `PASS if arm1 and arm2`，**arm2 仍進入 PASS 判定**（上輪要求「改回 arm1 單獨裁定、arm2 另立標籤」未做）。且 18 案中有 **10 案（BASE-001..008,010,011）走 `:168-173` 的 foreign-commit 分支**：`status` 由 harness 依 `present is None` 自行組字串、`commit/blob/raw_sha256` 是**字面 `None`**，產品函式完全沒被呼叫 →「probe 無非 null 身分」是**建構出來的**，不是觀測。其 `expected_first_fail: FOREIGN_AS_LOCAL_REFUSED` 在 B1 正文與證據型附錄各出現 **0 次**。
- 另外 8 案（BASE-009,012..018）走 `:165-166` 的 `resolve_target(..., "repo:"+rel)`，是真產品函式，這部分是真觀測。

### B1-F03｜CLOSED
- `b1_tqaep.py:128-145`：`identity_ok = all(status ∈ {TRACKED, TRACKED_CONTENT_MATCH, ALLOWLIST_VERIFIED} and raw_sha256)`；`NOT_IN_OWNER_ALLOWLIST → HOLD`；未達 identity → `PARTIAL`；無 target → `FAIL`。
- 實資料：006（3×DISK_DIRECTORY）、007/008/011（DISK_BUT_UNTRACKED）、009（TRACKED glob＋2×DISK_BUT_UNTRACKED）＝PARTIAL；018（`tests/test_fda_*` 不在 owner allow-list）＝HOLD。12 個 BASE POS PASS 的每個 target 都有非 null `raw_sha256`（我逐案掃，0 例外）。
- 與 `read_set_summary.missing_targets=10` 的關係現在自洽：10＝6 DISK_BUT_UNTRACKED＋3 DISK_DIRECTORY＋1 NOT_IN_OWNER_ALLOWLIST，正好對應 5 PARTIAL＋1 HOLD。
- 殘留（另立新 finding N-02）：`ALLOWLIST_VERIFIED` 這條路的 identity 沒有和 allow-list pinned raw SHA 比對。

### B2-F1｜STILL OPEN
- 產物：`verdict_counts = {PASS_VERBATIM_ROW:1385, PASS:1385, HOLD:160}`；2,770/2,930＝94.5% 仍是 PASS-family。
- 行為沒變：`b2_tqaep.py:88` 的判斷條件與上輪完全相同（`e["decision"]=="VERIFIED"` → 綠），只是標籤換字；Q POS 的 `actual` 仍是 carrier line／key／row／payload_sha 的文件層比對。
- spec 對同一 unit 的立場：§05.R5_PARAMETERS `B2.U0081` `"actual":"NOT_EXECUTED"`（B2 正文 **L46826**）、`"carrier_result":"EXACT_ORDERED_JSON_EQUAL_NOT_SEMANTIC_ACCEPTANCE"`（**L46837**）；§06.R5.4（**L107948**）「Actual/exit/raw/readback/Reader/ACK 均 NOT_EXECUTED」；§06.R5.5（**L107949**）文件層結果另名 `DOC.REG.*` 且「**不計入2990產品 Case**」；L429 明禁「拿 exit0／0 FAIL／**VERBATIM_ONLY 冒接收**」。
- 因此：`PASS_VERBATIM_ROW` 在 spec 出現 0 次、仍是 PASS 前綴、仍留在產品案表與 `verdict_counts` 內，**沒有把 1,385 個 NOT_EXECUTED 產品案移出 PASS 類**。詞義收窄（note 已寫「not a semantic PASS」）是改善，但不是行為真變。

### B2-F2｜CLOSED
- `b2_tqaep.py:108-112` 18 個 HARD POS 一律 HOLD，note 直寫「observed would be derived from the same record … self-comparison」；verdict 表不再有 `PASS_PRESERVED`（全檔 0 筆）。
- 殘留（P3，另列 N-05）：`b2_engine.py:170-186` 仍輸出 `observed_requiredness=req`、`requiredness_preserved: True`，`op_hard` 摘要仍是 `preserved:80`；且 18 筆 HARD POS 記錄同時有 `derived_requiredness:"UNKNOWN"` 與 `emitted:{original:"HARD",observed:"HARD"}`（兩套推導互相矛盾）。

### B2-F3｜CLOSED
- `b2_tqaep.py:113-119` 18 個 HARD NEG 一律 HOLD，記 `mechanical_guard` 與 mutation 字串；不再有常數 gate 產生的 PASS。
- 殘留（P3）：18/18 `mechanical_guard.decision = NOT_APPLICABLE`（因為 HARD unit 的 item-level 推導是 UNKNOWN），mutation 記成 `UNKNOWN -> OPTIONAL` —— 即機械臂在 18 案上其實一次都沒被行使，只是不再冒 PASS。

### B2-F4｜PARTIAL
- **已修**：`b2_tqaep.py:30-44` 改逐 item 掃 token，不再硬取 index 2。我自行分類 1,465 unit：Q1 的 token 落在 **col2**（353 案）、Q2 落在 **col5**（353 案），兩欄的值域與 Q1 Requiredness 欄一致（OPTIONAL/CONDITIONAL/HARD/EVAL_ONLY）→ 這 706 案的 requiredness 是真欄位。
- **UNKNOWN 真的被拒**：585 個 Q_UNKNOWN ＋ 80 個非 Q_UNKNOWN 全部 `REJECT`（`b2_engine.py:235-236`），我的推導與 B3 的 1,465 個決定 **0 不一致**。
- **未開合**：Q3 的 token 落在 **col1**，而 col1 是 **Kind applicability** 欄（DESIGN_APPLICABLE 181／`CONDITIONAL` 94／NOT_APPLICABLE_UNTIL_PD 50／INDIRECT_ONLY 35／NOT_APPLICABLE_TO_NATIVE_COMPOSITION 14／BLOCKED_EFFECT 4）。Maker 把 applicability 的 `CONDITIONAL` 當 requiredness，**94 列因此 `ACCEPT_FOR_DRAFT`**。carrier L7 明訂「Q1 Requiredness、Q2 AdmissionDecision、Q3 Kind applicability 及 Q4 Golden 是四個不同維度，不能互蓋」；B2 L429 要求「requiredness 保持原 namespace/polarity/Consumer/來源 scope」。→ 假綠從 991 降到 **94**，不是 0。

### B2-F5｜CLOSED
- `b2_tqaep.py:145-166`：TRS＝qres 1,385 ＋ hard/e00/route 80 ＝ **union_emitted 1,465**；`receivers` B3 total 1,465、B5 total 1,465；80 個非 Q key 在 B3 以 `source_row=None` 被拒、在 B5 亦在拒絕名單內（我逐 key 對過）。RETURN 完整性已補。

## 3｜新 finding

| ID | mandatory | severity | 事實（file:line） |
|---|---|---|---|
| **B1C-R2-N01** | **是** | P2 | **凍結的 `b1_r5_run_base.json` 不是凍結碼可重現的**。該檔（manifest 成員，sha `b56b3b19…`／41,729B）`base.entries` = **30 筆，含 7 筆 `kind:"FDA"`**；同一次 freeze 的 `b1_r5_run_all.json`（21:17）＝23 筆（BASE 18＋KERNEL 5）；現行 `b1_engine.py:373-374` 對非 BASE/KERNEL 一律 `continue`，我實跑 `--op BASE` 得 23 筆。檔 mtime 20:57 < `b1_engine.py` 21:16 → 此收據由**舊引擎**產生，與凍結碼不成對。 |
| **B1C-R2-N02** | 否 | P2 | `resolve_target` 的 ext 分支（`b1_engine.py:291-306`）只檢查 path `in allowed`，**沒有把讀到的 bytes 與 allow-list 的 `raw_sha256` 比對**，就把 `ALLOWLIST_VERIFIED` ＋自算 sha 回傳；`op_base` 也只對有 `disk_sha256` 的 target 掛 `locator_binding`，所以這 6 個 PASS（BASE-012..017）的記錄裡**沒有 expected/observed sha 對照欄**。今日 13/13 外部 carrier 與 pin 相符（我實算），故無現行假綠，但 carrier 改一個 byte 仍會 PASS。 |
| **B1C-R2-N03** | 否 | P2 | FDA op 自報 `disposition:"COMPLETE_NO_MISSING"`（我實跑），而 7 個 slot 全部帶 `missing`（`b1_cli.py:68-76` 只統計 base 的 missing）。且 `b1_engine.py:567-568` 對 broker_live_submit **覆寫** `missing` 為 `allowed_effect_pos`，使該 slot 獨有的 `slot_action_artefact_mapping: UNVERIFIED`（其餘 6 個 slot 都還留著）消失 —— 正是本次受修 slot 的缺因被稀釋。 |
| **B1C-R2-N04** | 否 | P3 | `b1_engine.py:576` `live_broker_policy` 是字面字串；`:482-486` 只取**第一個** `live_broker:` 行（今日僅 1 行，屬硬化提醒）。 |
| **B2C-R2-N05** | 否 | P3 | 兩套 requiredness 推導並存且互相矛盾：`b2_engine.py:151-157`（payload 序列化字串 substring）對 18 個 HARD unit 回 `HARD`，`b2_tqaep.py:30-44`（item-level）回 `UNKNOWN`；18 筆 HARD POS 記錄同時出現兩個值。 |
| **B2C-R2-N06** | 否 | P3 | `derived_requiredness` 詞彙表只有 5 個 token，但 Q1/Q2 的 requiredness 欄值域有 36 種：**Q1 87 列、Q2 160 列**（`SOFT`、`SOFT/CONDITIONAL`、`N_A`、`EVAL_ONLY_*`、`BASE_REQUIRED*`、`ROUTE_ONLY_NOT_TOOL_REQUIREDNESS`…）被判 UNKNOWN 而拒收。方向保守（不會假綠），但「UNKNOWN」不等於「原列無 requiredness」，B3 的可收集合被低估。 |
| **B2C-R2-N07** | 否 | P3 | receiver 收據不含被檢值：`b2_r5_receivers.json` 的收據 13 欄沒有 `requiredness`／`source_row`，ToolReadSet 本身也沒落盤 → 800/665 的逐案理由**無法只憑交付物重算**（我是用 spec 自行重推才對上）。另 B3/B5 彙總仍只寫 `accepted/rejected`，未帶 `ACCEPT_FOR_DRAFT` 限定詞（上輪 F-07 未改）。 |

## 4｜重算表（題目 1–8）

| # | 必驗項 | 我的重算（自寫程式／實跑 CLI） | 判定 |
|---|---|---|---|
| 1 | guard 決策是否依 policy；YAML 行號與值 | `b1_engine.py:503-509` 有 `policy_value=="DENY_ALWAYS"` 分岔，兩支 first_fail 不同（FIN_ORDER_DENY_ALWAYS／NO_CONNECTOR_PRESENT）；YAML **L24 `live_broker: DENY_ALWAYS`**，全檔僅 1 次，sha `9406456d…`／11,110B，與 allow-list 相符 | **PASS**（deny 側）／POS 側見 F01 |
| 2 | 實跑 `--op FDA` 與一份 BASE | FDA：exit 0、`artefacts_verified 16/16`、policy 區塊如宣稱、`deny_control` 三臂＋未知 action 皆 `DENY/FIN_ORDER_DENY_ALWAYS`、flip=`NO_CONNECTOR_PRESENT`、`gui/lease/broker=false`、`disposition COMPLETE_NO_MISSING`（見 N-03）。BASE：exit 2、23 entries、`missing_targets 10`、`disposition PARTIAL_SPLIT_PER_KEY` | **PASS（輸出如宣稱）** |
| 3 | b1 TQAEP：集合、逐案一致、PASS 不含 006/007/008/009/011、5 PASS 抽樣、HOLD/PARTIAL 全核、flip probe | 60/60，case 集合與 §06 表双向 0 差集，`expected_first_fail` 60/60 與表相符，verdict 重數＝檔案宣稱；BASE PASS 者皆非 006/007/008/009/011。抽 5 PASS：POS.BASE-001（TRACKED，raw=04.K2 期望）✔、POS.BASE-013（ALLOWLIST_VERIFIED，raw 與 pin 同）✔但見 N-02、NEG.BASE-001（arm2 自造）✘、NEG.broker（三臂＋flip）✔、POS.KERNEL_fsdt（PASS_EVIDENCE＋D-4 HOLD）✔。6 HOLD＋5 PARTIAL 皆有 `hold_reason`，理由與 actual 相符 | **PASS（結構）／案級見 F02** |
| 4 | NEG BASE arm2：oracle 預先宣告、非必然真、accepted 清單、foreign flag、probe 無非 null 身分 | `oracle_predeclared` 18/18、accepted_statuses 4 個、`foreign_commit_present_locally=false` 10 案有記錄、所有 probe 的 commit/blob/raw 皆 null；**但** 18/18 pass=True、10 案 status 由 harness 組成（`:169`）、`:170-172` 三個欄位是字面 None | **PARTIAL（見 F02）** |
| 5 | b2 TQAEP：2930、verdict 分佈、0 orphan、HARD/E00/ROUTE 不再 PASS、derived requiredness 40 抽樣 | 我自行解析：1,465 unit／2,930 case、uid `d54bdd4a…`／cid `30592c71…` 全等、雙向 orphan 0；verdicts `{PASS_VERBATIM_ROW 1385, PASS 1385, HOLD 160}` 與逐案重數一致；HARD/E00/ROUTE **0 個 PASS**（36/16/108 全 HOLD）。20 UNKNOWN 抽樣：Q1 `SOFT/CONDITIONAL`、Q2 `ROUTE_ONLY_NOT_TOOL_REQUIREDNESS` 等（皆拒）；20 非 UNKNOWN：Q1 col2 `HARD`/`CONDITIONAL`、Q2 col5（皆收）；**Q3 col1 applicability 的 `CONDITIONAL` 94 案也被收 → 判為誤收** | **PASS（結構）／FAIL（requiredness 語義，見 F4）** |
| 6 | receivers：B3 800/665、B5 0/1465、20 抽樣與 requiredness 一致、UNKNOWN 真被拒 | B3 `ACCEPT_FOR_DRAFT 800`／`REJECT 665`（合計 1,465）；B5 `REJECT 1,465`。我用自己的推導對 1,465 筆做全量比對，**0 不一致**；UNKNOWN **全數被拒**；Q3 94 筆雖被收但值來自 applicability 維度 | **PASS（機制）／殘餘 94（F4）** |
| 7 | manifest／freeze：逐行 sha/bytes、循環 | 19/19 sha 與 bytes 全等；freeze 的 manifest sha `af9b203f…`／1,870B 與實檔一致；**freeze receipt 不在 manifest 內**、manifest 不自列；allowlist／locators／carrier／repo HEAD 四個 input sha 全等 | **PASS**（但 manifest 內含 N-01 的不可重現收據） |
| 8 | 新缺陷掃描 | 發現 N-01（凍結收據不可重現）、N-02（ext identity 未錨定）、N-03（disposition／missing 稀釋）、N-04～N-07（常數摘要、雙推導矛盾、詞彙缺口、收據不可審）。未發現「把 PARTIAL 併入 PASS」、「把 HOLD 稀釋為 N/A」、「把 draft 寫成 ACK」、「宣稱 B1/B2_ACCEPTED」 | **見 §3** |

## 5｜我無法重算的（不猜）

1. **Maker 的 full run 是否逐字如實**：我只實跑 FDA／BASE 兩個 op，未重跑 TQAEP；TQAEP 的逐案值以「與我獨立重算對撞」佐證（Q 列 1,385/1,385、carrier 1,385 列、B1 60 案集合與 FirstFail 60/60）。
2. **`b1_r5_edge_sec.json` 9 案**：不在 change cone，本輪未重跑（freeze 宣稱 9/9 pass 未驗）。
3. **B2 Q NEG 的變異廣度**：上輪 F-06（payload/requiredness 子臂未施加）不在本次 cone，未重驗；本次只確認 1,385 個 NEG 皆由 `NAMESPACE_JOIN_DENY` 取得 PASS。
4. **Q3 欄位語義的原 Header**：carrier 只說「原欄位（按序保留）」無欄名，我是以「Q3 註冊節＝Kind applicability、col1 值域 6 個狀態且不含 requiredness 詞彙」判定 col1 非 requiredness；原始 EVID_R1 表頭未取得。
5. **0 個 mandatory 的「原 Reader／Owner 接受」**：本輪不涉及，維持 NOT_ESTABLISHED。

## 6｜對本輪結論的淨影響

- 真修好的：**B1-F03**（POS 不再以 status 白名單發 PASS，10 個 missing 與 verdict 自洽）、**B2-F2/F3**（自比與常數 gate 不再產生 PASS）、**B2-F5**（1,465 union 已交付）、**B1-F01 的 deny 側**、**B1-F02 的「跑後改 oracle」**、**B2-F4 的 index 991**。
- 仍未開合：**B1-F01 POS 常數 read-control**、**B1-F02 arm2 仍決定 PASS（10/18 自造 observed）**、**B2-F1 只換詞（1,385 個 NOT_EXECUTED 案仍在 PASS 類）**、**B2-F4 仍有 94 案以 applicability 值通關**；另有 **N-01 凍結收據不可由凍結碼重現**。
- 因此本輪仍不得升格：不是「證據不足」，而是 **case-level PASS 仍依賴 Maker 自造／錯維度的 oracle**（B1 18 案、B2 1,385＋94 案）。

VERDICT: REJECT

MANDATORY_FINDINGS: 5
