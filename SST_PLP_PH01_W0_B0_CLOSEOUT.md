# SST_PLP_PH01_W0_B0_CLOSEOUT

- subject `SST/SQS-THC/PH01/E00`｜OriginalWave `P1-W00M`｜BID `0`
- 交付時間 2026-11-25（Asia/Taipei）｜Commander：HERMES v0.23.3（opencode-go/deepseek-v4.1-flash）｜Maker（EXECUTE 車道）：Codex CLI 0.169.0-alpha.11.1（同模型）｜Checker：VERIFY_SECURITY 車道分離 session（同模型）
- 產品效果 `SOURCE_READ`｜`write_set=[]`｜`preimage=N/A`｜`FIN_ORDER=DENY`
- 本檔只陳述**已實測**結果；未測者標 `NOT_EXECUTED`／`NOT_VERIFIED`／`HOLD`。

## 1｜規格、採納與候選身份

| 項 | 實際值 |
|---|---|
| 唯一規格根 S | `C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8\SST_PLP_PH01_W0_B0_執行控制小包\B0_NATIVE_FIRST_2026-11-25_r4_CODEX_FINAL` |
| 施工正文 | 99,791 bytes，raw SHA256 `582a54048d8b63e37be3d803c829a12ffe164be72963f026cea1a1b6183345d9` |
| 六件配套 | 依 `00_唯一交付入口_2026-11-25_r4.md` §02 逐件實測，六件 raw SHA 全符（`4bff0829…`／`5de45ee2…`／`f7f0219c…`／`7dfadccb…`／`1daca528…`） |
| 版本關係 | r4 取代 r3 候選與 r2 明列舊載體；r3／r2 原 bytes 保留 LastGood，未改 |
| 工程寫入根 W | `C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace`；**無 `.git`**，local HEAD=`NONE`、dirty=`N/A`，以逐檔 raw SHA preimage 代替 |
| 候選 freeze | `40_OPS/candidate_freeze.json`：**25 檔**，manifest 2,570 bytes，`candidate_digest=5ec38e9c1835dba89c5755acd2f2c720aadd9193dd96d08d0a1fe7ddfa36c456`；Commander 以 `40_OPS/freeze_candidate.py` 獨立重算，與產品 envelope 內 `candidate_digest` **逐字相同** |
| DEV-0 基線 | `40_OPS/dev0_baseline_20261125.json`（83 檔、tree digest `0bc2cdead7b8…`、寫權實測 OK、Python 3.14.9） |
| WriteSet | `20_DEV/WORKORDER_B0_DEV_r4_2026-11-25.md` §1（既有 13 檔 preimage 全列）＋§1.2 新增檔＋§1.4 受影變更（含 host ACL 收緊記錄） |

## 2｜重用、修補與退出載體（只列真缺陷）

**重用**：W 既有 `b0_reader` 7 模組與 5 個測試檔、`00_PREFLIGHT` 歷史 pin；r4 前 59 tests／22 checker 只作 LastGood，**不作本輪 PASS**。

