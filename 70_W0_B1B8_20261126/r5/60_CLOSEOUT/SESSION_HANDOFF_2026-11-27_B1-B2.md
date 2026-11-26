# SESSION HANDOFF｜W0 B1–B2 收斂結案 → 下一 SESSION 續跑指引

- 產生：本 SESSION 結案時
- 產出根：`C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126`
- 遠端：`https://github.com/shw097-team/SQS-THC_MVP`（public；已去識別化）
- 宣稱上限：`B1_ACCEPTED`／`B2_ACCEPTED`／`B3_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` **全部未成立**；`FIN_ORDER=DENY`；`distribution=LOCAL_ONLY`（原件）

---

## 1｜先讀這三份（按序）

| 順序 | 檔案 | 用途 |
|---|---|---|
| 1 | `DELIVERY_MANIFEST.json` | `promotion_state=CURRENT_CANDIDATE`、32 條 current_pointers、`phase_status` |
| 2 | `60_CLOSEOUT/SST_PLP_PH01_W0_B1-B2_CONVERGENCE_HANDOFF_INPUT.md` | B1/B2 實證、**九條共通契約缺陷 C-1…C-9**、五類責任分帳、B3 研究結論 |
| 3 | `60_CLOSEOUT/SST_PLP_PH01_W0_B1-B2_CLOSEOUT_r5.md` ＋ `…_HANDOFF_r5.md` | 數字由收據生成的最終狀態 |

## 2｜層位（工程衛生後）

| 層 | 位置 | 規則 |
|---|---|---|
| 主用候選 | `70_W0_B1B8_20261126\`（33 MB） | 只有 `current_pointers`（32）＋凍結 manifest（45 成員）為現行 |
| 歷史 | `…\SQS-THC_MVP_Workspace\90_ARCHIVE\70_W0_B1B8_20261126_pre_r5\`（135 MB） | 129 項：timestamped runs、round1–6 freeze、`GPT_WORK_CANDIDATE` 舊規格、舊 descriptor 候選。**保留不刪**，不在指標內 |
| 暫存 | 已清 | `__pycache__`／`.pyc`／`%TEMP%` 探針檔 |
| 公開衍生物 | `dist\SQS-THC_MVP\70_W0_B1B8_20261126\r5\` | 只含結構／程式／hash；`LOCAL_ONLY` 檔另列 |

層位機讀：`C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\90_ARCHIVE\LAYERS.json`

## 3｜已升格／未升格（本次核對結論）

- **沒有任何項目升格為 ACCEPTED_PRIMARY**：B1／B2／B3 均未通過產品接受，故仍為 `CURRENT_CANDIDATE`。這是正確狀態，不是遺漏。
- 已「進主用」者：六份 r5 CLOSEOUT／HANDOFF、凍結 manifest、B0 真讀收據、三端接收、META、B3 研究與 typed fixture、四 Op 引擎。全部在 `current_pointers` 且已發布。
- 被誤放候選層者：**無**（本次已逐一核對 32 條指標全可解析）。
- 曾被錯置、已歸位：舊候選規格、timestamped runs（→ 歷史層）、`B0_READ_CONTEXT_2026-11-26_RENEWAL_CANDIDATE.json`（→ 歷史層；採用的是 `B0_READ_CONTEXT_2026-11-26.json`）。

## 4｜下一 SESSION 可直接續跑的工單

| # | 工單 | 前置 | 不需新權限 |
|---|---|---|---|
| W-1 | B3 44 案真 mutation（`b3_neg.py` 已寫好但被暫停；需先加檔案讀取快取，否則 >180 s） | 無 | 是 |
| W-2 | 10 份 DOC_BRIDGE heading 不符的規則確認（ATX `^#{1,6} ` 已採納，10 案兩數並列） | 原文件作者或內容版本確認 | 是（研究） |
| W-3 | 其餘 62 個 DOC pin 的世代定位 | 需指出合法位置 | 是（只讀） |
| W-4 | BEHAVIOR／SEAM／RECOVERY 語義化（typed skeleton 已產：73／5／2） | 原 Reader 契約 | 部分 |
| W-5 | B4／B5 真 mandatory 接收 | B1 D-1/D-3、B2 TT-UP-1 | 否（需原權位） |

## 5｜需要原權位的（不要代簽）

D-2 四測試讀權、D-3 七槽 M:N、D-4 五 Kernel 語義、TT-UP-1／6 E00／54 ROUTE、B3 正式 COMMIT 若再開需 `REPOSITORY_WRITE` 以上 ceiling。清單：`60_CLOSEOUT/SST_PLP_PH01_W0_B1-B3_OWNER_DECISION_LIST_r5.md`。

## 6｜重現指令（不需口令的部分）

```
cd C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126\20_DEV\b1_r5
python -B b1b2_freeze.py          # 重算凍結（應得 45 成員）
python -B closeout_gen.py         # 由收據重生成六份文件
python -B b3_tqaep.py             # B3 752 案分帳（688/44/20/0）
python -B b3_product.py --dry-run # 四 Op 記憶體版（不寫產品檔）
```

## 7｜三個必須記住的坑

1. `b1_spec.load_b2()` 會併掉兩個 HARD key → 一律用 `w0_spec.units()`。
2. Unit 的 `direct_parent_ref` 目錄名有筆誤 `W0_B0-m`，正解 `W0_B0-B8`；身份以 SHA 認，記 `CANDIDATE_NOT_RATIFIED`。
3. `owner_window.py open` 若已有窗會回 `WINDOW_ALREADY_OPEN`；舊窗 broker 不在時只能 `close --force`（不簽章）。
