# B1 分離 Checker Verdict（r5）

## 0｜scope／checker

- 受檢：`spec_delta_r5/CODEX_FINAL`（B1 正文 `24e4f17a…`、B1 附錄 `c667f814…`、B2 正文 `1a11f0cf…`、B2 附錄 `9a16fd13…`、`FINAL_SPEC_MANIFEST.tsv` `3c816deb…`）；Maker 產物 `20_DEV/b1_r5/{b1_engine,b1_spec,b1_cli,b1_tqaep,b1_edge_sec}.py` 與 `40_OPS/{b1_r5_run_all,b1_r5_tqaep,b1_r5_edge_sec}.json`。
- Checker 身分：**分離 context／分離 session 的唯讀 Checker**，未執行 Maker 任何模組（A–G 全部用自寫 parser／自寫 hash／`git cat-file`／`ast` 重算）。
- **SoD 限制（必須明說）**：本 Checker 與 Maker 同一模型軸，**同模型≠獨立**；本輪只建立 process/session 分離，**model-axis SoD 未建立**。因此本裁決可作技術反駁，不能當「獨立第三方」。
- 唯讀紀律：對 `C:\Projects\Agent_Workspace\SQS-THC` 與 `…\FHS` 只做 `git rev-parse` / `cat-file` / 唯讀讀檔／`os.stat`；無 fetch／checkout／import／執行；無 GUI／broker／lease／網路；未改任何受檢檔。僅寫本目錄兩個輸出檔。
- 我沒有重跑 Maker 的 run，因此「run 是否如實產生」只能由**產物內部一致性＋與我獨立 hash 的對撞**判定，不能由「我跑過」判定。

## 1｜獨立重算表（A–G）