| # | 缺陷（證據來源） | 修法 |
|---|---|---|
| 1 | 舊 CLI 由 caller 自授權（`--allowed-root/--source/--required-field`），v1 wire | 改 `read --request-json -`（`B0ReadRequest/2`）＋固定部署 descriptor；v2 `SST.B0.SourceReadSet/2` |
| 2 | `errors.py` 只有舊碼、無 `source_id/op/attempt/resume` | 重寫為 §02.E typed error（12 欄），`RIGHTS_DENIED` 不 retryable |
| 3 | 無同 handle／TOCTOU 防護（`realpath` + `open(path)`） | 新增 `winio.py`：`CreateFileW`（只分享讀）、`GetFinalPathNameByHandleW`、volume serial＋file index、`FileAttributeTagInfo`、同 handle `ReadFile`、讀後身份複核 |
| 4 | handle 缺失仍以路徑重開（破壞同 handle 保證） | 改回 `PATH_IDENTITY_UNVERIFIED`（Wave2 自測發現） |
| 5 | `ctypes HANDLE(-1)` 未辨識為 `INVALID_HANDLE_VALUE` | 以 sentinel 比對並保留 `GetLastError`（Wave2 自測） |
| 6 | `requiredset.py` 把 `FORMAT_UNSUPPORTED`／`CLAUSE_RULE_MISMATCH` 併吞 | 分離到契約階段回正確碼（Wave2 自測） |
| 7 | CLI 把 `read_sources` 每個 exit-64 都印成 `TRUST_CONTEXT_UNBOUND` | 回傳 typed code（Commander 真來源實測） |
| 8 | `write_set` 非空／effect 錯回 `INVOCATION_INVALID` | `EFFECT_DENIED`（exit 64、讀前拒） |
| 9 | request pin／span 錯無專屬碼 | `SOURCE_PIN_MISMATCH`（exit 2 per-source）、`SPAN_INVALID`（exit 2） |
| 10 | 未知 `source_id` 無專屬碼 | `SCOPE_MISMATCH`（exit 64） |
| 11 | **P0**：`native_entry` 匯出 `_mint_test_context`／`_mint_isolated_context`，caller 可自造 `TrustedContext` | mint 全數移出 `b0_reader` 至 `tests/trust_fixture.py`；每個 context 由 import 期 process-private 隨機鍵做 HMAC seal，`_verify_context`／`revalidate_trusted_context` 驗 seal 且 fail closed；只有 `resolve_context_for_current_principal()` 能產生可通過的 context（Checker 第一輪 FAIL → 已修） |
| 12 | **P0**：撤權檔 hash 改變但 `state` 非 CLOSED/REVOKED/EXPIRED 時放行 | 缺失／讀取失敗／hash 改變／state 未知／格式不明一律 `RIGHTS_UNVERIFIED`；只有 pin 相符或 `state=OPEN` 且 scope／到期皆有效才放行（Checker 第一輪 FAIL → 已修） |
| 13 | **P1**：`icacls` 結果被丟棄，未核 DACL writer 集合 | `_read_acl` 指標化；解析真實 DACL（含逗號權限如 `(S,RD,X,RA)`、`Mandatory Label`、`(OI)(NP)(IO)(NW)`），信任錨（descriptor＋直屬父目錄）對 Everyone／Users／Authenticated Users／ANONYMOUS 的寫入權 fail closed；祖先仍做 reparse／identity（Checker 第一輪 FAIL → 已修） |
| 14 | 中文 Windows 下 `icacls` 摘要行非英文 → 每個路徑 `PATH_IDENTITY_UNVERIFIED` | 摘要行改為 locale 無關（最後一行非 ACE 即摘要）（Commander 實測發現） |
| 15 | `C:\` 根的 ACE（逗號權限、完整性標籤）解析失敗 → 所有讀取失敗 | 逐 token 分類、略過 integrity label、未知 token fail closed（Commander 實測） |
| 16 | sealed 規則套到磁碟根每個祖先（Windows 必然失敗） | 只套 descriptor 與其直屬父目錄（信任錨）；其餘祖先維持 reparse／identity |
| 17 | `_owner_window_is_valid` 要求 Owner 視窗鍵集合**全等**，真實視窗多寫 workspace／fingerprint → 永遠無效 | 改「必填鍵 ⊆ 實際鍵」（與 `owner_window.py` 實際輸出對齊） |
| 18 | 產品 `_CANDIDATE_RELATIVE_PATHS` 未含新增 `tests/trust_fixture.py` → product／Commander digest 不一致 | 補入清單，兩邊重算後一致（`1257f5ee…`） |

**退出／不採用的非必要載體**：v1 wire、舊 CLI 授權旗標、`OperationType`／EffectRegistry／通用 Reader／Runner／ACK／RawSchema Registry 作 B0 前置（D01–D03 受界採納）；`BR.B0.KEY` 持久 idempotency ledger。**未宣稱**退出全部七 HardRoot 或改寫 W0M／PH01 其他批次。

**Host 動作（具名、可回查）**：`W/00_PREFLIGHT` 目錄原本繼承 `NT AUTHORITY\Authenticated Users:(I)(M)`（自 `C:\Projects`），依 §04.N1.4 不能宣稱信任錨隔離。已對**本批自有**該目錄 `/inheritance:r /grant:r` 只授 `DESKTOP-57EO414\user`、`SYSTEM`、`Administrators`，並 `icacls <dir>\* /reset`；K 知識庫、原 repo、他人檔案 ACL 一律未動。收緊前後 `icacls` 原文可回查（Workorder §1.4 第 3 項）。

## 3｜真產品 OPS（Native Direct、真合法來源、最終候選）

執行身份 `DESKTOP-57EO414\user`；受權引用＝Owner 本人於原視窗簽發 `WIN-2ffca679906c`（ed25519、ceiling `READ_ONLY_PROBE`、`2026-11-25T12:11:29→20:11:29 +08:00`），收據 SHA `e750066a430da8a7c479efa9687d5aa2377964dbab51fdd20e144c6303edd28a`。口令未經代理、未落 W。

| 執行 | request_digest | exit | stdout | stderr | 無寫 |
|---|---|---|---|---|---|
| **POS**（兩個真來源、真 span） | `0d681d2a47dbccd0…` | **0** | 5,429 B | 空 | `NO_PRODUCT_WRITE_OBSERVED` |
| NEG pin（只改一來源 `expected_sha`） | `9fa386d5cad57377…` | 2 | 3,383 B（另一來源照常成 entry） | `SOURCE_PIN_MISMATCH` | 同上 |
| NEG span（**只改第二來源** span，單變異） | `0ae780e4509fb5a5…` | 2 | 3,247 B | `SPAN_INVALID` | 同上 |
| NEG effect（`write_set` 非空） | `dfe3b4105b49c3cd…` | 64 | 0 B | `EFFECT_DENIED` | 同上 |
| NEG scope（加入未授權 `source_id`） | `779c4aa4b1dd07ed…` | 64 | 0 B | `SCOPE_MISMATCH` | 同上 |

證據：`40_OPS/ops_r4_g_{pos,neg_pin,neg_span,neg_effect,neg_scope}.json` 與 `.raw/stdout.txt`／`.raw/stderr.txt`；請求檔 `40_OPS/b0_read_request_2026-11-25.json`、`b0_read_neg_{pin,span_single,effect,scope}_2026-11-25.json`；錄製器 `40_OPS/run_ops_r4.py`（argv／cwd／python／exit／raw ＋ W 樹 size+mtime+**內容 sha256** 與 K 來源根 before/after）。

**Commander 獨立重算**

| 檢查 | 結果 |
|---|---|
| 來源 raw SHA | `dd37a40b112bf5aa…`（457,294 B）、`5670990d8f0faa57…`（311,983 B）與原件重算相符 |
| clause SHA | `77132f0636e30b0c…`（ALL L572–579）、`4f0db2cb1d7c…`（W0M L295–307）與原件切片相符 |
| observed | `read="READ 只讀合法來源，不能繼承 DEV 效應。"`、`value_sha=78a231eaa93d64fe…`、`span=[573,573]`／`[299,299]` |
| R/P/M | `R=["read"]`、`P=["read"]`、`M=[]` |
| authority | 14 欄齊；`LIVE_REVALIDATE`、`expires_at=20:11:29+08:00`（＝視窗到期）、`disclosure=LOCAL_ONLY`、`os_principal=DESKTOP-57EO414\user` |
| 產品寫入 | `write_set=[]`、`fin_order=DENY`；W 內容 hash 與 K 根前後全等，無 `__pycache__`／暫存／ledger |

**分帳**：上表四個 NEG 為**正確拒絕**；第 7–18 項為**真缺陷**，已修並以測試釘住；修補後重跑五個執行皆如上表。

## 4｜工程測試

`cd W/20_DEV; unset TMPDIR; PYTHONDONTWRITEBYTECODE=1; TEMP=TMP=<W>/20_DEV/.tmp_tests; python -B -m unittest discover -s tests`

**實測：Ran 132 tests — OK（0 fail / 0 error / 0 skip）**，耗時 290 s（含真 junction、share 競態、契約探針）。

| 模組 | 案數 | 對應 |
|---|---|---|
| `test_b0_root.py` | 9 | §04.ROOT／路徑語法／祖先 |
| `test_b0_bytes.py` | 11 | §04.BYTES／raw SHA／CRLF・CR・LF／BOM／span |
| `test_b0_fields.py` | 7 | §04.FIELDS／R・P・M／規則 |
| `test_b0_return.py` | 13 | §04.RETURN／v2 組裝／CLI typed code |
| `test_b0_cases.py` | 24 | §06.1 原 14 主案＋§06.2 8 補充群 |
| `test_product_read.py` | 34 | N01／N03／N04／N05／N06 產品面／N07 |
| `test_windows_security.py` | 15 | N02／N07（真 `mklink /J` junction、share 模式、handle 身份、改名競態） |
| `test_contract_probe.py` | 13 | N06 獨立 v2 validator（不 import Maker serializer） |
| `test_native_off.py` | 6 | N08（import 閉包、縮減環境冷啟、pin 漂移、偽造 env/cwd/flags、固定 trust 入口、child-process 面） |

## 5｜獨立驗收（同候選、分離 session）

### 5.1 第一輪（freeze `7a4711ad…`）— 18 findings：8 PASS／3 FAIL／5 NOT_VERIFIED／2 HOLD

逐條原文：`30_VERIFY/findings_r4.json`；收據 `30_VERIFY/verify_r4_receipt.json`。Checkers 自行由原件重算 digest、span、value_sha，讀實際 raw 與 stderr，並主動否證兩項 P0（caller mint、撤權 fail-open）與一項 P1（ACL 未核）。HOLD：SPAN 負例非單變異（已重造）、Workorder pin 文字衝突（已改單一定義）。NOT_VERIFIED：撤權證據不可獨立讀取、無寫證據不足、Native OFF、同候選獨立驗收、獨立 probe 未執行。

### 5.2 第二輪（freeze `1257f5ee…`）— **派工兩次，發布時尚無判定**

| 嘗試 | 時間 | 結果 |
|---|---|---|
| 第一次 | 15:36 派工，15:59 由 Commander 主動終止（關機指令） | 無回覆、無收據 |
| 第二次 | 17:55 重派（含「跑 132 案全套」指示） | **50 分後 lane timeout**：`ERR_LANE_ALL_ROUTES_EXHAUSTED`、`timed_out_arms=[opencode-go/deepseek-v4.1-flash]`、`ok=false`；期間 relay usage 持續 200、0 次 policy 阻擋 → 屬長回合超時，非拒絕 |
| 第三次 | 19:00 窄版重派（限 12 分／25 次工具呼叫，**不跑測試**，只核 5 項） | 收據 `30_VERIFY/verify_r4_round2b_receipt.json`；結果見下 |

（第三次回覆後補入逐條 verdict。若第三次仍未回覆，則本節即為「三次均未取得獨立判定」的如實紀錄，`B0_CORE_ACCEPTED` 維持不成立。）

因此：**第二輪獨立判定仍未取得**，`B0_CORE_ACCEPTED` 照實不成立。第一輪三項 FAIL（`SEC-CALLER-MINT`／`SEC-REVOCATION-FAIL-OPEN`／`ROOT-ACL-CONTENT-UNCHECKED`）的修補是**我方自述＋132 案測試釘住**，不是獨立判定。

- 第二輪一旦回覆：把逐條 verdict 貼入本節、同步 §6，並以獨立 commit 更新本檔與 `30_VERIFY/`。
- 重跑指令見 `SST_PLP_PH01_W0_B0_RESUME_2026-11-25.md` §3-⑤。

## 6｜狀態、缺件與恢復

| 狀態 | 本輪實際 |
|---|---|
| `DOCUMENT_SELF_CHECKED / ACTIVE` | 成立（r4 文檔自驗，非產品驗收） |
| `B0_SPEC_READY` | 成立 |
| `B0_ENGINEERING_CANDIDATE` | **成立**（真寫權、preimage、diff、同候選 freeze、132 tests OK） |
| `B0_PRODUCT_EXECUTED` | **成立**（真來源四 Op＋四個單變異真 NEG、raw／exit／無寫齊） |
| `B0_CORE_ACCEPTED` | **不成立**（Native OFF 的 network／transitive tracing 為 `NOT_VERIFIED`；同候選獨立驗收待第二輪判定） |
| `B0_COMPLETE` | **不成立**（無真 B1/B2/B3 接收） |
| `B1_CONTRACT_COMPATIBLE / CONSUMER_NOT_YET_EXECUTED` | 成立（僅獨立探針） |
| `B1_INPUT_READY`／`B1_READY_EXECUTE` | 不成立 |

**未閉合項（含責任與恢復條件）**

| # | 項 | 受影 | 責任 | 恢復條件 |
|---|---|---|---|---|
| H1 | Native OFF 缺 network／transitive child-process tracing | N08、`B0_CORE_ACCEPTED` | 工程（受權工具） | 提供可用的進程／連線觀測（ETW／ProcMon 級），同候選冷啟重跑；不得以「沒看到」代替 |
| H2 | 無真 B1/B2/B3 Consumer | 正式交接、`B0_COMPLETE` | B1/B2/B3 Owner | 有真 Consumer 後以同 freeze／pin／當前權利接收並 readback |
| H3 | 無 provider-versioned epoch 服務 | `EPOCH_STALE` 真路徑 | Source/Data Owner | 提供真版本化 epoch；現行一律 `LIVE_REVALIDATE` |
| H4 | 繼承 SourceManifest 原件未取得 | `source_manifest=UNVERIFIED` | 原持有人 | 提供 `2012a28f…` 同 bytes 原件與法位 |
| H5 | P0-W00M 當期來源／權利成果未定位 | 其他正式來源接受 | Source/Data Owner | 提供當期 source／scope／用途／撤權／時效證據 |
| H6 | Owner 視窗到期（`2026-11-25T20:11:29+08:00`） | 之後任何真讀 | Owner 本人 | 於原視窗重開；只換 descriptor 的 `authorization_sha`／有效期並重 freeze |
| H7 | 每次派工 `WARN_LANE_CREDENTIAL_POSTURE_INCONCLUSIVE`（posture gate 檔缺） | 車道偵測面（非產品） | 車道 Owner（FHS/HGK） | 補 `scripts/gcm-containment/lane_credential_posture.py` 或明示接受 |
| H8 | 三車道同模型（owner order） | model-axis SoD | Owner | 依原裁決維持；served 已證、lane ADMITTED 未獨立證明 |

**停止／重試紀錄**：無 `PARK_UNTIL_DELTA`；每 finding 修補次數 ≤2（F1–F4 一次；R1–R3 一次；測試遷移一次）；一次 lane timeout（`ERR_LANE_ALL_ROUTES_EXHAUSTED`，因 writer 反覆嘗試被 policy 阻擋的 PowerShell，已改以 python／icacls 直接呼叫後恢復）；無盲重試；`RIGHTS_DENIED` 類不入 retry 集合。

**LastGood**：`40_OPS/dev0_baseline_20261125.json` 的 83 檔基線與公開倉 `shw097-team/SQS-THC_MVP@c502db00e16a`（前輪工程候選）。本輪未覆寫任何歷史證據。

## 7｜公開交付（增量上推，2026-11-25 18:41 +08:00）

| 項 | 實際 |
|---|---|
| repo | `https://github.com/shw097-team/SQS-THC_MVP`（既有公開庫，增量更新，未改 visibility、未 force） |
| 前後 commit | `c502db00e16a6d47187de56c6c967bccfbaf540e` → **`a24aef29dabf7d15cf02c2c0e6f19c3bf8c8cfc1`**（`c502db0..a24aef2 HEAD -> main`） |
| 變更 | 55 個檔案（35 新增＋15 修改＋其餘）；tree 82 entries／71 blobs（`git/trees/main?recursive=1` 實查） |
| 推送方式 | `git push` 以 `http.extraheader` 注入權杖（只在子進程 env；未入 argv、remote URL、log 或檔案）；`git ls-remote` 先行驗證 exit 0 |
| staging | `W/dist/SQS-THC_MVP`（隔離工作樹，以 `origin/main` 為基線）；`W` 本身無 `.git` |
| 讀回 | remote `main` SHA 與 local HEAD **逐字相同**；`CLOSEOUT.md`／`README.md`／`20_DEV/tests/trust_fixture.py` 的 raw 下載 sha256 與本地**完全相同**；`HANDOFF.md`／`native_entry.py`／`candidate_freeze.json` 僅 CRLF↔LF 差異（正規化後 byte 相同） |
| secrets／PII／散布檢查 | 62 個變更檔以 8 條樣式（ghp_/github_pat_/sk-/oc_sk_/AKIA/PRIVATE KEY/Bearer/passphrase 指派）掃描 **0 命中**；未含口令信封、權杖、Owner 私鑰、知識庫正文、lane 派工收據／logs、`30_VERIFY/b0_checkpoint*` |
| 公開版本邊界 | 只放工程候選、真跑 raw（含 1 行規格引用字串）、findings 與兩份 MD；`authorization_ref` 等以本地 locator＋SHA 表示 |

