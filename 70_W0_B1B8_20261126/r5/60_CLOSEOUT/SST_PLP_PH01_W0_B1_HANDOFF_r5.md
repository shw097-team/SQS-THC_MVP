---
artifact_kind: BATCH_CLOSEOUT_HANDOFF
subject: SST/SQS-THC/PH01/E00
original_wave: P1-W00M
spec_version: 2026-11-26_r5_Native-first_CODEX_FINAL
spec_manifest_sha256: 3c816deb8fc216eae831dddfac396217d5b224fc7575c03415ef9f08ebbfa046
candidate_manifest_sha256: ef9449a5a7eb9d6bff51f050ac6d452f877b9e3cf4659de412fac6b851b2dad6
generated_at: 2026-11-26T23:35:47+0800
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
