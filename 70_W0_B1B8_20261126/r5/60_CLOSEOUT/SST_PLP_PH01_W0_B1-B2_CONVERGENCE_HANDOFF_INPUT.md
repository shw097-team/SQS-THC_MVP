# W0 B1–B2 收斂性結案｜下一階段（W0M 實證反饋與 B3–B8 雙去耦合重構）交接輸入

- 產生：本輪工程收尾
- 性質：**交接輸入**，不是產品接受、不是 Grant、不是 B3 產品宣稱
- 凍結：以 `40_OPS/b1b2_r5_candidate_freeze.json` 為同候選身份
- 宣稱上限：`B1_ACCEPTED`／`B2_ACCEPTED`／`B3_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` **均未成立**；`FIN_ORDER=DENY`

本文件只回答一件事：下一階段重構接手的**實據、缺陷與未閉合義務**是什麼。四個部分：①B1／B2 施工實證 ②共通契約缺陷 ③未閉合原義務 ④B3 來源映射與可施工性研究。

---

## 1｜B1／B2 施工實證（可重用，不需重跑）

| 批 | 規模 | 真跑結果 | 位置 |
|---|---|---|---|
| B1 | 30 Unit／60 Case／4 Op | PASS 32、PASS_EVIDENCE 5、PARTIAL 5、FIXTURE_ONLY 12、HOLD 6、FAIL 0；EDGE/SEC 9/9 | `b1_r5_run_all.json`、`b1_r5_tqaep.json`、`b1_r5_edge_sec.json` |
| B2 | 1,465 Unit／2,930 Case／4 Op | PASS 2,854、HOLD 76、FAIL 0；ToolReadSet union 1,465 | `b2_r5_tqaep.json`、`b2_r5_tool_readset.json` |
| B0 入站 | 產品真讀 | `SST.B0.SourceReadSet/2`、exit 0、errors 0、`write_set=[]`、`fin_order=DENY` | `b0_r5_sourcereadset.json`（LOCAL_ONLY） |
| 三端接收 | B1／B2／B3 | 各 ACCEPT，13 欄齊，`checked_at` 實跑、rights ref 綁當次視窗 | `r5_consumer_receipts.json`（LOCAL_ONLY） |
| 接收反例 | 11 臂 | 1 POS＋10 單變異全拒，first_fail 精確 | `r5_consumer_selftest.json` |
| META | 18 HARD | 2 條取得官方 metadata（pydantic 2.14.4、jsonschema 4.26.0，PyPI 回應 SHA 已釘）、7 UNBOUND、9 非發行物 | `b2_r5_meta.json` |
| 分離驗收 | Round 4 | ACCEPT／0 mandatory／6 項全 PASS；1 MINOR（信任根 ACL 只 broad-principal 封閉） | `b1b2_checker_r5_verdict_round4.md` |

**重用規則**：同候選、同 tuple、未受影者直接承接；只有 change cone 內重跑。B0 的 137＋15 不重跑。

---

## 2｜共通契約缺陷（跨批同型，重構時一次修）

| # | 缺陷 | 在哪裡發作 | 修法方向 |
|---|---|---|---|
| C-1 | **自比當驗證** | `b2_engine` HARD 早期拿 unit 值比 carrier 同值；B3 早期拿 payload 比自身 | 一律「兩份不同紀錄」比對，並在報告裡標出兩邊來源 |
| C-2 | **未執行記 PASS** | B2 首版 2,788 案標 PASS 但 spec 自陳未跑 | 判定只能是 PASS／FAIL／HOLD／NOT_EXECUTED，且 `attempted=True` 才可 PASS |
| C-3 | **常數 gate 冒充否證** | `broker_live_submit` 用常數 dict；`STATE_CONFLICT` 通用 token gate 反覆修不好 | gate 必須讀真 bytes 並驗 digest；通用狀態機不得覆蓋逐案原義 |
| C-4 | **位置欄位猜測** | `source_payload[2]` 當 requiredness（991/1385 錯） | 只認 carrier 宣告欄；未宣告 → NOT_APPLICABLE 並附行號，不得猜 |
| C-5 | **假綠詞彙** | `PASS_PRESERVED`／`PASS_INTERPRETED`／`CONTRACT_COMPATIBLE` 被當 PASS | 詞彙表收斂為 PASS／HOLD／NOT_EXECUTED／REFUSAL，其餘僅為 evidence |
| C-6 | **envelope hash 冒充 producer freeze** | B3 接收 `candidate_digest` 曾取 envelope SHA | producer freeze 與 envelope SHA 分欄，缺 freeze 即 `PRODUCER_FREEZE_UNBOUND` |
| C-7 | **locator 漂移被當缺失或當同件** | `W0_B0-m`→`W0_B0-B8`、`PHASE 00~04`→`01~04`、`DOC-nn(8)`→`DOC-nn` | 身份一律以 SHA 認；resolved 記 `CANDIDATE_NOT_RATIFIED`，不改 declared |
| C-8 | **無界掃描越界** | M-01 事件 | 只掃受權根；先驗權再開檔 hash；失敗／拒絕／缺失三態分開 |
| C-9 | **計數漂移** | closeout 曾寫 1,545 HOLD（實際 76）、72/75/1460 混用 | 文件數字一律由收據生成，禁手抄 |

