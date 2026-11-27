# SUPERSEDED RECEIPTS｜rev2

本輪的凍結與接收收據在 Checker 查核期間被就地覆寫（finding M1／M8）。原件**不在磁碟上**，
只在公開 commit `64747d6` 的樹裡；本檔記錄它們的識別，供對帳，不假造「已還原」。

| 收據 | 被覆寫版本 | 現行版本 | 何處可取回 |
|---|---|---|---|
| `40_OPS/r7_candidate_freeze.json` | digest `6816248936b798d366b6ea593c70e4dc63d45d96b3080695bb83896e28e3d121`（41 成員） | digest `45d41c59…`（同檔，已被 rev2 取代） | commit `64747d6` 的 `71_W0_B0-B3_R7_20261127/40_OPS/r7_candidate_freeze.json`（經 redaction，位元組與原檔不同） |
| `40_OPS/r7_consumer_receipts.json` | B1/B2/B3 皆 `ACCEPT`、`checked_at=15:40:58`（envelope authority 已於 01:08 到期） | 三端 `REJECT / RIGHTS_UNVERIFIED`（window 已關） | 同上 commit 路徑 |
| `40_OPS/r7_consumer_selftest.json` | `11/11` PASS | `HOLD_BASELINE_NOT_VALID` | 同上 commit 路徑 |

## 為何不刪除、不重寫

- 被覆寫的版本仍有歷史意義（它們是 rev1 的主張），但**不可作為現行證據**引用。
- rev2 起凍結採寫一次（`r7_freeze.py` 無 `--revision` 即拒絕覆寫），新修訂一律新檔並記 `supersedes`。
- 若需要 rev1 的原始位元組，只能由 commit `64747d6` 取得；該處為 redacted 衍生物，與原始 digest 不同，差異已記在該 commit 的 `PUBLISHED_MANIFEST.tsv`（frozen sha 與 published sha 兩欄）。

記錄時間：2026-11-27T16:07:16+0800
