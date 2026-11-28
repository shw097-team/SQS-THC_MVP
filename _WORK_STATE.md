# _WORK_STATE｜SST_PLP_PH01 W0（2026-11-28 +08:00）

> 本檔是**主用狀態指標**。任何「已接受」的對象都必須在此指向其固定 commit 與受檢 manifest；
> 未接受者一律標 `candidate`／`PARK`，不得以檔案存在或聊天回報代替。

## 1｜當前狀態

| 批 | 狀態 | 受檢對象 | 分離判定 | 交付 |
|---|---|---|---|---|
| W0 B0 | **`B0_COMPLETE`** | 候選 `c1f852cd50247aaa…`（13 成員，`72_W0_B0_R3_20261127/60_CLOSEOUT/CANDIDATE_receiver_r34.tsv`） | `ACCEPT`、blocking 0（`72_…/30_VERIFY/verdict_r32_round10.json`，2026-11-28T00:52:10+08:00） | `72_W0_B0_R3_20261127` @ `7f1665bea223f3de…` |
| W0 B1 | `B1_NOT_ACCEPTED_PARTIAL` | 29/60 案可用；31 案具名 HOLD | 無（未送分離接受，不得宣 `B1_ACCEPTED`） | `73_W0_B1_20261128` @ `ae323494cdb057d3…` |
| W0 B2／B3 | 文件已存在，產品未接受 | — | — | 歷史 `71_W0_B0-B3_R7_20261127`（研究錨 `b695d8d2…`） |

**B0 活動鏈**（只有這一組是 active，其餘同名前綴皆為歷史或歸檔）：
`B0_READ_CONTEXT_20261127_r10.json` → `b0_sourcereadset_r11_20261127.json` → `DEPLOYMENT_prod_20261127_r12.json`
（`deployment.py:PINNED['prod']`）→ `r13_inbound_b{1,2,3}_receipt.json`（各 2/2 ACCEPTED）。
OWNER window `WIN-056f06fe7b02` 已 CLOSED；新接收需重新取得合法權利。

## 2｜分層規則（2026-11-28 已整理）

| 層 | 位置 | 內容 |
|---|---|---|
| **main（主用）** | `72_…/60_CLOSEOUT`（7 檔）、`72_…/10_CODE`、`72_…/00_PREFLIGHT`（r10／r12）、`72_…/40_OPS`（r13 收據） | 受檢候選、最終 CLOSEOUT/HANDOFF、freeze、活動鏈 |
| **archive（歷史）** | `72_…/90_ARCHIVE/superseded_revisions`（110 檔） | r8–r33 的文件、freeze、manifest、候選 manifest；**不得**當活動指標 |
| **evidence（證據）** | `72_…/30_VERIFY/verdict_r*_round*.json`（10 輪） | 未經改寫的分離判定原文 |
| **candidate（未接受）** | `73_W0_B1_20261128` | B1 基線、r7 原碼原樣、重新分類收據、PARK |
| **disposable** | `publish/`、`tmp/`、`__pycache__/` | 本地建置物；`tmp/` 與 `__pycache__` 已刪，`publish/` 只在本機 clone |

## 3｜不變量

- `write_set=[]`、`preimage=N/A`、`FIN_ORDER=DENY`（B0 產品效果不變）。
- LOCAL_ONLY 原件不出本地；公開投影去敏，對照表在各波 `REDACTION_NOTICE.md`。
- 歷史 commit 不改寫；被取代的修訂只歸檔，不刪 git 歷史。

## 4｜未閉合（需 Owner）

B1 的 `F01/D-1`（BASE-009/017 declared path 批准）、`F02/D-2`（allow-list／FDA 四項讀權）、
`F03/D-3`（7 槽原 artefact 與合格 reader）、`F04/D-4`（Kernel 原十條規則與 `SECOND_WRITER` oracle），
以及 `fabricated_commit` 已用盡 2 次額度。逐項恢復條件見
`73_W0_B1_20261128/60_CLOSEOUT/SST_PLP_PH01_W0_B1_STATUS_20261128.md` §4。

## 5｜歷史

2026-11-24 起的 `B0_ENGINEERING_COMPLETE / PRODUCT_NOT_EXECUTED` 狀態、車道修復與早期 `20_DEV`／`40_OPS` 內容，
保留在本 repo 根目錄與 git 歷史中，僅作歷史；**不代表**當前狀態。
