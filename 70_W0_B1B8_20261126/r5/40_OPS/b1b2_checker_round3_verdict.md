# B1/B2 分離 Checker Verdict — round 3

## 0｜分離声明、範圍、唯讀紀律

- **分離声明（必須明說）**：本 Checker 與 Maker **同一模型軸**。本輪只建立 context／session 分離，**model-axis SoD 未建立**。本裁決只作技術反駁，**不是獨立第三方（R16）**，不構成任何原 Reader／Owner 接受，也不構成 `B1_ACCEPTED`／`B2_ACCEPTED`。
- **受檢 change cone**：`20_DEV/b1_r5/{b1_engine.py, b1_cli.py, b1_tqaep.py, b2_engine.py, b2_tqaep.py}`；產物 `40_OPS/{b1_r5_run_base.json, b1_r5_run_all.json, b1_r5_run_fda.json, b1_r5_tqaep.json, b2_r5_tqaep.json, b2_r5_receivers.json, b1b2_r5_CANDIDATE_MANIFEST.tsv, b1b2_r5_candidate_freeze.json}`。
- **方法**：全部用自寫 stdlib 解析器重算（`UNIT_BEGIN`／`R5_CASE_PARAMETERS` JSON 區塊、B1 §06 60 列表、B2 §06 2,930 列表、carrier 註冊列、compact-JSON SHA256、`git cat-file`／`ls-tree` 唯讀）。**未把 Maker 任何內部函式當 oracle**；Maker CLI 只當受測產品實跑（`--op FDA`／`--op BASE`／`--op ALL`）。`b2_engine.op_qrows` 僅被當受測產品呼叫，**變異由我自行建構、期望值取自釘定 spec 列**。
- **唯讀紀律**：受檢檔、SQS-THC、FHS、知識庫全程唯讀（只讀 bytes／sha／git 物件）；無網路、GUI、broker、lease。檢查結束後重算 manifest 全部 20 個成員 sha256 → **與凍結清單逐字相同**。本輪只寫本目錄兩個檔（本檔與 `b1b2_checker_round3_recompute.json`）。
- 全部數字見 `b1b2_checker_round3_recompute.json`（下稱 RECOMPUTE）。

## 1｜逐 finding 裁決表

