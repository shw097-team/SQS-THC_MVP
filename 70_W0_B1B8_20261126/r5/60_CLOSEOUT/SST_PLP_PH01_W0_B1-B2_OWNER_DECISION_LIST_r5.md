# W0 B1–B2｜最小 Owner／原權位裁決清單（r5，未裁決即 HOLD）

產生時間：2026-11-26T23:29:11+0800
依據：薄 PROMPT DONE §122「一次提交最小 Owner 裁決清單」；本文件不是 Grant、不是接受。

## 0｜現況（真跑計數，非報告抄寫）

| 批 | PASS | 其他 | 合計 |
|---|---:|---|---:|
| B1 | 32 | FIXTURE_ONLY 12、HOLD 6、PARTIAL 5、PASS_EVIDENCE 5 | 60 |
| B2 | 2,854 | HOLD 76 | 2,930 |
| B3 | 22 PASS_SOURCE_BOUND＋44 PASS_REFUSAL | NOT_EXECUTED 686 | 752 |

B0 產品：`SST.B0.SourceReadSet/2` exit 0，1 entry，errors 0（`40_OPS/b0_r5_sourcereadset.json`，sha `bdb2a03f…`）。
B3 JOIN：1,369 ready／96 held；draft v2 `f08ec189…`（315,375 B）。

## 1｜需要裁決的最小項目

| ID | 精確 scope | 需要的裁決者 | 需要的東西（缺此即 HOLD） | Resume 條件 |
|---|---|---|---|---|
| D-1 | BASE-009 ×2、BASE-017 | Repo／Source Owner | 逐 target 批准 resolved namespace／root／path／commit／blob／raw／用途／接收權；真 tracked 驗證 | 三者由 `CANDIDATE_NOT_RATIFIED` 升為已採納後重跑受影 3 Unit |
| D-2 | BASE-018 之 `tests/test_fda_{lease,router,router_integration,security}.py` | FDA Source Owner／原 Reader | 四檔精確讀權（現行 16 檔 allow-list 不含） | 補權後重判 BASE-018；不得以 waiver 取代 |
| D-3 | 7 個 FDA slot | FDA／XQ／R13 原 Reader | 每槽原始 slot→action→artefact M:N、typed schema、fixture、Reader、scope、build | 現況 7/7 CARRIER_LEVEL_ONLY、hit_count 0 |
| D-4 | 5 個 KERNEL NEG | 五 Kernel Domain Owner／Reader | 有效 baseline、受保護欄位／path／old-new、原 predicate、inner/outer FirstFail、當期或後波決定 | 現況僅 raw SHA＋span 相符，無語義 Oracle |
| D-5 | B2 carrier 父源 | B2 Source Owner／原 Q carrier Reader | `463dcf33…` 之表頭、原欄序、各 namespace／kind 規則之採納 | 現已用 carrier 宣告欄位作 `labelled-only` requiredness |
| TT-UP-1 | 9 個 HARD non-loss NEG | R17／OriginalConsumer | inner 原功能錯碼 ↔ outer `TOOL_REQUIREDNESS_HOLD` 的具權映射 | 現 9/9 只到 outer |
| E00 | 6 個缺 Oracle 的 E00_TECH | E02／E05／PIPD 原權威 | 原 typed `DesignSelection` 與合法 enable 條件 | 現 2/8 有真證據 |
| ROUTE | 54 個 TECH_ROUTE | R17／route Reader | protected path、原值、單變異、拒錯 | 現僅 `interpreted` |
| B3-READER | 686 案 | B3 原 Reader | `DOC_BRIDGE/CH…` 等 kind 的原 Reader 與 ExpectedSet | 現無原 Reader，不用 payload 自比 |
| B0-PIN | reader pin delta | 分離驗證者（非 Owner 權） | 對 `native_entry.py` 三常數變更之獨立重算 | 已在送驗中 |

## 2｜我已自行解決、不需裁決的

- B0 三層閘門（視窗 scope 精確順序、descriptor 續期、per-source `usage_evidence_sha`、sealed ACL、pin 切換）
- B3 locator 漂移（`PHASE 00~04` → `PHASE 01~04`，同 SHA `9d6c7a5e…`）——記為 `CANDIDATE_NOT_RATIFIED`，未改原宣告
- 18 HARD 的 metadata：2 條取得官方 metadata（pydantic 2.14.4 MIT、jsonschema 4.26.0 MIT，PyPI JSON＋回應 SHA 已釘），7 條 pin UNBOUND、9 條非發行物；依原契約交接，未編造

## 3｜M-01 受界處置

見 `40_OPS/m01_boundary_grep_receipt.json`：事件已記錄、非授權所得已隔離、FDA 證據僅由 16 檔 allow-list 依 SHA 重建（16/16 相符）、事件後未再執行廣域 grep。不追認、不擴權。

## 發布｜remote readback（工程成果，非產品接受）

- Repo：`https://github.com/shw097-team/SQS-THC_MVP`，branch `main`
- commit：`8d49a7858f58247f3ab725fb4c33f8628bd51afe`（remote `ls-remote` 回讀與本機 `rev-parse HEAD` 全等）
- 發布範圍：`70_W0_B1B8_20261126/r5/` 下 168 檔（引擎、TQAEP/OPS 收據、凍結 manifest、CLOSEOUT/HANDOFF、裁決清單）
- **未發布**：`40_OPS/b0_r5_sourcereadset.json`（含原條文逐字），依 `LOCAL_ONLY` 留本地，remote 只記其 sha256（見 `40_OPS/LOCAL_ONLY_EXCLUSIONS.json`）
- 憑證：以受管 `extraheader` 一次性注入，未寫入 git config、未出現在 argv/URL/log/commit
- 發布 ≠ 接受：`B1_ACCEPTED`／`B2_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` 仍未成立，`FIN_ORDER=DENY`
- 更新時間：2026-11-26T23:59:29+0800
