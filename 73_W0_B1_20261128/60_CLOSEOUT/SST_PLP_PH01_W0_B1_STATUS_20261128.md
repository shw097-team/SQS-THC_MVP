# SST PH01 W0 B1｜狀態與交接（2026-11-28，T1 核收結果）

> 本件如實分帳：B1 **尚未接受**。已完成的是活動基線核收、原成功資產承接與 29/60 可取用案例的
> 重新分類；31 案保留具名 HOLD／PARK 與精確恢復條件。本件不宣 `B1_ACCEPTED`、不宣 `ReadyExecute`。

## 1｜活動基線

| 項 | 值 |
|---|---|
| B1 活動 SPEC | `…\W0_B0-B3_r7\SST_PLP_PH01_W0_B1_執行控制小包_實質正文_2026-11-27_r7_Native-first_CODEX_FINAL.md`，266543 B，`28437e1b249291f9…` |
| B1 入口 | `00_唯一交付入口_W0_B0-B3_2026-11-27_r7.md`（同目錄 `FINAL_SPEC_MANIFEST.tsv`） |
| 原 Case 規模 | 30 Unit／60 Case（18 BASE＋5 KERNEL＋7 FDA）＋EDGE/SEC 9 |
| B0 基線 | commit `69f8cb3d…`，`72_W0_B0_R3_20261127`，Receiver `c1f852cd…`（round 10 ACCEPT），B0 `COMPLETE` |
| B1 工程根 | `C:\Projects\Agent_Workspace\FHS-5_Workspace\SST_PH01_W0_B1_20261128` |
| 承接資產 | `10_CODE/b1_product/{b1_spec,b1_engine,b1_cli,b1_tqaep,b1_edge_sec}.py`（r7 原碼原樣）、`00_PREFLIGHT/{b1_locator_bindings,b1_source_allowlist,r7_preflight}.json`、`40_OPS/b1_r7_{tqaep,run_all,edge_sec,base_reconcile}.json`、`30_VERIFY/historical_r7_mechanical_verdict.md` |

資產逐檔 sha／bytes 見 `00_PREFLIGHT/asset_inventory.json`；本件未修改任何承接原件。

## 2｜r7 執行收據與本輪重新分類

原 r7 TQAEP 申報：`PASS 32／PASS_SOURCE_BOUND 5／PARTIAL 5／HOLD 18／FAIL 0`。
本輪**不以申報值當接受**，改以每案記錄的實際身份（commit／blob／raw sha）重判：

| 桶 | 案數 | 判定依據 |
|---|---|---|
| BASE POS 已驗 | **6** | 每個 target 皆有 commit＋blob＋raw sha（`BASE-001…005, 010`） |
| BASE NEG 已驗 | **18** | 刪列後 `BASE_ROW_MISSING`（拒絕路徑成立，刪除列本無 commit 身份） |
| BASE POS 無身份 | **11** | r7 判 PASS 或 PARTIAL，但 target 缺 commit/blob/raw（`006,007,008,009,011,012…017`）→ 一律降為非驗證 |
| BASE HOLD | **1** | `BASE-018`：含 allow-list 外 target |
| KERNEL SOURCE_BOUND | **5** | 內容 5/5 raw sha、span 64/64 相符；spec 的 commit pin 本地不可解析 |
| KERNEL HOLD | **5** | `SECOND_WRITER` 需原 Kernel 語義／原 Oracle |
| FDA HOLD | **12** | deny 係在**模擬 broker** 上觀測，非原 FDA artefact |
| FDA 常數案 | **2** | `broker_live_submit` POS/NEG 之 r7 PASS 建立在字面常數；r5 分離 Checker `B1C-R5-F01` 已裁不可作產品驗證 |

**可取用 29／60；未閉合 31。** `B1.NEG.*` 的 18 案與 6 案具身份 POS 可直接承接；其餘不得計入。

## 3｜四 Op 實際狀態

| Op | 狀態 | 依據 |
|---|---|---|
| `B1.REPO` | 部分可用 | 固定 commit `9a70501ad4bbf315…`、tree `688de895…`、local HEAD 與 remote 分欄；16 檔 allow-list 之 sha/bytes 歷史核對通過；`F01/D-1` 三 declared path 未具權採納 |
| `B1.BASE` | 24／36 可用 | 6 POS（具身份）＋18 NEG；11 POS 無身份、1 HOLD |
| `B1.FDA` | 0／14 可用 | 12 模擬 broker HOLD＋2 常數案；7 槽 typed 合約與 slot→action M:M 未以原 artefact 取證；未發 lease／未 live submit（`FIN_ORDER=DENY` 不變） |
| `B1.ROOTS` | 未取證 | 7 HardRoot／20 Edge 物理鏈本輪未重跑；未知保留 `UNKNOWN`，不以 grep 空結果冒 OFF |

## 4｜PARK 與精確恢復條件

| 項 | 內容 | Owner | Resume |
|---|---|---|---|
| `F01/D-1` | BASE-009／017 三 declared path；11 個無身份 POS | Repo/Source Owner | 逐 target 批准 namespace/root/path/commit/blob/raw/用途/接收權 → 具身份重讀並重跑 11 案 |
| `F02/D-2` | `BASE-018` allow-list 外 target；FDA 四項測試讀權 | Owner | 擴 allow-list 或授四項讀權；不得以 glob／mirror 替代 |
| `F03/D-3` | 7 槽原 artefact／合格 reader；12 案模擬 broker | FDA Owner／FDA-XQ-R13 Reader | 提供原 artefact 與讀權 → 重導 M:N 並重跑 14 案 |
| `F04/D-4` | 5 Kernel NEG 需原十條作者細規與 `SECOND_WRITER` oracle | Kernel Owner | 提供原規則／oracle → 逐案重判 |
| `fabricated_commit` | 原 finding 已 2 次實質修補 | — | 額度用盡，需 Owner 明確復工決定，不得改名重置 |

## 5｜四 Ready 與最終狀態

| Ready | 狀態 |
|---|---|
| ReadyDraft | PRESENT（r7 SPEC＋60 案表） |
| ReadyAtom | PARTIAL（29/60 可取用） |
| ReadyExecute | NOT_READY |
| ReadyAccept | NOT_READY |

**`B1_NOT_ACCEPTED_PARTIAL`**：無同候選分離接受，故不宣 `B1_ACCEPTED`；B0 的 `COMPLETE` 與三端接收不受影響。

## 6｜可交接 B4 的部分（受限）

- 可交：6 案具身份 POS BASE 的 `declared／resolved／tracked／commit／blob／raw sha` 與 18 案 NEG 的拒絕語義；
  5 Kernel 的內容 sha 與 64 個 symbol span（標 `SOURCE_BOUND`，非接受）。
- 不可交：`RepoReadSet` 全量、`CommitPathSpan` 全量、`UnknownPhysicalEdgeSet`（`B1.ROOTS` 未取證）與任何
  FDA 槽位結論。B4 不得以本件之部分結果升 `ReadyExecute`。
- B2／B3 文件與其自身合法獨立工程不受 B1 未接受影響。

## 7｜本輪未做（避免虛假完成）

未重跑產品、未修改 `10_CODE/b1_product/*`、未開 owner window、未發真 lease／live submit、未重取真來源、
未宣告任何 Case 由 HOLD 轉 PASS。下一輪若 Owner 給出 §4 任一恢復條件，即以受控最小範圍重跑對應案。
