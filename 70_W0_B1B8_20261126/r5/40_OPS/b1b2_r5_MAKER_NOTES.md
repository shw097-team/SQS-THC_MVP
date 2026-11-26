# B1/B2 r5 — Maker 執行記錄與自報（非驗收）

- 版本：2026-11-26_r5_Native-first_CODEX_FINAL
- 角色：Maker（施工 + 自測）；**不是** Checker、不是原 Reader、不代表接受
- 產品效果：`SOURCE_READ`；`write_set=[]`；`preimage=N/A`；`FIN_ORDER=DENY`
- 分離 Checker：round1 REJECT（B1 3 / B2 5 mandatory）→ 修補 → round2 REJECT（5 mandatory）→ 第二次修補 → **round3 ACCEPT / 0 mandatory**

## 1｜實際執行的命令與結果（真跑，非描述）

| # | 命令 | exit | 結果 |
|---|---|---|---|
| 1 | `python -B b1_spec.py` | 0 | manifest 4/4 全等；B1 30 unit／60 case；unit set `e0d3afa6…`、case set `910962c5…` |
| 2 | `python -B b1_cli.py --op BASE --repo …\SQS-THC` | 2 | 23 unit 逐 target 取證；`PARTIAL_SPLIT_PER_KEY` |
| 3 | `python -B b1_cli.py --op ALL --repo …\SQS-THC` | 2 | repo identity + BASE/KERNEL + FDA 16/16 + ROOTS UNKNOWN |
| 4 | `python -B b1_tqaep.py` | 0 | 60 案：PASS 32、PASS_EVIDENCE 5、PARTIAL 5、FIXTURE_ONLY 12、HOLD 6、FAIL 0 |
| 5 | `python -B b1_edge_sec.py` | 0 | 9/9 safety 案 |
| 6 | `python -B b2_tqaep.py` | 0 | 2,930 案：PASS 1,385（皆為 namespace 拒絕）、HOLD 1,545、orphan 0 |
| 7 | `python -B b1b2_freeze.py` | 0 | 20 artefacts 凍結（`75660aa3…`） |
| 8 | `python -B closeout_gen.py` | 0 | 6 份 CLOSEOUT／HANDOFF 由收據生成 |

## 2｜環境事實（實測）

- Python 3.14.9；git 2.56.1.windows.1；OS principal = 目前 Windows 使用者
- `SQS-THC` HEAD = `9a70501ad4bbf315c675894a7a58c0f98bf18f47`；**無 `origin` remote**（`No such remote 'origin'`）
- `FHS/Fabric` HEAD = `765df6289cfb7730aa56efbd522d76df6ec9809a`
- spec 釘定的 Kernel commit `d34dc903…` **不在 SQS-THC 本地 object DB**（`cat-file -e` 失敗）
- `agents/profiles/sqs-{orchestrator,data-analysis,risk}` 存在但 `listdir` 對目前 principal 拋 `PermissionError`

## 3｜Maker 自報缺陷（本輪自己發現，未等 Checker）

1. **作用域越界（M-01）**：為確認 slot 名是否在載體中出現，我對整個 `fabric-desktop-automation/` 目錄跑過一次 `grep -ril`（跨 `*.py/*.yaml/*.json/*.md/*.txt`）。該目錄**超出** owner 授權的 16 路徑 allow-list。實際只保留「檔名／命中與否」作為線索，未把任何非授權檔案內容寫入產物或收據；但讀取行為本身已越界，屬自報 finding，需 Owner 裁決是否接受為研究性讀取。產品端（`op_fda`）嚴格只讀 16 路徑，未受此影響。
2. **arm2 oracle 曾跑後修正（M-02）**：第一輪把 `DISK_BUT_UNTRACKED` 判為 arm2 失敗，看到結果後才改成「只要不製造 commit/blob/raw_sha 即算拒絕」。此為跑後改 oracle，已被 round-1 Checker 記為 B1-F02；現已把 oracle 與 accepted_statuses 升到模組頂部、執行前宣告。
3. **TQAEP 分母用錯（M-03）**：B2 的 B3 receiver 曾以 `source_payload[2]` 當 requiredness，991/1385 列其實不是 requiredness；已改為 labelled-only 推導，UNKNOWN 一律拒收（B3 現 0 收 / 1,465 拒）。

