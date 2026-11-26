# SST_PLP_PH01_W0_B2_CLOSEOUT_HANDOFF_rev1

- subject `SST/SQS-THC/PH01/E00`｜OriginalWave `P1-W00M`｜BID `2`｜effect `SOURCE_READ`
- `write_set=[]`｜`preimage=N/A`｜`FIN_ORDER=DENY`｜窗口 `WIN-4e4b8cdc56c7`
- 本批**已真施工**：DEV-1（解析＋pin）與 OPS-1（QROWS／HARD／META／RETURN 之交換型別）已跑出真收據；**未**執行 2930 案 TQAEP、**未**做分離驗收、**未**選型（B5 職責）、**未**安裝任何工具。

## 1｜規格與身分

| 項 | 實測 |
|---|---|
| B2 正文 | 8,016,371 B；raw SHA256 `140de5bc1249dbb6e2d199dae336cf3a57741097aaf5cd883a7ec280e9199d3b` — 與 PROMPT pin 相等 |
| `spec.pin_match` | `true` |

## 2｜census（獨立重算，非引用作者敘述）

| 量 | 實測 | 原宣告 | 相符 |
|---|---|---|---|
| `UNIT_BEGIN` markers | 1,465 | 1,465 | ✅ |
| `payload_sha` 重算 | **1,465 / 1,465 精確**，0 failures | — | ✅ |
| `Q_SOURCE_ROW` | 1,385 | 1,385 | ✅ |
| `HARD` | 18 | 18 | ✅ |
| `E00_TECH` | 8 | 8 | ✅ |
| `TECH_ROUTE` | 54 | 54 | ✅ |
| Case 唯一 ID | **2,930**（POS 1,465／NEG 1,465） | 2,930 | ✅ |

## 3｜四 Q 原列（分母不互相補足）

| 象限 | 實測 | 原宣告 | 相符 |
|---|---|---|---|
| Q1 | **440** | 440 | ✅ |
| Q2 | **513** | 513 | ✅ |
| Q3 | **378** | 378 | ✅ |
| Q4 | **54** | 54 | ✅ |
| 合計 | **1,385** | 1,385 | ✅ |

判法：象限取自該 unit 自身標題 `#### B2.Uxxxx｜\`R3-REGISTRY-Qn::…\``，**不**由總數反推、**不**由鄰近章節推測（前兩版曾因標題位於 `UNIT_BEGIN` 之後而誤判，已修並以精確等式釘住）。

## 4｜Requiredness 保全（HARD 不降級）

| 檢項 | 結果 |
|---|---|
| HARD rows | 18，全部保留 `HARD` token |
| `downgraded_hard` | `[]`（空集） |
| Q4 `EVAL_ONLY` 對 Q1 HARD 之影響 | 無；未刪任何一列 |
| E00 TECH / TECH_ROUTE | 8 / 54，與原分母一致 |

## 5｜Wheel metadata 差額（B2 只記錄缺口，不選型）

| 檢項 | 值 |
|---|---|
| rows_without_bound_pin | **72** |
| 樣本 | 見收據 `wheel_metadata_ref.sample_unbound` |
| 說明 | pin／license／first_probe 之具名選定屬 **B5**；B2 僅回報缺口，不代選、不安裝、不以 Q4 optional 降級 HARD |

## 6｜可重跑入口（已實測）

```text
cwd = ...\70_W0_B1B8_20261126\20_DEV\b2_reader
cmd = python -B b2_parse.py      -> ..\..\40_OPS\b2_parse_<stamp>.json
cmd = python -B b2_ops_qrows.py  -> ..\..\40_OPS\b2_toolreadset_<stamp>.json
```

## 7｜收據

| 檔 | bytes | SHA256 |
|---|---|---|
| `40_OPS/b2_parse_20261126T121931.json` | 274,689 | `14147dcb94a71e598dc205b0c325b9cf226ae63d151f75bffc83ce355f2ae522` |
| `40_OPS/b2_toolreadset_20261126T122128.json` | 716,671 | `661ce45e8a86982e4cf45f4a804feb5ce0012f6ba7ca3958694daf7d0924bd0a` |

中間輪（`T121931`→`T122128` 之間的四次 Q 分母修正）全部保留為歷史，失敗輪不稱 LastGood。

## 8｜狀態

| 狀態 | 判定 |
|---|---|
| `B2_SPEC_READY` | 成立（pin 相符、1465/1465 payload pin） |
| `B2_ENGINEERING_CANDIDATE` | 成立（parser＋QROWS OPS 可重算） |
| `B2_PRODUCT_EXECUTED` | 成立（四 Op 之交換型別已產出真收據） |
| `B2_TQAEP_EXECUTED` | **不成立**（0/2930） |
| `B2_ACCEPTED` | **不成立** |
| `B2_COMPLETE` | **不成立** |

## 9｜HOLD

| # | 項 | 受影 | 責任 | Resume |
|---|---|---|---|---|
| H-B2-01 | 2,930 案未跑 | `B2_TQAEP_EXECUTED` | 工程 | 逐案 POS/NEG fixture 與真跑 |
| H-B2-02 | 無分離 Checker | `B2_ACCEPTED` | 分離 session | 同候選獨立判定 |
| H-B2-03 | 72 列無 bound pin | `WheelMetadataRef` | B5／R17 | B5 選型時補 version/license/probe |
| H-B2-04 | ToolReadSet 尚未被 B3/B5 真接收 | B2→B3／B2→B5 requires | B3/B5 | 依 §03.2 演算法各自接收 |

## 10｜交接給 B3／B5

- **B3 可消費**：`ToolReadSet@1`（1,465 rows，`tool_key`／`requiredness`／`source_row` 齊）＋ Q 分母 440/513/378/54。
- **B5 可消費**：`RequirednessDelta`（18 HARD 保全、0 降級）＋ 72 列 metadata 缺口清單。
- **不得冒**：任何工具已安裝、已選定、已資格化；B2 不代 B5 選型。