| # | 項目 | expected（Maker／spec 宣稱） | observed（我自己的重算） | 判定 |
|---|---|---|---|---|
| A | `FINAL_SPEC_MANIFEST.tsv` 四檔 raw SHA256 + bytes | 24e4f17a…/263939、c667f814…/26565、1a11f0cf…/12549483、9a16fd13…/27565 | 完全相同 4/4（且 manifest 自身 `3c816deb…`/666B 與 `SPEC_POINTER.manifest_sha256`、`manifest_bytes` 一致；entry `771bd404…` 亦一致） | **PASS** |
| B | B1 正文 unit/case 集合 | 30 Unit / 60 Case；unit set `e0d3afa6…`、case set `910962c5…` | 30/60；`sha256("\n".join(sorted unit_id))`（無尾 LF）＝`e0d3afa6…` ✔；`sha256("\n".join(sorted CaseID))`（無尾 LF）＝`910962c5…` ✔；種類 `{BASE:18, KERNEL:5, FDA:7}` ✔；每 unit `case_ids` 2 筆、unit→case 與 case 表**雙向零差集** ✔ | **PASS**（附錄:100–101 自述「sorted exact UnitID／CaseID UTF-8 LF join 無尾LF」與我採用的慣例一致；此 digest 只釘 ID 集，不釘 kind/key，故我另獨立驗了 18/5/7 組成） |
| C | §04.K2 五 Kernel 原碼 | 5 個 raw SHA＋64 個 symbol span | `git cat-file blob HEAD:` 逐檔 sha256：90a5f4d4…／21e0150f…／ea1e13cd…／288a2a0e…／d2a143c5… **5/5 全等**；自寫 `ast` 取 `(lineno,end_lineno)` 對表列 Lx–Ly：**64/64 全等**（fsdt 14、temporal 13、knowledge 12、harness 13、capability 12） | **PASS（內容）**；**commit pin `NOT_VERIFIED`**：`git cat-file -e d34dc903…^{commit}` 失敗，本地 HEAD=9a70501a…，該 commit 不在本地 object DB（spec 自標 `REMOTE_SOURCE_ONLY`、Maker 記 `pinned_commit_present_locally=false`，二者一致） |
| D | FHS 16 allow-list | §02.R5.LOCATORS 16 組 sha256+bytes | 逐檔實算 **16/16 sha 與 bytes 全等**；另 3 列 §02.R5.LOCATORS 候選（`data_plane/src/backfill_daily.py` fc10f802…、`check_daily.py` 06b25b72…、`governance/FDA_INTEROP_DISPOSITION.yaml` 9fac4d25…）亦 **3/3 全等** | **PASS** |
| E | TQAEP 60 案 | case_count=60、case 集＝B 的 60 ID、verdict_counts 與逐案一致、PASS 不得依未綁 oracle | 結構面全對：60/60、集合全等、`expected_first_fail` **60/60 與 §06 表第 6 欄逐字相同**、unit_id↔case 對應 60/60、逐案計數 `{PASS:37, FIXTURE_ONLY:12, HOLD:6, PASS_EVIDENCE:5}` ＝ `verdict_counts` ✔、verdict/arms 無矛盾 ✔、6 HOLD 未被寫成 PASS ✔、12 FIXTURE_ONLY 未被併入 PASS ✔。**但**：37 個 PASS 中 25 個的 PASS 依賴常數／自造 oracle／無 commit 身分的讀取（見 F01–F03） | **FAIL（verdict 層）** |
| F | EDGE/SEC 9 案 | caller 不得自授 context、repo 非 allow-list 拒、W 外寫拒、未知 commit 拒、空請求拒、write_set=[]、GUI/lease/broker 未觸發 | 6 案為真 subprocess 且失敗碼與 code path 對得上（`b1_engine.py:87-90` context override、`:138-139` repo allow-list、`b1_cli.py:80-82` OUT 前綴、`:60-63` EMPTY_REQUEST、`:41-42` unknown arg、`b1_engine.py:590-592` COMMIT_UNRESOLVED）；`SEC.NO_WRITE_TO_SOURCE_REPO` before/after 相同，**我另以 20,175 檔 mtime 全掃（>20:50 修改 0 檔）＋HEAD 未變獨立佐證**；`SEC.PRODUCT_EFFECT_INVARIANTS` 的 write_set/effect/gui/lease/broker 是 `b1_engine.py:544,580` 的**字面常數**（非觀測），但我以靜態 import 分析獨立確認：五模組只 import stdlib（ast/hashlib/json/os/re/subprocess/sys/time/traceback），唯一外呼是 `git`，故「未觸發 GUI/lease/broker」**實質為真** | **PASS（實質）**；證據品質記 P3（2 案以常數自證） |
| G-i | 「5 Kernel 內容與 symbol span 全等」 | 全等 | 內容 5/5、span 64/64 全等；commit pin 本地不可解析 | **CONFIRMED（內容）／commit `NOT_VERIFIED`** |
| G-ii | 「1385/1385 B2 Q 列 payload 全等」 | 1385/1385 | carrier `463dcf33…`/767859B/2392行 **sha 相符**；我自寫 carrier 列解析＋canonical JSON 重算，**隨機 20 列 20/20 payload_sha 相等且 carrier_key 落在所記 physical line**；**未做 1385 全量重算** | **PARTIAL（抽樣 20/20）／全量 `NOT_VERIFIED`** |
| G-iii | 「B1 無寫入 source repo」 | head+status 不變 | HEAD 仍 9a70501a…；SQS-THC 20,175 檔中 **>20:50 被修改者 0 檔**；`.git/index` mtime 仍 2026-10-15 | **CONFIRMED** |

補充交叉驗證（用於判斷 E 的 actual 是否真讀到檔）：TQAEP 內 13 個外部 carrier 的 `raw_sha256` 與我對實檔的 sha256 **13/13 相同**；BASE-009 兩個 `DISK_BUT_UNTRACKED` 目標的 `locator_binding.sha_match=true` 與我實算一致。→ **Maker 的 read-set 觀測是真的，不是抄表**。

## 2｜Findings

### B1C-R5-F01｜mandatory｜P1｜broker_live_submit 的 POS/NEG PASS 建立在常數上，且正是 spec 明文禁止的手法
- 位置：`20_DEV/b1_r5/b1_engine.py:467-483`（`fda_deny_control` 純常數回傳）、`b1_tqaep.py:203-216`（POS/NEG 皆以該常數裁 PASS）、spec 正文 `…r5_Native-first_CODEX_FINAL.md:510`（§04.R5 broker_live_submit 列「當期法位」：**「永久DENY；不能用常數同時冒read control成功」**）。
- 事實：`fda_deny_control("read")` 回 `ALLOW_READ_CONTROL`、`submit/replace/cancel` 回 `DENY/FIN_ORDER_DENY_ALWAYS`，全部為字面 dict，未觸任何 FDA artefact、未經 `fda_router.py`/`fda_lease.py`、無 connector/lease 物件。`B1.POS.FDA_broker_live_submit` 與 `B1.NEG.FDA_broker_live_submit` 的 `actual` 就是這兩個常數的輸出（`pos_is_deny_invariant: true`、`allowed_effect_pos: null`）。
- 影響：2 個 PASS 不成立為「產品行為已驗」，而是「常數已宣告」。B1_ACCEPTED 不得以此 2 案計入；且此寫法與 spec 明列禁令直接衝突，屬**規則違反**而非只是證據不足。