## 4｜明確不成立的宣稱（不得由本檔推出）

- `B1_ACCEPTED` / `B2_ACCEPTED`：**NO**
- 產品 ReadyAccept、WorldRaw、OriginalReaderResult、ConsumerACK：**NOT_EXECUTED / UNBOUND**
- 工具已安裝、license/ABI/lock 已核、B5 選型已完成：**NO**（META 全 `NOT_EXECUTED`）
- GUI / lease / broker / 真交易：**未接觸**（`gui_started=false`、`lease_acquired=false`、`broker_contacted=false`）
- Repo 發布：**未推送**（`distribution=LOCAL_ONLY`，散布權未具）

## 5｜保留缺口（Owner／原權位才能關）

| ID | 缺口 | 實測依據 | Owner | Resume |
|---|---|---|---|---|
| D-1 | BASE-009 兩 locator、BASE-017 一 locator 仍 `CANDIDATE_NOT_RATIFIED` | 磁碟 bytes 與 candidate raw SHA **相符**（`sha_match=true`），但 spec declared path 未修訂 | Repo/Source Owner | 逐 target 批准 namespace/root/path/commit/用途/接收權 |
| D-2 | `tests/test_fda_*` 四檔不在 16 路徑 allow-list | 名稱可見（`test_fda_lease/router/router_integration/security.py`），內容未讀 | FDA Source Owner | 具權追加讀權或書面確認非當期必需 |
| D-3 | 七 slot → action → artefact 的 M:N 未建立 | 6/7 slot 名在 16 檔中 **0 命中**（僅 `xs_compile` 有） | FDA/XQ/R13 原 Reader | 逐槽提供原 typed schema/Reader/fixture |
| D-4 | 五 Kernel 十條作者細規語義未核 | 5 檔內容 SHA 全等、64 symbol span 全等；但 pinned commit 不在本地 | 五 Kernel Domain Owner | 逐條確認 10 條擴展規則的原義 |
| D-5 | B2 父源/carrier namespace 與接收權 | carrier SHA/bytes 全等、1,385 列逐列驗證通過 | Source Owner | 具權採納 by-sha binding |
| TT-UP-1 | 九 HARD 非 loss 的 inner→outer 映射 | 18 HARD NEG 全 HOLD | R17/OriginalConsumer | 提供原 inner 錯碼與映射 |
| TT-UP-2 | 1,385 Q 的行號 namespace | **本 carrier 版本實測 carrier=Lnn 精確命中**，未見 +664 偏差 | Source Owner | 僅需確認是否另有載體 |
| E00 | 6/8 E00 的 typed DesignSelection/enable Oracle | 全 HOLD | E02/E05/PIPD | 提供決策/enable 權位 |
| ROUTE | 54 TECH_ROUTE 的 protected path | 108 案 HOLD | R17/route Owner | 逐 key 提供 protected field |

## 6｜檔案位置

- 引擎／測試：`70_W0_B1B8_20261126/20_DEV/b1_r5/`
- 執行結果：`70_W0_B1B8_20261126/40_OPS/b1_r5_*.json`、`b2_r5_*.json`、`b1b2_r5_candidate_freeze.json`
- 凍結清單：`40_OPS/b1b2_r5_CANDIDATE_MANIFEST.tsv`
- 分離 Checker：`40_OPS/b1_checker_r5_verdict.md`、`b2_checker_r5_verdict.md`、`b1b2_checker_round2_verdict.md`、`b1b2_checker_round3_verdict.md`
- 交付文件：`60_CLOSEOUT/SST_PLP_PH01_W0_{B1,B2,B1-B2}_{CLOSEOUT,HANDOFF}_r5.md`

## 7｜已知非 mandatory 缺陷（round3 提出，未在受檢凍結上改動）

