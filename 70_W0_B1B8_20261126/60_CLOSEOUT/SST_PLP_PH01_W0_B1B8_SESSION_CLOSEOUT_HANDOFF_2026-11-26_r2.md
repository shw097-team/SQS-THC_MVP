# SST_PLP_PH01 W0 B1–B8｜SESSION 結案與移交（2026-11-26 · r2）

> 讀者：下一位執行代理（Commander）。本檔自足，取代 r1 作現行移交。
> 撰寫原則：只寫本次實測；未達成者寫「未達成」，不美化、不補值。

---

## 0｜本次 SESSION 做了什麼（與沒做什麼）

| 項目 | 本次結果 |
|---|---|
| 上游知識庫位置 | **被重新編排**：B1–B8 SPEC 已移入 `W0_B1-B8_NATIVE_FIRST_2026-11-26_r4_HERMES_FINAL\SST_PLP_PH01_W0_B1-B8_執行控制小包\`。B1/B2 的 raw sha **未變**（`13294cad…` / `140de5bc…`），故以 **sha 認身分**、不再以路徑深度找檔；`b1_reader` 與 `b2_semantics` 已改為 by-sha 定位 |
| B1 | 修完 round-3 的 11 項中 10 項（第 3 項措辭於 round 4 判 PARTIAL）、再修 round-4 指出的 5 項 Maker 缺陷中的 4 項；**round 4 判 `B1_ACCEPTED = NO`**；已 freeze round-5 候選並送 round 5（本次 SESSION 內未取回 verdict） |
| B2 | **由 PAYLOAD_INTEGRITY_ONLY 升級為 ROW_SEMANTICS_AND_CLASS_MUTATION**：真正 NEG 分類變異 1,465 案（`NAMESPACE_JOIN_DENY` 1,385／`TOOL_REQUIREDNESS_HOLD` 72／`STATE_CONFLICT` 8，與 SPEC §06 完全一致）、象限三訊號一致 440/513/378/54、pin 對帳誠實結論「歷史 72 不可重建」、clause 身分規則 UNBOUND 明列。已 freeze 並送分離 Checker（本次 SESSION 內未取回 verdict） |
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
| B2 freeze | `40_OPS/b2_candidate_freeze_20261126T141949.json` | digest `095ddf25…` |
| B2 ToolReadSet@2 | `40_OPS/b2_toolreadset_20261126T141706.json` | `450d30bd…`（2,649,780 B） |
| B2 TQAEP@2 | `40_OPS/b2_tqaep_20261126T141735.json` | `eb75ddd0…`（2,071,976 B） |
| B3 parse | `40_OPS/b3_parse_20261126T142325.json` | `6dff324f…` |
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

## 3｜B2 真實狀態

- `b2_ops_tqaep2.py`：**2,930 案全 PASS**，但這次不是同義反覆：
  - POS = payload pin 重算 ＋ 各 kind 必填欄 ＋ requiredness（對 SPEC `input_rule` 導出的規則）＋ Q 列一致性 ＋ 象限一致；
  - NEG = **真實分類變異**，且每個變異都先驗 baseline 乾淨：Q 列尾碼 join（naive 會命中、oracle 拒 `NAMESPACE_JOIN_DENY`）、HARD 被降級／route 列越權升 HARD＋啟用（`TOOL_REQUIREDNESS_HOLD`）、E00 同列兩個互斥狀態（`STATE_CONFLICT`）。
  - SPEC §06 期望分布 **1,385／72／8** 與實測完全一致，`orphans 0 / missing 0`。
- 象限：`Q1 440 / Q2 513 / Q3 378 / Q4 54`，`key` namespace 與 `q_row.full_key` 兩訊號 100% 一致；非 Q 列 80 = 18 HARD + 8 E00 + 54 ROUTE。
- **pin 對帳（誠實結論）**：歷史 72 **不可重建**（HARD pin-UNBOUND 實測 16，+54 route-only = 70）；舊 TQAEP 的 54 恰等於 TECH_ROUTE 數。→ 兩個歷史純量不可互換引用，改以逐列 `pin_state` 為唯一載體。
- **clause 身分**：`direct_clause_sha` 以三種 span 規則重算 **0/80 可重現** → 生成器規則 UNBOUND，明列不宣稱 clause 身分；EVIDENCE 引用之文件 1,385/1,385 以 sha 綁定。
- `parent_source`：宣告路徑含失效段 `W0_B0-m`，以 sha `d95c8ac6…` 重綁為 `PARENT_SOURCE_REBOUND_BY_SHA`＋`CANDIDATE_NOT_RATIFIED`（同 B1 binding 手法，需 Owner 追認）。
- `B2_ACCEPTED`：**不成立**（分離 Checker verdict 本次未取回）。

---

## 4｜待 Owner 裁決（合併清單）

| # | 事項 | 受影 | 最小恢復 |
|---|---|---|---|
| D-1 | 三筆 locator binding（BASE-009 ×2、BASE-017）追認或改 SPEC 路徑＋新 sha | B1 | Owner 簽認或 SPEC 修訂 |
| D-2 | allow-list 是否納入 `tests/test_fda_*.py`；mirror carrier 地位 | B1 `BASE-018`、EOL 觀察 | Owner 決；不可由 Maker 擴張 |
| D-3 | 七槽 slot↔artefact 映射（`slot_reference_counts=0`） | 7 FDA POS（`CARRIER_LEVEL_ONLY`） | 提供 slot 級來源 |
| D-4 | 五 Kernel NEG 語意 oracle | 5 案 | 原 Domain Owner 受保護欄位 oracle |
| D-5 | B2 parent 重綁（`d95c8ac6…`）追認 | B2 全部 1,465 列 | Owner 追認 rebind |
| D-6 | `direct_clause_sha` 生成規則（三種規則皆不可重現） | B2 clause 身分 | 提供原生成規則或重出 clause sha |
| D-7 | B2 歷史 72/54 純量之出處 | 舊收據 | 原作者說明；不得再引用 |

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

## 7｜本次踩到的坑（已寫進程式）

1. **上游改版會搬路徑**：一律 by-sha 定位（`w0_spec.find_spec` / `b2_semantics.find_spec` / `b1_reader.run_b1.find_spec`）。
2. **`os.walk` 回傳檔名不是身分**：B2 目錄下有 r2/r3/r4 同名檔，只有 r4 的 sha 是 pin。
3. **`dict` 字面量內 `set.pop()` 會讓後面的 `len(seen)` 變 0**：`q_of` 一度因此把所有象限判成不一致（已修）。
4. **`candidate_digest` 要寫清楚排序規則**：round 4 抓到宣告序 vs 排序序不一致（本次已改為排序並在檔內註明）。
5. **TECH_ROUTE 的 payload 是 2 欄複合字串**，不是單欄；Q3 列只有 8 個非空欄。
6. `codex exec` 的 `-o` 可寫回 wave root，但 checker 沙箱本身 read-only（round 4 明說）。

---

## 8｜不可跨越的線（未變）

不讀／不輸入口令、私鑰、DPAPI；不自建 issuer／registry／compiler；不改知識庫原件、不改 `SQS-THC`、不改 `FHS/Fabric`；`write_set=[]`（產品效果）；不 checkout／fetch／import／執行 repo 內程式碼；`FIN_ORDER=DENY`；不為求綠改 expected／改 Oracle／把 HOLD 藏成 PASS；Maker 自測不是驗收。