---

## 3｜未閉合原義務（依五類分帳）

| 類 | 內容 | 對應 Owner |
|---|---|---|
| 已可取得、本研究已完成 | 281 Unit 原映射（488/488 clause SHA 全等）、30/92 PIPD pin（依 SHA 認回）、112＋DOC_BRIDGE 文件取證 | — |
| 待工程實作 | B2 18 HARD `source_row=null`、9 HARD non-loss NEG 的 inner 實作、B3 44 案真 mutation、B3 四 Op 語義化 | 工程 |
| 待設計補編 | DOC_BRIDGE heading 契約（已採納 ATX `^#{1,6} `，10 案仍不符）、BEHAVIOR／SEAM／RECOVERY typed fixture（73／5／2，骨架已產） | 工程＋具權採納 |
| 真需原權位 | D-2（四測試讀權）、D-3（7 槽 M:N）、D-4（五 Kernel 語義）、TT-UP-1／6 E00／54 ROUTE、62 個未定位 DOC pin | FDA／Kernel／R17／文件持有人 |
| 下游驅動 | B4 驅 B1 BASE PARTIAL（012–016）、D-1 三 locator；B5 驅 B2 76 HOLD；B6 驅 20 Edge／8 Port | B4／B5／B6 |

> 舊「全部等 OWNER 提供原資料」的清單**作廢**（見 `SST_PLP_PH01_W0_B1-B3_OWNER_DECISION_LIST_r5.md`）。

---

## 4｜B3 來源映射與可施工性研究（本輪新增，供下一階段接手）

| 發現 | 內容 |
|---|---|
| 原映射存在於 Unit JSON，不在 payload | `direct_parent_ref` ＋ `resolved_source_ref` ＋ `direct_clause_sha` 三件；488/488 切片 SHA 全等 |
| payload 首欄不是行號 | `PLP-00` 的 528 與藍圖行 1606 無關；以 payload 猜行號會被判錯（本輪曾犯並已撤回） |
| DOC_BRIDGE 原件在封存區 | `【4】舊版封存\SWOF_SQS-THC_PIPD-LS-PKG\DOC`，30/92 pin 命中；檔名 `(8)` 後綴已不存在 |
| B3 四 Op 已有真 callable | `b3_product.py`：JOIN／CHILD／ROUTE／COMMIT；`b3_neg.py`（mutation 執行器，已暫停）；`b3_closeout.py`（typed fixture＋文件生成） |
| B3 現況分帳 | 752 案：SOURCE_BOUND 688／REFUSAL 44／HOLD 20／NOT_EXECUTED 0 |
| 產品寫入 | `b3_ledger/SourceChildLedger.draft.v2.md`（29,624 B、`cc1cb866…`、preimage ABSENT、readback 相符）；**僅此一次，正式施工已依 Owner 指示暫停** |
| 未宣稱 | `B3_ACCEPTED` 未成立；44 案仍用通用 JOIN 三臂；ROUTE 只到「來源可證」不是語義路由 |

**接手建議**：下一階段重構時，把 C-1…C-9 當成一次共同的契約修補；B3 這批研究可直接作 W0M 反饋與 B3 重構的實證輸入，不需重做映射研究。

---

## 5｜本輪結束狀態

- B1／B2：**PARTIAL／PARK_UNTIL_DELTA 工程結案**（非產品接受）
- B3：**研究與可施工性輸入已交付**，正式施工暫停
- 發布：增量 commit＋remote readback；LOCAL_ONLY 原件留本地；公開樹已去識別化
- 下一階段：W0M 實證反饋 ＋ B3–B8 產品與施工雙去耦合 Native-first 最小受影精簡重構
