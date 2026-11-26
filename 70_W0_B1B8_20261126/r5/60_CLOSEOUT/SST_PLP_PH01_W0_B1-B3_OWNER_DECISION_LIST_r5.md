# W0 B1–B3｜原責任五類分帳（r5，取代舊「全部等 OWNER」清單）

產生：2026-11-27T00:40:59+0800｜本文件不是 Grant、不是接受。

## 0｜現況（真跑計數）

| 批 | 計數 |
|---|---|
| B1 | PASS 32｜PASS_EVIDENCE 5｜PARTIAL 5｜FIXTURE_ONLY 12｜HOLD 6（共 60） |
| B2 | PASS 2,854｜HOLD 76（共 2,930）；receiver B3 1,351 收／114 拒、B5 4 收／1,461 拒 |
| B3 | SOURCE_BOUND 636｜REFUSAL 44｜HOLD 12｜NOT_EXECUTED 60（共 752） |

B3 的 636 案已由各 Unit 自帶的 `resolved_source_ref` ＋ `direct_parent_ref` ＋ `direct_clause_sha` 逐案重算（488 個映射全等；目錄筆誤 `W0_B0-m`→`W0_B0-B8` 已記為 `CANDIDATE_NOT_RATIFIED`）。

## 1｜已存在、可定向取得的原資料（代理可直接續做，不需裁決）

| 項 | 位置 | 狀態 |
|---|---|---|
| 281 Unit 的 original mapping | 各 Unit JSON 的 3 個 ref | **已完成 488/488 全等** |
| 112 DOC_BRIDGE 文件 | K 內同名檔＋SHA 相符 | 已證 |
| CHILD／PROTECTED 22 案 | 藍圖 `9d6c7a5e…` L4340–4355 等 | 已證 |

## 2｜原義明確、待工程實作（不需裁決，需工時）

| 項 | 缺什麼 | 下一步 |
|---|---|---|
| B2 18 HARD `source_row=null` | 原 carrier 無列號欄 | 由 B5 真使用場景驅動；不得補造 |
| B2 9 HARD non-loss NEG | inner 原功能錯碼對映 outer `TOOL_REQUIREDNESS_HOLD` | 需 R17 具權映射（見第 4 類） |
| B3 COMMIT | Writer／OutputRoot／preimage／Undo 條件 | 已可建 DEV；執行需 effect class 提升 |
| B3 44 PASS_REFUSAL | 目前依「atom 不在 ToolReadSet」 | 需原 NEG mutation 才升真反證 |

## 3｜原規格未完整、待自主設計補編（代理可編，需具權採納）

| 項 | 差額 | 建議 |
|---|---|---|
| DOC_BRIDGE heading 計數 | payload 只給 `headings=N`，未定義計數規則 | 提出最小計數契約（`^#+ ` 行數）並具權採納；12 案現為 HOLD |
| BEHAVIOR_ROUTE 73 Unit | payload 無 source 釘 | 以 §04.OPS 建 behaviour fixture 契約 |
| B3 ROUTE_OUT／HOLD 欄位 | 後波欄位未 typed | 最小 typed contract |

## 4｜真正需要 OWNER／第三方權利或不可替代外部事實

| 項 | 需要的裁決者 | 缺什麼 |
|---|---|---|
| D-2 | FDA Source Owner | `tests/test_fda_{lease,router,router_integration,security}.py` 精確讀權（不在 16 檔 allow-list） |
| D-3 | FDA／XQ／R13 Reader | 7 槽 slot→action→artefact 的 M:N、typed schema、fixture |
| D-4 | 五 Kernel Domain Owner | 有效 baseline、protected field、inner/outer FirstFail |
| TT-UP-1／6 E00／54 ROUTE | R17／E02／E05 | inner→outer 映射、typed `DesignSelection`、protected path |
| B3 60 案 | 原 PIPD-LS-PKG 文件持有人 | `PIPD-LS-PKG_DOC-*` 九份文件不在 K，需具權來源 |
| B3 COMMIT 執行 | Owner | 需 `LOCAL_DRAFT_WRITE` effect class＋原 Writer 指派（現窗 `READ_ONLY_PROBE`） |

## 5｜適合由 B3～B6 真 Consumer 驅動的原責任回補

| 觸發 | 回補對象 |
|---|---|
| B4 真 Brownfield／FDA／Kernel 使用 | B1 剩餘 BASE PARTIAL（012–016）、D-1 三 locator |
| B5 真 HARD／E00／ROUTE／META | B2 76 HOLD、18 `source_row=null` |
| B6 真 Edge／Port | 20 Edge／8 Port／63 欄的 physical chain |

## 6｜結論

「全部缺件等 OWNER 提供原資料」的說法**不成立**：第 1 類已自行完成、第 2／3 類是工程工時與設計補編、第 5 類由下游真使用驅動；只有第 4 類 6 項需要原權位。B1／B2 狀態維持 PARTIAL／PARK_UNTIL_DELTA，B3 為 SOURCE_BOUND 級（非 B3_ACCEPTED）。

## 發布｜remote readback（工程成果，非產品接受）

- Repo：`https://github.com/shw097-team/SQS-THC_MVP`，branch `main`
- commit：`acad969e80d37ac4299a81a0bd068925c1020d92`（remote `ls-remote` 回讀與本機 `rev-parse HEAD` 全等）
- 發布範圍：`70_W0_B1B8_20261126/r5/` 下 168 檔（引擎、TQAEP/OPS 收據、凍結 manifest、CLOSEOUT/HANDOFF、裁決清單）
- **未發布**：`40_OPS/b0_r5_sourcereadset.json`（含原條文逐字），依 `LOCAL_ONLY` 留本地，remote 只記其 sha256（見 `40_OPS/LOCAL_ONLY_EXCLUSIONS.json`）
- 憑證：以受管 `extraheader` 一次性注入，未寫入 git config、未出現在 argv/URL/log/commit
- 發布 ≠ 接受：`B1_ACCEPTED`／`B2_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` 仍未成立，`FIN_ORDER=DENY`
- 更新時間：2026-11-27T00:55:19+0800
