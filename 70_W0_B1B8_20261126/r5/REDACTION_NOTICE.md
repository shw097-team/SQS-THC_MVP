# 公開版去識別化說明（redaction notice）

產生時間：2026-11-27T00:40:22+0800

公開樹只保留結構、程式、規則與 hash 摘要；下列檔案完整保存在本地 W，其 SHA256 如下，供有權者對帳。

| 未公開檔案 | 原因 | SHA256（本地原件） |
|---|---|---|
| `40_OPS/b0_r5_sourcereadset.json` | LOCAL_ONLY: verbatim source clause | `bdb2a03f079412434f5de11247a7a73b015d96440b00d6bc04dd6d0e05da8d0e` |
| `40_OPS/b1b2_r5_publish_record.json` | contains window id and credential-adjacent references | `152694afb5723acaf89bd6ea3b255012380eb9d1a69a0579d5a7e5addb32281e` |
| `40_OPS/r5_consumer_receipts.json` | contains the owner window id, the private rights-receipt digest and absolute K paths | `da01a24740f63dee32d12d88c03be768686bc69050d9a3b6a1313f906fb58e6b` |

未改寫 Git 歷史、未 force push；本說明以增量 commit 加入。