### B1C-R5-F02｜mandatory｜P1｜18 個 NEG BASE 的 PASS 是 arm1 ∧ arm2 合取，而 arm2 的 oracle 是跑後自改的、且 probe 用與本案無關的硬編碼 commit
- 位置：`b1_tqaep.py:149-178`（arm2 定義與 `verdict = PASS if arm1 and arm2`）、`b1_tqaep.py:158-161`（probe 固定 `0489ac84a390a7172c6cce8322caefeb66b8942c`）、`b1_tqaep.py:173-175`（自述 `oracle_note: "arm oracle corrected once: …"`）。
- 事實：§06 表對這 18 案列的 Expected FirstFail 只有 `BASE_ROW_MISSING`；`FOREIGN_AS_LOCAL_REFUSED` 不在 spec 任何位置，是 Maker 自造字串，且記錄自承「corrected once」。arm2 對每個 key 都拿同一個與該 unit declared remote（`d34dc903…`）無關的 commit 去 `rev-parse --verify`，必然得到 `COMMIT_UNRESOLVED`（30 個 probe：COMMIT_UNRESOLVED 16、ABSENT_TREE 11、DISK_BUT_UNTRACKED 3），因此 `pass=true` 是**必然結果**而非觀測。arm1 亦為結構性必然：`BASE_TARGETS.pop(key)` 後 `op_base` 走 `:423-427` 的分支直接吐 `BASE_ROW_MISSING`。
- 影響：18 個 PASS 的「PASS」不是「原 predicate 成立」，而是「原 predicate＋一個跑後改過的 predicate」的合取。18 案必須改回以 arm1 單獨裁定，arm2 另立標籤（如 `AUTHOR_EXTRA_ARM`），不得進入 PASS 判定。

### B1C-R5-F03｜mandatory｜P2｜17 個 POS BASE 的 PASS 由「status 白名單」給出，POS 分支沒有 FAIL 路徑；5 案在無 commit/blob/raw 身分下仍 PASS
- 位置：`b1_tqaep.py:118-135`（`if "NOT_IN_OWNER_ALLOWLIST" in statuses → HOLD … else PASS`；該分支只有 HOLD/PASS_WITH_RECORDED_MISSING/PASS，**無 FAIL**）、`b1_tqaep.py:6-7`（自訂 POS 定義「POS is only PASS when the product really read an identity…」）。
- 事實：`B1.POS.BASE-006` 三個 declared profile 目錄 `commit/blob/raw_sha256/disk_sha256/bytes` **全為 null**（純 `DISK_DIRECTORY`）仍 `PASS`；`007`（`SQS/TWICT_RUNTIME_PACK_MANIFEST.yaml`）、`008`、`011` 為 `DISK_BUT_UNTRACKED`（只有 disk_sha，無 commit/blob/raw，亦無 §02.R5.LOCATORS 期望值可比）仍 `PASS`。`run_all.json` 自報 `missing_targets: 10`，而 60 案中 **FAIL 數為 0**。此外 §05 各 unit 的 `input_rule` 自述「B1只定位；B4處置=…actual UNKNOWN」，即該 key 的功能性 POS 在 B1 階段**不可能**成立。
- 影響：嚴格而言 **006/007/008/011 四案**（無任何 commit 身分、亦無 §02.R5.LOCATORS 期望值可比）應改為「READ_SET_RECORDED／NOT_EXECUTED（功能性）」；`009` 另有兩個 `locator_binding.sha_match=true` 可補內容身分，但仍是 `DISK_BUT_UNTRACKED`（無 CommitPathSpan）。連同 POS 分支缺 FAIL，5 個 POS PASS（006/007/008/009/011）鑑別力皆為零（無任何輸入能讓 POS FAIL）；B1_ACCEPTED 不得以 POS PASS 計入。

### B1C-R5-N04｜non-mandatory｜P3｜TQAEP 逐案記錄缺 §06.0 規則 4 要求的 raw 欄
- `b1_tqaep.py:113-116` 的 case 記錄只有 9 欄；spec `:2180-2190` 要求 same Subject/Candidate/Scope/Host/PolicyEpoch/CaseID、input/POS/NEG bytes SHA、實際 exit/diagnostic、observed 或 WorldRaw ref、原 Reader。另 `oracle_domain` 被 `case["predicate"][:180]` 截斷（`:115`），長列 predicate 不是原文。

