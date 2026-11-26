---
artifact_kind: BATCH_CLOSEOUT_HANDOFF
subject: SST/SQS-THC/PH01/E00
original_wave: P1-W00M
spec_version: 2026-11-26_r5_Native-first_CODEX_FINAL
spec_manifest_sha256: 3c816deb8fc216eae831dddfac396217d5b224fc7575c03415ef9f08ebbfa046
candidate_manifest_sha256: f851ede0ea038e4b522a934ce756abbb98cbca43d44eb41c2b38a147637af6b2
generated_at: 2026-11-27T00:47:47+0800
product_actual: EXECUTED_SOURCE_READ_ONLY
fin_order: DENY
distribution: LOCAL_ONLY
---

# W0-B1｜HANDOFF（r5 產品層）

## 01｜producer 輸出（B4 可消費）

| 欄 | 值／規則 |
|---|---|
| RepoReadSet | `commit,path,blob,missing`；只有 tracked 才有 commit，disk-untracked 一律 null |
| CommitPathSpan | 逐 BASE/KERNEL 原 path 與 span；external carrier 無 commit（自身 Git 身分不同） |
| FDA inventory | 7 slot 全 `CARRIER_LEVEL_ONLY`；`live_broker=DENY_ALWAYS` 讀自矩陣 L24 |
| UnknownPhysicalEdgeSet | 七根／20 Edge = UNKNOWN（不推 OFF） |

## 02｜consumer 義務

- B4：自帶 expected set；不得把 `missing:null` 當 0；不得用 remote URL 當 local commit。
- B6：只 observes；`UNKNOWN` 不得當 OFF。

## 03｜未具

`B1_ACCEPTED=NO`；D-1…D-4、TT-UP-1/2 未閉合；本檔不是 ACK。

## 發布｜remote readback（工程成果，非產品接受）

- Repo：`https://github.com/shw097-team/SQS-THC_MVP`，branch `main`
- commit：`acad969e80d37ac4299a81a0bd068925c1020d92`（remote `ls-remote` 回讀與本機 `rev-parse HEAD` 全等）
- 發布範圍：`70_W0_B1B8_20261126/r5/` 下 168 檔（引擎、TQAEP/OPS 收據、凍結 manifest、CLOSEOUT/HANDOFF、裁決清單）
- **未發布**：`40_OPS/b0_r5_sourcereadset.json`（含原條文逐字），依 `LOCAL_ONLY` 留本地，remote 只記其 sha256（見 `40_OPS/LOCAL_ONLY_EXCLUSIONS.json`）
- 憑證：以受管 `extraheader` 一次性注入，未寫入 git config、未出現在 argv/URL/log/commit
- 發布 ≠ 接受：`B1_ACCEPTED`／`B2_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` 仍未成立，`FIN_ORDER=DENY`
- 更新時間：2026-11-27T00:47:47+0800
