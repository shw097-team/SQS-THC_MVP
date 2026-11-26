---
artifact_kind: BATCH_CLOSEOUT_HANDOFF
subject: SST/SQS-THC/PH01/E00
original_wave: P1-W00M
spec_version: 2026-11-26_r5_Native-first_CODEX_FINAL
spec_manifest_sha256: 3c816deb8fc216eae831dddfac396217d5b224fc7575c03415ef9f08ebbfa046
candidate_manifest_sha256: 96d1342db3d394351f34974186035d9f58af33a1e53e8985fe5b51c319cf31f4
generated_at: 2026-11-27T00:28:19+0800
product_actual: EXECUTED_SOURCE_READ_ONLY
fin_order: DENY
distribution: LOCAL_ONLY
---

# W0-B2｜CLOSEOUT + HANDOFF（r5 產品層）

## 01｜接受狀態

| 項 | 值 |
|---|---|
| 產品實跑 | 是（2,930 案全部執行，orphan 0） |
| 案級分佈 | HOLD 76、PASS 2854 |
| **B2_ACCEPTED** | **NO** |
| 凍結候選 | `96d1342db3d394351f34974186035d9f58af33a1e53e8985fe5b51c319cf31f4` |

## 02｜真輸入

| 項 | 值 |
|---|---|
| carrier | `SST_PLP_共用實質正文_工具合約_2026-11-23_r2.md` `463dcf33a668a9daa8f0bbf447c7dacc4c3d602bc53fa7e4866844ffbbc4b3e1`（767,859 B，實測全等） |
| spec | `3c816deb8fc216eae831dddfac396217d5b224fc7575c03415ef9f08ebbfa046` |
| Q 列 | 1,385（Q1 440／Q2 513／Q3 378／Q4 54，實測與 spec 象限一致） |

## 03｜QROWS 實測

| 項 | 值 |
|---|---|
| 逐列驗證 | **1,385 / 1,385**（physical line + key 欄 + row 欄 + canonical payload SHA 四項全等） |
| 未驗證 | 0 |
| 意義 | 原列逐字保全（VERBATIM_ONLY）；**不是**工具 requiredness/admission 的語義接受 |

## 04｜HARD / META / RETURN

| Op | 實測 |
|---|---|
| 欄位權威 | 由 carrier 自身宣告的四維度還原：`carrier:13` Q1=Requiredness(idx2)、`carrier:457` Q2=AdmissionDecision(idx2)/Requiredness(idx5)、`carrier:974` Q3=KindApplicability、`carrier:1356` Q4=Golden；Q3/Q4 無 Requiredness 欄 → `NOT_APPLICABLE`＋section 行號為 applicability evidence |
| HARD | 18 unit 的單位值與 carrier 列值比對（兩份不同記錄），非自比 |
| E00 | 8 unit 的 typed DesignSelection 逐字保留；`SELECTED_*` → 未授權 enable 被拒 |
| ROUTE | 54 unit 的 requiredness 陳述與其工具列交叉核對；改寫即拒 |
| META | 全部 `NOT_EXECUTED`（無官方 metadata 讀權／未連網），工具名不當 license、不當准入 |
| RETURN | union 1,465 送 B3/B5；B3 收 1351 拒 114（缺 requiredness/source_row 者拒）、B5 收 4 拒 1461（缺 metadata 者拒） |
| 來源缺陷 | 0 條。前版曾列 21 條 ROUTE 不一致，經分離 Checker 指出為 Maker 以子字串掃描造成的誤判，已全部撤回並改為結構化取欄（不再計入任何 verdict） |

## 05｜HOLD 的構成（76 案）

- 34 個 Q POS：原列 requiredness 欄存放作者策略值（`REUSE_INTERNAL_FIRST`、`BASE_REQUIRED_AS_ADAPTER` 等），
  不屬 carrier 宣告的原子集 → 不猜、記 HOLD。
- 34 案 Q POS 之外：8 案 E00（pinned spec B2-F05 宣告其 typed DesignSelection oracle HOLD，
  即使 carrier 交叉核一致也不得升 PASS）、34 案 ROUTE（route 未陳述 requiredness 欄，產品不斷言）。
- 全部 HOLD 的實際數字以 `b2_r5_tqaep.json` 的 `verdict_counts` 為準（本表不手抄）。
- 1,385 Q NEG 為真拒絕（同尾碼異 namespace → `NAMESPACE_JOIN_DENY`）。

**注意**：`REFERENCE/EVAL_ONLY`、`EVAL_ONLY_COMPARATOR` 這類「原子前綴＋限定詞」的取值，
本輪以原子前綴規則判定為合法 requiredness（保留原字串）。此為作者層解釋，非 carrier 明文，
已列入 AUTHOR_DESIGN_ONLY，Checker 可據此挑戰。

## 06｜交接（B3/B5）

- B3 mandatory `tool_key,source_row,requiredness`：requiredness 全 UNKNOWN → 全拒；B2 需先補欄位映射（D-5）。
- B5 mandatory 含 `metadata`：未取得 → 全拒；不得以工具名代替 license/ABI/lock。
- 接收結果為 `draft readiness`，**不是** ACK。

## 07｜未做

未安裝／啟用任何產品工具、未做 B5 選型、未連網取 metadata、未宣 `B2_ACCEPTED`。

## 發布｜remote readback（工程成果，非產品接受）

- Repo：`https://github.com/shw097-team/SQS-THC_MVP`，branch `main`
- commit：`acad969e80d37ac4299a81a0bd068925c1020d92`（remote `ls-remote` 回讀與本機 `rev-parse HEAD` 全等）
- 發布範圍：`70_W0_B1B8_20261126/r5/` 下 168 檔（引擎、TQAEP/OPS 收據、凍結 manifest、CLOSEOUT/HANDOFF、裁決清單）
- **未發布**：`40_OPS/b0_r5_sourcereadset.json`（含原條文逐字），依 `LOCAL_ONLY` 留本地，remote 只記其 sha256（見 `40_OPS/LOCAL_ONLY_EXCLUSIONS.json`）
- 憑證：以受管 `extraheader` 一次性注入，未寫入 git config、未出現在 argv/URL/log/commit
- 發布 ≠ 接受：`B1_ACCEPTED`／`B2_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` 仍未成立，`FIN_ORDER=DENY`
- 更新時間：2026-11-27T00:28:19+0800