**這不是金融 Release、不是產品驗收、不是 R18 發布**；`FIN_ORDER=DENY` 不變。

**第三次（窄版）實際回覆（19:20，`ok=true`、served arm 正確、`usage_receipt_ok=true`）**

| 受檢項 | Checker 判定 | 內容 |
|---|---|---|
| freeze 重算 | `NOT_VERIFIED` | 沙箱阻擋指定 python 與 3 份 `00_PREFLIGHT` 檔；PowerShell 可讀的 22/25 檔 SHA256＋bytes **全相符** |
| caller mint／seal | `PASS` | `_mint*` 已不存在；sealer 未匯出；`_verify_context` 以 HMAC 比對，caller 自造 context 無法通過 |
| 撤權 fail-closed | **`FAIL`** | 缺固定撤權 pin：hash 改變後若內容仍是有效 `OPEN` 視窗，`_owner_window_is_valid` 會回 True → 可繞過 |
| ACL 解析／sealed | `PASS` | `icacls` 真解析；broad write 在 descriptor 與直屬父目錄 fail closed；祖先不套 sealed 為刻意設計 |
| POS／四個 NEG | `PASS` | POS exit 0、5,429 B、stderr 空；`SOURCE_PIN_MISMATCH`(2)／`SPAN_INVALID`(2)／`EFFECT_DENIED`(64)／`SCOPE_MISMATCH`(64)；`dd37a40b…`／`77132f06…`／`5670990d…`／`4f0db2cb…` 全符，raw stdout SHA `4004f208…` |

CORE_ACCEPTED 五條件（Checker 原話）：真核心產品實跑＝成立；安全負例＝**不成立**；Native OFF＝不成立；同候選獨立驗收＝不成立；獨立契約探針＝成立。

**對該 FAIL 的處置（同日 19:47）**：`_owner_window_is_valid` 增加 `max_expiry` 上限，改由 **descriptor 自身 `expires_at`** 綁定——任何自稱更晚到期的視窗一律拒（攻擊面：換一份有效期更長的視窗來延長權利）。改後重跑：**132 tests OK（279 s）**、POS 與四個 NEG 全部重跑（`40_OPS/ops_r4_h_*`）、新 `candidate_digest=5ec38e9c1835dba89c5755acd2f2c720aadd9193dd96d08d0a1fe7ddfa36c456`（25 檔，產品與 Commander 重算一致）。此為**我方修補，尚無獨立複核**，故安全負例仍記不成立。