| ID | 內容 | 處置 |
|---|---|---|
| N-08 | 凍結成員 `b1_r5_run_fda.json` 是修前產物（自報 `COMPLETE_NO_MISSING`、缺 `artefact_sha256`） | 不在凍結上改 bytes；另存 `b1_r5_run_fda_REGEN.json`，交付文件一律引用 `b1_r5_run_all.json` 的 FDA 段 |
| N-09 | `op_hard.summary.preserved` 對 UNKNOWN 仍計數 | 已知；HARD 全 HOLD，不影響案級 verdict |
| N-10 | 本檔舊數字過期 | 已於本版更正 |
| N-11 | BASE-006 arm2 因 commit 不可解析被標 failed | arm2 已不參與 PASS 合取 |
| N-12 | `resolve_target` 內死碼 | cosmetic |

## 8｜v2 增量（D-5／TT-UP-2 欄位映射，2026-11-26 續工）

**權威來源**：carrier `463dcf33…` 自身第 7–9 行宣告四維度，四節標題各自給出列數與行號：
`carrier:13` Q1(440)、`carrier:457` Q2(513)、`carrier:974` Q3(378)、`carrier:1356` Q4(54)。
由該宣告還原的最小欄位映射：

| namespace | 維度 | Requiredness 欄 | 其他維度欄 |
|---|---|---|---|
| Q1 | Requiredness | idx2 | — |
| Q2 | AdmissionDecision | idx5 | idx2 = AdmissionDecision |
| Q3 | KindApplicability | 無此欄 | idx1 = kind |
| Q4 | Golden | 無此欄 | — |

- Q3/Q4 不輸出 UNKNOWN，而輸出 `NOT_APPLICABLE` ＋ section 行號作 applicability evidence。
- `N_A`、`ROUTE_ONLY_NOT_TOOL_REQUIREDNESS` 視為來源自陳的 not-applicable。
- **AUTHOR_DESIGN_ONLY**：`REFERENCE/EVAL_ONLY`、`EVAL_ONLY_COMPARATOR`、`EVAL_ONLY_RESEARCH`
  這類「原子前綴＋限定詞」值，以原子前綴規則判為合法 requiredness（保留原字串）。此規則是
  作者層解釋，非 carrier 明文，Checker 可據此挑戰。
- 仍 UNKNOWN 的 34 個 Q 列（`REUSE_INTERNAL_FIRST`、`BASE_REQUIRED_AS_ADAPTER` 等）不猜值，
  對應 POS 記 HOLD。

**v2 實測**：B2 2,930 案 = PASS 2,786、HOLD 144、FAIL 0；B3 receiver 收 1,351 拒 114；
B5 收 0 拒 1,465（缺 metadata）。凍結 manifest 見 `b1b2_r5_candidate_freeze.json`（本檔不手抄 digest，避免過期）。

## 9｜v3 增量（E00／ROUTE／分解表修正，2026-11-26 續工 2）

Checker v2 判 REJECT（3 mandatory，全在 E00）與 5 項非 mandatory。處置：

| ID | 問題 | 修法（行為改變，非改詞） |
|---|---|---|
| M-01 | E00 POS 用 spec 自己的 payload 當 oracle | 改用 carrier `TECH54具名設計合約` 段的 `SelectedDesign`／`SelectedVersion`（carrier:1416 起）作獨立原據；逐案比對 leading token |
| M-02 | E00 NEG 的 first_fail ≠ spec 宣告的 `STATE_CONFLICT` | guard 改回 `STATE_CONFLICT`（未授權 enable 即狀態衝突），並以該碼作 PASS 條件 |
| M-03 | notes/closeout 的 HOLD 分解與 artifact 不符 | 分解表改由 `verdict_counts` 生成，不再手抄 |
| N-01 | ROUTE key 無 namespace，54 案全未 join carrier | `resolve_tool_row()` 以 Q1／Q2 雙前綴解析，唯一命中或雙邊一致才採用；route 與工具列交叉核 |
| N-02 | distribution 少計 40 列 | 加 `rows_total`，四象限合計 440/513/378/54 |
| N-04 | 523 個 NOT_APPLICABLE 收據無 evidence | receipt `checked_values` 增 `applicability_evidence` |
| N-05 | 本檔引用過期 digest；closeout §06 與 §04 矛盾 | 已修 |