| ID | 上輪 | 本輪 | 一句理由 | file:line |
|---|---|---|---|---|
| **B1-F01** | PARTIAL | **CLOSED** | `fda_live_submit_guard('read')` 真的呼叫 `fda_live_broker_policy()`；該函式**先比對 pinned digest、不符即 `SOURCE_CHANGED` 中止**，再回傳 value/line/sha/bytes。我以「pin≠bytes」實跑：stdout `{}`、exit 2、`SOURCE_CHANGED`，read control 未產生；POS 也檢 `artefact_sha256==policy.sha256`、`artefact_line==policy.line`、`DENY_ALWAYS`、三臂皆 DENY | `b1_engine.py:484-492, 505-514`；`b1_tqaep.py:225-236` |
| **B1-F02** | PARTIAL | **CLOSED** | `verdict = "PASS" if arm1["pass"] else "FAIL"`，arm2 降為 `added_safety_arm`；arm2 對 repo 類 target **真呼叫** `resolve_target(..., FOREIGN_COMMIT, ...)`。實證：`B1.NEG.BASE-006` 的 arm2 `pass=false`（3×`DISK_DIRECTORY`）**仍然 PASS**，證明 arm2 不再參與裁定 | `b1_tqaep.py:147-197`（187-197 為關鍵） |
| **B2-F1** | STILL OPEN | **CLOSED** | 1,385 個 Q POS **一律 HOLD**，row identity 只留在 `actual` 作證據；`PASS` 1,385 恰等於 spec 宣告 `NAMESPACE_JOIN_DENY` 的案集（我逐案比對），`PASS_VERBATIM_ROW`／`PASS_PRESERVED` 在檔內 0 次 | `b2_tqaep.py:68-79` |
| **B2-F4** | PARTIAL | **CLOSED** | requiredness 只接受 **labelled**（dict 內 `requiredness` 鍵）；positional 一律 `UNKNOWN`，`UNKNOWN` 在 receiver 端強制列入 mandatory missing → **B3 0 收／1,465 拒、B5 0 收／1,465 拒**，上輪 94 筆 applicability 值全部不再被收 | `b2_engine.py:154-173, 252-255` |
| **N-01** | STILL OPEN | **CLOSED** | `b1_r5_run_base.json` = **23 entries（BASE 18＋KERNEL 5，無 `kind:FDA`）**；我用凍結引擎實跑 `--op BASE`，與凍結檔逐欄比對**只差 `invocation.out`**；sha `20dd226c…` 與 manifest 同 | `40_OPS/b1_r5_run_base.json` |
| **N-02** | STILL OPEN | **CLOSED** | `ALLOWLIST_VERIFIED` 改為計算 `pin_match = (obs == pinned)`，不符則 `ALLOWLIST_PIN_MISMATCH`；13/13 外部 target 的 `raw_sha256==pinned_sha256==allow-list pin`，我另以磁碟 bytes 自算相符 | `b1_engine.py:303-311` |
| **N-03** | STILL OPEN | **CLOSED** | CLI disposition 已計入 fda missing（排除 by-design `ABSENT`）→ 實跑 `PARTIAL_SPLIT_PER_KEY`（exit 2）；broker slot 的 `missing` 由覆寫改為 **append**，同時保留 `slot_action_artefact_mapping:UNVERIFIED` 與 `allowed_effect_pos:ABSENT` | `b1_cli.py:74-82`；`b1_engine.py:563-580` |
| **N-04** | STILL OPEN | **CLOSED** | `fda.live_broker_policy` 區塊改由解析後的 policy 物件組出（value/line/sha256），非字面；殘留：仍只取第一個 `live_broker:` 行（今日全檔僅 1 行，屬硬化提醒） | `b1_engine.py:588-590` |
| **N-05** | STILL OPEN | **CLOSED** | `derived_requiredness()` 只剩一條路徑（轉呼 `B.derive_requiredness`）；HARD 案的兩側現同為 `UNKNOWN`，上輪「HARD vs UNKNOWN」矛盾消失（殘留彙總見 N-09） | `b2_tqaep.py:27-28` |
| **N-06** | STILL OPEN | **CLOSED** | token 掃描已移除，不再有欄位被誤標；代價是 1,465 列全 `UNKNOWN` 而被拒（保守、無假綠；B3 因此 0 收） | `b2_engine.py:151-173` |
| **N-07** | STILL OPEN | **PARTIAL**（非 mandatory） | 收據已存 `checked_values`（requiredness/source_row/kind），但仍無「哪個 mandatory 欄缺」的清單，ToolReadSet 未落盤 → 逐案拒絕理由仍不能只憑交付物完整重算 | `b2_engine.py:256-273` |

結算：**CLOSED 10／PARTIAL 1／STILL OPEN 0**。

## 2｜新 mandatory finding

**無（0）**。Maker 沒有把 HOLD 算成 PASS、沒有把 PARTIAL 併入 PASS、沒有宣稱 `ACCEPTED`／`ACK`、也沒有把未綁 oracle 的結果寫成產品接受。三個 PASS 家族逐一綁定：

- B1 18 個 BASE NEG → spec §06 該列宣稱 `BASE_ROW_MISSING`（我自寫解析器 60/60 對得，且 18 個 key 的配對 POS 皆有 ≥1 declared target，arm1 不是空刪）。
- B2 1,385 個 Q NEG → spec §06 該列宣稱 `NAMESPACE_JOIN_DENY`；我自建 7 個 unit／13 個跨 namespace 變異（Q4、Q9）實跑產品，13/13 都回 `NAMESPACE_JOIN_DENY`。
- B1 12 個 BASE POS → 16 個 target 的 blob／磁碟 sha 與 bytes 我全數自算相符（repo blob 逐個對到 `ls-tree HEAD`）。

## 3｜新 finding（非 mandatory）

