# LAYERS｜本輪檔案分層（rev7）

- 產生：2026-11-27T19:52:14+0800
- 現行候選：`40_OPS/r7_candidate_freeze.rev12.json`／`8fe2b08d56670234…`

## 統計

| 層 | 檔數 |
|---|---:|
| PRIMARY | 44 |
| CURRENT_CANDIDATE | 26 |
| SUPERSEDED | 19 |
| VERDICT_SUPERSEDED | 1 |
| DOC_HISTORY | 12 |
| LOCAL_ONLY | 1 |
| EFFECT | 2 |

## 升格（本輪）

| 項目 | 路徑 | 依據 |
|---|---|---|
| B0 descriptor renewal | `40_OPS/b0_descriptor_renewal.json` | window WIN-5afc943249a6, ceiling READ_ONLY_PROBE, only authorization/usage/time changed |
| B0 current SourceReadSet/2 | `40_OPS/b0_current_sourcereadset.json` | exit 0, 2 sources, 14 authority fields, missing=[], write_set=[] |
| B0 three-end receive | `40_OPS/r7_consumer_receipts.json` | B1/B2/B3 ACCEPT, currency CURRENT (usage_evidence_sha equals the live receipt) |
| consumer self-test | `40_OPS/r7_consumer_selftest.json` | 12/12 arms, including ENVELOPE_AUTHORITY_EXPIRED |
| B0 product case suite | `40_OPS/b0_product_test_2026-11-27.log` | 137 tests OK, bounded temp root, TMPDIR unset |

## 未升格（不連帶）

- B1：PARTIAL_PARK_UNTIL_DELTA (no new recoverable delta this round)
- B2：PARTIAL (20 route FirstFail divergences need an owner decision)
- B3：ReadyAtom false: 183/273 source-bound atoms have no declared owner

## 規則

- `PRIMARY`：accepted or engine/config used by this round
- `CURRENT_CANDIDATE`：this round's live candidate, not accepted
- `SUPERSEDED`：older freeze/manifest revision, kept for audit, never cited as current
- `DOC_HISTORY`：older document revision, kept for audit
- `LOCAL_ONLY`：rights-bearing; never published, sha recorded instead
- `EFFECT`：a product write (draft ledger), evidence not input
- `VERDICT_SUPERSEDED`：a separated-checker verdict whose judged candidate digest is no longer current; history only, must not be cited as applying to the current candidate