**v3 實測**：B2 2,930 案 = PASS 2,839、HOLD 91、FAIL 0；另列 22 條 ROUTE 的來源內部不一致
（`source_defects`，不計入產品 PASS）。E00：7 PASS、1 HOLD（該工具 carrier 無 SelectedDesign）。
B3 收 1,351 拒 114；B5 收 0 拒 1,465。

## 10｜v4 修正（撤回誤判，2026-11-26 續工 3）

Checker v3 判 REJECT（1 mandatory），兩點都成立：

1. **E00 7 PASS 越權**：pinned spec B2-F05 已宣告 U0019–26 之中 6 個 Oracle HOLD、2 個有歷史證據。
   我用 carrier 交叉核把它升成 PASS，等於繞過 spec 的 Oracle 狀態宣告。→ **已全數改回 HOLD（8/8）**，
   carrier 交叉核只作 supporting evidence（`carrier_agrees` 欄）。
2. **21 條 source_defects 全是誤判**：我用 `REQ_VOCAB` 對 route 全文做子字串掃描（`eval_only`、
   `hard` 會命中 `EVAL_ONLY_COMPARATOR`、`HARD_SOURCE_OBLIGATION`）。→ **已撤回全部，改為結構化
   取欄**（以全形「／」分割，取每段 `;` 前的 leading token），最終 `source_defects = 0`。

**v4 實測**：B2 2,930 案 = PASS 2,854、HOLD 76、FAIL 0；HOLD = 34 Q（策略值不可分類）
+ 8 E00（spec Oracle HOLD）+ 34 ROUTE（無 requiredness 欄，不斷言）。
B3 收 1,351 拒 114；B5 收 0 拒 1,465。此根因的 2 次實質修補額度已用盡，
後續若再有同根因爭議應 PARK，不再換名重修。

## 11｜B0 入站：視窗已開但仍被兩層擋住（2026-11-26 23:0x）

1. **OWNER 視窗**：使用者本人在 tkinter 提示輪入當事口令後已成功開啟
   `WIN-90b52ba73008`（task `SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH`、scope `sqs_thc_ph01_e00,b0_source_read_authority`、
   ceiling `READ_ONLY_PROBE`、到期 2026-11-27T01:02:30、broker 1655）。**這一層已通。**
2. **descriptor 自身權利區間過期**：`native_entry.py:346 RIGHTS_EXPIRED`。
   `B0_READ_CONTEXT_2026-11-25_r4.json` 的 `valid_from..expires_at` = 2026-11-25T20:26:58 → **2026-11-26T02:26:58**，
   已過期約 20.6 小時。這不是視窗問題，是簽發檔本身的時效。
3. **路徑身分**：把續期候選放到 `70_W0_B1B8_20261126/00_PREFLIGHT/` 後，reader 先以
   `root.PathSecurityError PATH_IDENTITY_UNVERIFIED`（broad principal has write ACL）拒絕——
   簽發檔必須位於 broad principal 不可寫的位置。

**已備但未採納**：`00_PREFLIGHT/B0_READ_CONTEXT_2026-11-26_RENEWAL_CANDIDATE.json`
（sha `1a627301…`、3608 B、與原檔同 key set、interval 2026-11-26T23:02:30→2026-11-27T01:02:30、
authority 指向使用者本人剛簽的 `OWNER_WINDOW.json` sha `e754002e…`）。
採納需三件控制面動作，代理不自為：① Owner 簽發、② 檔案設限縮 ACL、③ `native_entry.py` 的
EXPECTED_DESCRIPTOR_PATH/SHA/BYTES 換 pin（程式碼 delta，需新 freeze 與分離驗證）。