| ID | mandatory | severity | 事實 | 必要處置 |
|---|---|---|---|---|
| **N-08** | 否 | **P2** | **凍結的 `b1_r5_run_fda.json` 是修前引擎產物**（mtime 21:17 < `b1_engine.py` 21:35）。它仍自報 `disposition:"COMPLETE_NO_MISSING"`、`deny_control` 無 `artefact_sha256`/`line`、`slots[6].missing` 只有 `allowed_effect_pos`；與凍結引擎實跑有 **13 個欄位不同** | 以凍結引擎重跑該 op（或自 manifest 移除）。同一 op 在交付集內同時出現 `COMPLETE_NO_MISSING` 與 `PARTIAL_SPLIT_PER_KEY` 會自相矛盾 |
| **N-09** | 否 | P3 | `op_hard` 仍對 80 個 unit 一律吐 `decision:"PRESERVED"`、摘要 `preserved:80`，但每個 requiredness 都是 `UNKNOWN`（逐筆 `requiredness_preserved:None`） | 摘要改 `0/NOT_ESTABLISHED`，或只計已知 requiredness |
| **N-10** | 否 | P3 | `b1b2_r5_MAKER_NOTES.md` 未隨最後一跑更新：仍寫 B2 `PASS 1385＋PASS_VERBATIM_ROW 1385＋HOLD 160`（實檔 `HOLD 1545／PASS 1385`），並稱 `xs_compile` 有命中（我掃 16 檔與產品輸出皆 0） | 重寫自報表 |
| **N-11** | 否 | P3 | `B1.NEG.BASE-006` 的 arm2 被記 `added_safety_regression_failed`，但其 declared target 是目錄（`DISK_DIRECTORY`），屬「該臂不可評」而非「失敗」；不影響 verdict | 記 `NOT_APPLICABLE` |
| **N-12** | 否 | P3 | `rec["arms"].append(arm2)` 緊接被 `rec["arms"] = [arm1]` 覆寫，死碼 | 刪除 |

**關於 N-08 的升級判斷（明說）**：本輪紀律只承認三類 mandatory，N-08 不屬其中任一（無案級 PASS 依賴它、無 HOLD/PARTIAL 併入 PASS、它宣稱的是「完成」而非 ACCEPT/ACK）；且同一缺陷在「產品活著就吐」時，上輪已判 non-mandatory（N-03）。修後的 FDA 段落在 `b1_r5_run_all.json` 內**逐位元可重現**，故產品主張仍有錨。因此判 **non-mandatory**，但**它是交付面的必改項**：Owner 採納前必須重生該檔，否則凍結集自相矛盾。

## 4｜重算表（題目 1–8）

