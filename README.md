# SQS-THC_MVP — SST/SQS-THC PH01 W0-B0（作者工程候選）

本 repo 是 **SST/SQS-THC/PH01/E00 W0-B0「合法來源讀取與逐欄缺件分離」** 的作者工程候選交付。
它不是產品驗收、不是 ledger、不是 Release；`FIN_ORDER=DENY` 不變。

## 狀態（請先讀）

- `status`: `B0_ENGINEERING_COMPLETE / PRODUCT_NOT_EXECUTED`
- `product_actual`: `NOT_EXECUTED`｜`expected_world_raw`: `EXPECTED_NOT_OBSERVED`
- 四 Ready：Draft `AUTHOR_DOCUMENT_WITH_TYPED_MISSING_ONLY`；Atom / Execute / Accept 全 `false`
- 缺的原綁定：`BR.B0.READER`（OriginalReader）、`BR.B0.EFFECT`（EffectRegistry）、`BR.B0.SCHEMA`（RawSchema）、`BR.B0.RUNNER`（CaseRegistry/fixture）、`BR.B0.AUTH`（Policy/Issuer）、`BR.B0.SCOPE`（acl_epoch）
- 因此本 repo 的通過僅代表「作者候選在作者 oracle 下自洽」，不代表 B1 可接收。

## 內容

| 目錄 | 內容 |
|---|---|
| `20_DEV/` | `b0_reader` 套件（B0.ROOT / B0.BYTES / B0.FIELDS / B0.RETURN + 作者控制面）、5 個測試模組、work order |
| `30_VERIFY/` | 獨立 checker（分離 session）之 22 點 oracle findings（R1 與 R2）與 lane receipts |
| `40_OPS/` | 工程證據蒐集器與實跑結果（exit、tree hash、raw stdout） |
| `00_PREFLIGHT/` | 來源 pin（SHA-256）與 B0 預檢；僅 locator 與雜湊，不含來源正文 |
| `SST_PLP_PH01_W0_B0_CLOSEOUT_HANDOFF.md` | CLOSEOUT 與 HANDOFF 兩章 |

## 重跑

```bash
cd 20_DEV
python -m unittest discover -s tests -v      # 59 tests
cd ..
python 40_OPS/collect_evidence.py            # 重算 tree hash 並記 raw
```

## 證據摘要

- Maker：59 tests OK（含 22 個 CaseID 測試）
- Checker R1：21 PASS / 1 FAIL（`build_read_set` 缺 top-level `write_set`）
- 修補 #1：`return_.py` 加 `"write_set": []` 與斷言
- Checker R2：22 PASS / 0 FAIL
- Canonical freeze：15 檔，tree `397d1ecaec6a7909…`（定義見 `40_OPS/candidate_freeze.json`）
- 車道 served 證據：`opencode-go/deepseek-v4.1-flash`，usage 200（receipts 見 `20_DEV/*receipt.json`、`30_VERIFY/*receipt.json`）

## 不含

未包含任何來源正文、知識庫原文、憑證、口令信封或受限 raw。`FIN_ORDER=DENY`：不含任何金融下單能力。