### B1C-R5-N05｜non-mandatory｜P3｜EDGE/SEC 2 案以常數自證
- `b1_edge_sec.py:75-77`：`SEC.FDA_DENY_INVARIANT_OUTPUT` 只驗 `exit in (0,2)` 與 JSON 形狀，不驗 deny invariant；`b1_edge_sec.py:86-96`：`SEC.PRODUCT_EFFECT_INVARIANTS` 讀 `run_all` 的**字面常數**（`b1_engine.py:544,580`）。我已用靜態 import 分析獨立確認命題為真（僅 stdlib＋git），故為證據品質問題、非高報。

### B1C-R5-N06｜non-mandatory｜P3｜「5 Kernel 全等」是「內容全等」，不是「commit 全等」
- `git cat-file -e d34dc903…^{commit}` 失敗；本地 HEAD 9a70501a…。spec 與 Maker 均已自標 `REMOTE_SOURCE_ONLY`／`pinned_commit_present_locally=false`，故非矛盾，但驗收文字不可寫成「pinned commit 已核」。

### B1C-R5-N07｜non-mandatory｜P3｜unit 集合 digest 只釘 ID
- 附錄 `:100` 自述慣例為「sorted exact UnitID」，故 `e0d3afa6…` 不含 kind/key；我另獨立驗 18/5/7 與 kind/key 唯一性。Case digest 同慣例（無尾 LF），我亦重算相符。

### B1C-R5-N08｜non-mandatory｜P3｜exit-2 語義與 CLI 契約文字不一致
- `b1_cli.py:6-9` 定義 2＝「有合法 entry 但部分 missing」，但 `b1_engine.py:590-592` 對未知 commit 直接拋 `COMMIT_UNRESOLVED`、stdout 為 `{}`（`b1_cli.py:90`）。SEC.UNKNOWN_COMMIT 只驗 `exit==2`，未驗 stdout 是否為空物件，屬判準過鬆。

## 3｜我無法重算的項目（不猜）

1. **§04.K2 的 commit pin**：`d34dc903…` 不在本地 object DB，只能證明「本地 HEAD 的 bytes 與宣稱 raw SHA 相同」，不能證明「該 commit 的 bytes 相同」。
2. **B2 1385/1385 全量**：只抽樣 20 列（20/20 相符）＋carrier sha 相符；未做 1385 全量重算。
3. **run 的執行真實性**：我未重跑 Maker 程式；只能以「產物值與我獨立 hash 對撞」佐證（13/13 外部 carrier、5/5 kernel、2 個 locator binding 均相符），故 read-set 是真的；但 `verdict` 的推導是否如 `b1_tqaep.py` 所述，只能由程式碼閱讀斷定。
4. **`status_lines` 132 vs `dirty_tracked_files` 2**：兩者來自不同 git 指令（一邊含 untracked），我依唯讀紀律未執行 `git status`，未獨立重算此兩個數字；我改用 mtime 全掃作為「無寫入」的獨立證據。

## 4｜對 B1_ACCEPTED 的淨影響

- 文件／身分層（A、B、C 內容、D、G-i 內容、G-ii 抽樣、G-iii）**獨立重算全部相符**：這份 spec 與 Maker 的取證層是真材實料，Maker 沒有在 digest 上造假。
- 產品裁決層（E）**不成立**：37 個 PASS 中有 **25 個**（F01 的 2 案＋F02 的 18 案＋F03 的 5 案，三集合互斥）在案級上得不到支撐。
- 反面要說清楚：Maker **沒有**把 6 個 HOLD 寫成 PASS、**沒有**把 12 個 FIXTURE_ONLY 併入原語義 PASS，`claim_ceiling` 也明寫「HOLD/FIXTURE_ONLY are NOT PASS」，且全工作區仍宣示 `B1_ACCEPTED=NO`。所以這是「案級 PASS 標籤高報」，不是「偷渡接受」。
- 結論：即使 B1_ACCEPTED 目前本來就是 NO，本輪 37 PASS／9-9 EDGE_SEC 的證據**不足以支撐任何升格**，且 F01（常數冒 read control 成功）是 spec 明文禁止者，必須先改。

VERDICT: REJECT

MANDATORY_FINDINGS: 3