| # | 必驗項 | 重算結果 | 判定 |
|---|---|---|---|
| 1 | `fda_live_submit_guard('read')` 是否真讀 policy、sha 比對在 return 前 | `b1_engine.py:508` 呼叫 policy；`:484-486` pin 不符即 `EngineFault(SOURCE_CHANGED)`，位置在 `:487-491` 掃行與 `:511-512` 回傳之前。動態反證：pin 改錯 → exit 2、stdout `{}`、`SOURCE_CHANGED`，read control 不出現；pin 正確 → `ALLOW_READ_CONTROL`＋sha `9406456d…`／line 24／11,110B（與我獨立重算同） | **PASS** |
| 2 | 實跑 `--op FDA` | exit 2、`disposition PARTIAL_SPLIT_PER_KEY`、`artefacts 16/16`、`deny_control.pos_deny_invariant` 含 `artefact_sha256`/`artefact_line`/`artefact_bytes`、三臂＋未知 action 皆 `DENY/FIN_ORDER_DENY_ALWAYS`、flip=`NO_CONNECTOR_PRESENT`、`gui/lease/broker=false`；`slots[6].missing` = `slot_action_artefact_mapping(UNVERIFIED)` ＋ `allowed_effect_pos(ABSENT)` | **PASS** |
| 3 | `b1_r5_run_base.json` | 23 entries（18 BASE＋5 KERNEL，0 FDA）；statuses `ALLOWLIST_VERIFIED 13／TRACKED 7／DISK_BUT_UNTRACKED 6／TRACKED_CONTENT_MATCH 5／DISK_DIRECTORY 3／NOT_IN_OWNER_ALLOWLIST 1`；`missing_targets 10`；sha 與 manifest 同行一致；與凍結引擎實跑僅差 `invocation.out` | **PASS** |
| 4 | `b1_r5_tqaep.json` | 60 案、案集與 §06 雙向 0 差集、`expected_first_fail` 60/60 相符；18 BASE NEG 全部 `verdict = arm1`（`BASE-006` arm2 fail 仍 PASS）；broker POS/NEG 的 `actual` 均含 policy `sha256`＋`line 24`；12 個 BASE POS PASS 的 16 個 target 我自算 sha/bytes 全等（含 repo blob 對 `ls-tree HEAD`） | **PASS** |
| 5 | `b2_r5_tqaep.json` | 2,930 案、1,465 unit（1385/18/8/54）、orphan 0、案集＝spec 案集；`HOLD 1545／PASS 1385` 與逐案重數一致；Q POS 1,465 全 HOLD、HARD/E00/ROUTE 160 全 HOLD；`PASS` 集合**恰等於** spec `NAMESPACE_JOIN_DENY` 1,385 案集 | **PASS** |
| 6 | `b2_r5_receivers.json` | B3 `0/1465`、B5 `0/1465`；抽 10 筆（實為全量）`checked_values.requiredness` 全 `UNKNOWN`；`decision` 一律 `REJECT`、`first_fail` 一律 `MANDATORY_FIELD_MISSING`；`ACCEPT_FOR_DRAFT` 0 筆、全檔無 `ACK`（除「never a product ACK」說明句） | **PASS** |
| 7 | 新缺陷掃描 | 未見 HOLD→PASS、PARTIAL→PASS、宣稱 ACCEPTED、未綁 oracle 冒接受；`ACCEPT` 字樣僅出現在 `claim_ceiling` 的否定句。另發現 N-08～N-12（皆非 mandatory） | **PASS（0 mandatory）** |
| 8 | manifest／freeze | 20/20 行 sha 與 bytes 全等；manifest sha `75660aa3…`／1,970B 與 freeze 綁定值同；**freeze receipt 不在 manifest 內**（無循環）；spec manifest 4/4 全等；四個集合 digest（B1 30/60、B2 1465/2930）我自算皆與 artefact 宣稱同 | **PASS（含 N-08 成員瑕疵）** |

## 5｜無法重算的（不猜）

1. Maker 的整批 TQAEP 重跑本身：我沒有重跑，而是逐案以自寫 oracle 對撞（B1 60 案、B2 2,930 案全量比對），並實跑 3 個 op 與 13 個自建變異。
2. `b1_r5_edge_sec.json` 的 9/9：不在本 change cone，**NOT_VERIFIED**。
3. D-1／D-2／D-3／D-4／D-5、TT-UP-1/2、E00、ROUTE 的原權位缺口：Owner 域，本輪不動。
4. carrier 欄位的原始表頭語義（Q3 col1 是否確為 Kind applicability）：本輪只確認「positional 一律 UNKNOWN」已使該爭議不再產生假綠。
5. 場外觀察（不列入 finding）：`20_DEV/b1_r5/closeout_gen.py`（21:37，非本 Checker 所寫、不在 manifest）會「從凍結收據讀數字」生成 CLOSEOUT／HANDOFF 文件。若它讀到 N-08 的 `b1_r5_run_fda.json`，會把 `COMPLETE_NO_MISSING` 擴散到文件層 —— 這是 N-08 必須先重生、再跑 closeout 的另一個理由。

## 6｜淨影響

- 真開合：**B1-F01**（read control 資料綁定＋POS 檢 deny invariant）、**B1-F02**（arm1 單獨裁定、arm2 真呼叫）、**B2-F1**（Q POS 全 HOLD，1,385 個 NOT_EXECUTED 案已移出 PASS 類）、**B2-F4**（labelled-only＋UNKNOWN 必拒，誤收 94→0）、**N-01～N-06**。
- 未完全開合：**N-07**（收據仍缺 missing 欄清單，P3）。
- 新增：**N-08（P2，交付面必改）**、N-09～N-12（P3）。
- 本輪沒有「案級 PASS 依賴未綁 oracle／自比」、「HOLD/PARTIAL 併入 PASS」、「宣稱未發生的接受」三類事實，故不構成 REJECT 條件；但 N-08 必須在 Owner 採納前重生，否則凍結集內同一 op 出現兩個矛盾 disposition。

VERDICT: ACCEPT

MANDATORY_FINDINGS: 0
