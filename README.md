# SQS-THC_MVP — SST/SQS-THC PH01 W0-B0（r4 Native-first 工程候選 + 真產品執行證據）

本 repo 是 **SST/SQS-THC/PH01/E00 W0-B0「合法來源讀取、真欄位核實與逐源缺件分離」** 的 r4（`2026-11-25_r4_Native-first`）工程交付：
v2 wire `SST.B0.SourceReadSet/2`、四個 Op（ROOT／BYTES／FIELDS／RETURN）、可信啟動接線與 stdin CLI，附**真合法來源**的產品執行 raw 與四個單變異拒絕。

它不是產品驗收、不是 ledger、不是 Release；`FIN_ORDER=DENY`、`write_set=[]`、`preimage=N/A` 不變。

## 狀態（請先讀）

| 狀態 | 實際 |
|---|---|
| `B0_SPEC_READY / ACTIVE` | 成立（文檔自驗，非產品驗收） |
| `B0_ENGINEERING_CANDIDATE` | 成立（25 檔同候選 freeze、132 tests OK） |
| `B0_PRODUCT_EXECUTED` | 成立（真來源 POS exit 0；四個單變異 NEG 各回專屬碼；無產品寫入） |
| `B0_CORE_ACCEPTED` | **不成立**（Native OFF 的 network／transitive tracing 為 NOT_VERIFIED；真 Consumer 接收未發生） |
| `B0_COMPLETE` | **不成立**（無真 B1/B2/B3 接收） |
| `B1_CONTRACT_COMPATIBLE / CONSUMER_NOT_YET_EXECUTED` | 成立（僅獨立契約探針） |

- 候選 freeze：`candidate_digest = 5ec38e9c1835dba89c5755acd2f2c720aadd9193dd96d08d0a1fe7ddfa36c456`（25 檔；`40_OPS/candidate_freeze.json`）
- 產品 CLI：`python -B -m b0_reader.cli read --request-json -`（stdin 收 `B0ReadRequest/2`，stdout 一個 v2 JSON）
- 可信 descriptor：`00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json`，SHA256 `b8759ca7f5c213024c4046db07494cabb355d39d051b0082ff043845e9fb45e0`，3,612 bytes（`native_entry.py` 內固定 pin）

## 內容

| 目錄 | 內容 |
|---|---|
| `20_DEV/b0_reader/` | `errors`／`root`／`bytes_`／`fields`／`requiredset`／`return_`／`winio`／`native_entry`／`cli`／`controls`（`controls` 為作者層，未改） |
| `20_DEV/tests/` | 10 檔 132 案：原始 14 主案＋8 補充群、N01–N09、真 junction／share 競態、獨立契約探針、Native OFF、`trust_fixture.py`（測試專用信任夾具；生產 package 內無 mint API） |
| `00_PREFLIGHT/` | 可信 descriptor、兩份 RequiredSetSpec（真來源 pin 與真條文 span）、來源 pin 證據、預檢 |
| `30_VERIFY/` | 兩輪獨立 checker（分離 session）findings 與 lane 收據 |
| `40_OPS/` | DEV-0 基線、freeze 工具與結果、真跑 raw（POS／四 NEG）、無寫比對錄製器 |
| `SST_PLP_PH01_W0_B0_CLOSEOUT.md` | CLOSEOUT（真缺陷清單、OPS raw、狀態、未閉合項與恢復條件） |
| `SST_PLP_PH01_W0_B0_HANDOFF.md` | HANDOFF（B1/B2/B3 接口、entry 真值、信任錨與 ACL 分界） |

## 重跑

```bash
cd 20_DEV
unset TMPDIR                       # 測試套件要求 TEMP 指向 W 內；Hermes 預設會設 TMPDIR
export PYTHONDONTWRITEBYTECODE=1
export TEMP='C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\20_DEV\.tmp_tests'
export TMP="$TEMP"
python -B -m unittest discover -s tests -v     # 132 tests, ~290 s
```

真產品執行（需要有效 Owner 授權與已 sealed 的 descriptor 目錄）：

```bash
cd 20_DEV
python -B -m b0_reader.cli read --request-json - < ../40_OPS/b0_read_request_2026-11-25.json
```

## 證據摘要（皆為實跑）

- 真來源 POS：`exit=0`、stdout 5,429 bytes、兩個 entry；`sha`／`clause_sha`／`value_sha` 皆由原件重算相符
- 四個單變異 NEG：`SOURCE_PIN_MISMATCH`（exit 2）、`SPAN_INVALID`（exit 2）、`EFFECT_DENIED`（exit 64）、`SCOPE_MISMATCH`（exit 64）
- 無產品寫入：W 樹以 size+mtime+內容 sha256 前後比對、K 來源根未變；未涵蓋面（registry／network／child process）已在 CLOSEOUT 明列為 NOT_VERIFIED
- 獨立 checker 第一輪主動否證兩項 P0（caller 可自造 context、撤權 fail-open）與一項 P1（ACL 未核），修補後第二輪重判見 `30_VERIFY/`

## 不含

未包含任何來源正文、知識庫原文、憑證、口令信封、Owner 私鑰或受限 raw。`FIN_ORDER=DENY`：不含任何金融下單能力。
