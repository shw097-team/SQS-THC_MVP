---
artifact_kind: BATCH_CLOSEOUT_HANDOFF
subject: SST/SQS-THC/PH01/E00
original_wave: P1-W00M
spec_version: 2026-11-26_r5_Native-first_CODEX_FINAL
spec_manifest_sha256: 3c816deb8fc216eae831dddfac396217d5b224fc7575c03415ef9f08ebbfa046
candidate_manifest_sha256: 13359ee612d77e232880d7ece68df04fc755978968ecf9b027e1edfb3596385f
generated_at: 2026-11-27T00:55:19+0800
product_actual: EXECUTED_SOURCE_READ_ONLY
fin_order: DENY
distribution: LOCAL_ONLY
---

# W0 B1–B2｜合併 HANDOFF（下一階段唯一入口）

## 01｜可交接的產物（真存在）

| 產物 | 位置 | 證據 |
|---|---|---|
| B1 引擎＋CLI | `20_DEV/b1_r5/b1_engine.py`、`b1_cli.py` | manifest 內具 hash |
| B1 TQAEP | `20_DEV/b1_r5/b1_tqaep.py` → `40_OPS/b1_r5_tqaep.json` | 60 案逐案 |
| B1 EDGE/SEC | `b1_edge_sec.py` → `b1_r5_edge_sec.json` | 9/9 PASS |
| B2 引擎＋TQAEP | `20_DEV/b1_r5/b2_engine.py`、`b2_tqaep.py` → `b2_r5_tqaep.json` | 2,930 案 |
| B2 接收 | `b2_r5_receivers.json` | B3 0/1465、B5 0/1465（正確拒） |
| 凍結 | `b1b2_r5_CANDIDATE_MANIFEST.tsv` | `13359ee612d77e232880d7ece68df04fc755978968ecf9b027e1edfb3596385f` |

## 02｜下游可立即做的事

- **B3/B4/B5/B6 可先建最小 receiver**：介面已存在（13 欄 receipt、mandatory 檢查、拒收路徑）。
- 不得把本 HANDOFF 當 ACK；接收者必須自帶 expected set 並自行驗 rights。
- B4 對 B1：只消費 tracked 的 `commit/path/blob`；`missing` 為明確 null，不得補值。
- B5 對 B2：`requiredness` 目前為 UNKNOWN，任何以推測值填入都會被拒。

## 03｜明示未具

`B1_ACCEPTED`、`B2_ACCEPTED`、`W0_COMPLETE`、`W1 ReadyExecute` 全部 **NO／未宣**。
Repo 未推送；`distribution=LOCAL_ONLY`。GUI/lease/broker 未接觸。

## 發布｜remote readback（工程成果，非產品接受）

- Repo：`https://github.com/shw097-team/SQS-THC_MVP`，branch `main`
- commit：`acad969e80d37ac4299a81a0bd068925c1020d92`（remote `ls-remote` 回讀與本機 `rev-parse HEAD` 全等）
- 發布範圍：`70_W0_B1B8_20261126/r5/` 下 168 檔（引擎、TQAEP/OPS 收據、凍結 manifest、CLOSEOUT/HANDOFF、裁決清單）
- **未發布**：`40_OPS/b0_r5_sourcereadset.json`（含原條文逐字），依 `LOCAL_ONLY` 留本地，remote 只記其 sha256（見 `40_OPS/LOCAL_ONLY_EXCLUSIONS.json`）
- 憑證：以受管 `extraheader` 一次性注入，未寫入 git config、未出現在 argv/URL/log/commit
- 發布 ≠ 接受：`B1_ACCEPTED`／`B2_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` 仍未成立，`FIN_ORDER=DENY`
- 更新時間：2026-11-27T00:55:19+0800
