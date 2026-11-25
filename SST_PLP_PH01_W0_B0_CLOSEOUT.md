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
| `B0_CORE_ACCEPTED` | **不成立**（候選已更新為 8d4248a7…，OPS 待重跑）（Native OFF 的 network／transitive tracing 為 `NOT_VERIFIED`；同候選獨立驗收待第二輪判定） |
| `B0_COMPLETE` | **不成立**（無真 B1/B2/B3 接收） |
| `B1_CONTRACT_COMPATIBLE / CONSUMER_NOT_YET_EXECUTED` | 探針成立；**已由真接收取代**（見 §8.1） |
| `B1_INPUT_READY` | **成立**（B1 真接收 ACCEPTED、readback 見 §8.1） |
| `B1_TECHNICALLY_READY`（非 canonical） | 不成立（B1 自身 RepoRoot／BASE／五 Kernel／FDA 未取證） |
| `B1_READY_EXECUTE` | 不成立 |

**未閉合項（含責任與恢復條件）**

| # | 項 | 受影 | 責任 | 恢復條件 |
|---|---|---|---|---|
| H1 | Native OFF **已補**：子進程 0、外部 TCP 0、穩定投影相同（§8.2）；仍缺 transitive import 與 kernel 級寫入證據 | N08、`B0_CORE_ACCEPTED` | 工程（受權工具） | 需 ETW／ProcMon 級 trace 才能把 `NOT_VERIFIED` 轉 PASS |
| H2 | B1/B2/B3 最小真實接收**已成立**（§8.1）；仍缺 B1 自身技術前置與正式效果授權 | `B0_COMPLETE`、`B1_READY_EXECUTE` | B1 Owner | 取 B1 RepoRoot／BASE／Kernel／FDA 實證後再評 |
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

## 8｜本輪差額補強（2026-11-25 19:52–20:05）

### 8.1 B1／B2／B3 最小真實 v2 接收（新增，非探針）

- 入口：`60_B1/b1_consumer`（`python -B -m b1_consumer.cli receive --envelope <file|-> --context <ctx> --out <receipt>`），**不 import B0 maker 的 serializer**，型別／集合／錯誤規則依 r4 §02.F／§03.2 自行重寫。
- 各 Consumer 自己的可信權利入口：`rights_receipt_ref`＋`rights_receipt_sha`（Owner 簽署收據，hash-pinned）＋`rights_state_ref`（live owner window）——要求 `window_id` 相同、`state=OPEN`、且 **window 到期 ≤ 收據到期**；任一不符即 `RIGHTS_UNVERIFIED`／`RIGHTS_REVOKED`／`RIGHTS_EXPIRED`。
- 真接收結果（同一份真 B0 輸出 `snapshot_sha=82640619aa80…`）：

| Consumer | 收據 | verdict | accepted | window |
|---|---|---|---|---|
| B1 | `60_B1/receipts/b1_receipt_r4_2026-11-25.json` | **ACCEPTED** | 2 個 entry（M 皆空） | `WIN-2ffca679906c` |
| B2 | `60_B1/receipts/b2_receipt_r4_2026-11-25.json` | **ACCEPTED** | 2 | 同 |
| B3 | `60_B1/receipts/b3_receipt_r4_2026-11-25.json` | **ACCEPTED** | 2 | 同 |

- 負例：`60_B1/tests/test_b1_consumer.py` **15 案 OK**——錯 wire_version、BOM、重複 source_id、錯 candidate_digest、被改的 entry sha（破壞 observed 出處）、R/P/M 分割破壞、非法 epoch_strategy、consumer 未在 scope、未知 source、收據 hash 變更、window CLOSED、window_id 不同、window 到期超出收據、已到期。
- 邊界：B1 的 **自身技術前置（RepoRoot／BASE／五 Kernel／FDA）未取證**，故 `B1_TECHNICALLY_READY` **不成立**；`B1_INPUT_READY` 成立。

### 8.2 Native OFF 實測（H1 部分閉合）

`40_OPS/native_off_r4.py` → `40_OPS/native_off_r4.json`：

- 環境：只留 15 個 OS 變數，`PATH` 僅解釋器目錄，剝除 `HGK_*`／`FHS_*`／`HERMES_*`／`CODEX_*`／`OPENAI_*`／`OPENCODE*`／`PYTHONPATH`。
- 結果：`exit=0`、5,429 bytes、**穩定投影與正常執行完全相同**（兩個 entry 的 sha／clause／R/P/M 一致）；**子進程 0、外部 TCP 0**；verdict `NATIVE_OFF_OBSERVED_NO_EXTERNAL_DEPENDENCY`。
- 未證（如實）：transitive import 的缺席證明、kernel 級檔案／registry 寫入、取樣窗後的網路活動。`native_off_r4.json.not_proven` 已列。

### 8.3 發布位元組一致性（T3）

問題：`dist` clone `core.autocrlf=true` 使 GitHub blob 為 LF、本地候選為 CRLF，raw bytes 與候選不一致。處置：新增 `.gitattributes`（`* -text`）並 `git add --renormalize`，commit `1563775`；實測 `native_entry.py`／`return_.py`／`root.py`／`CLOSEOUT.md` 的 **HEAD blob 與工作檔 byte-equal**。

## 9｜R1 共用安全閉合（本輪實作，OPS 待重新授權後重跑）

### 9.1 R1.1 撤權／信任邊界（SEC-REVOCATION-FAIL-OPEN）

新增（`20_DEV/b0_reader/native_entry.py`）：

- `_pinned_receipt(context)`：以 descriptor 的 `authorization_ref` 讀入 Owner 簽署收據，並要求其 raw SHA 等於 `authorization_sha`，否則不得使用。
- `_window_matches_receipt(window, receipt)`：live 窗口必須是**收據所指的那一個窗口**——`window_id` 與 `owner_fingerprint` 皆必填且必須相等；收據缺這兩個識別即視為不可核實（fail closed），不再只憑 `state=OPEN`＋到期上限。
- `_revocation_error` 內對 `OwnerSigningWindow@1` 先做上述綁定，再走原有 schema／task／scope／ceiling／到期（≤ descriptor `expires_at`）檢查。

新增單變異負例（`20_DEV/tests/test_product_read.py`，均從有效 baseline 只改一項）：

| 變異 | 期望 |
|---|---|
| live 窗口 `window_id` 換成別的窗口 | `RIGHTS_UNVERIFIED` |
| live 窗口 `owner_fingerprint` 換掉 | `RIGHTS_UNVERIFIED` |
| live 窗口缺 `window_id`／`owner_fingerprint` | `RIGHTS_UNVERIFIED` |
| 收據本身缺窗口識別（無法綁定） | `RIGHTS_UNVERIFIED`（連 resolve 都不成立） |

測試 fixture 同步：`tests/trust_fixture.py` 的收據與 live 窗口現在都帶 `WIN-test-0001` / `test-fingerprint`，因此嚴格路徑在測試中同樣被執行，不是只在正式環境生效。

### 9.2 R1.3 N07 每源 30 秒上限

新增（`20_DEV/b0_reader/return_.py`）：

- `SOURCE_READ_LIMIT_SECONDS = 30.0`、`_read_with_budget(...)`：每個來源的讀取在獨立 daemon 執行緒中進行，超過上限即回該源 `BYTES / UNKNOWN_RECONCILE_REQUIRED`（**不是**靜默截斷），兄弟來源不受影響。
- 被放棄的讀取仍持有其 handle 直到該執行緒結束；結果一律 UNKNOWN，重入前必須 reconcile（r4 §04.R）。
- 負例 `test_N07_source_read_budget_reports_unknown_and_keeps_siblings`：S1 逾時 → error 僅 S1、`entries=[S2]`、exit=2；執行緒結束後來源可再次讀取（handle 已釋放）。

### 9.3 現況與缺口（照實）

- 全套測試：**135 案 OK**（原 132＋本輪 3 案）。
- 新候選 freeze：**`8d4248a7428dc035ee75f4ed7199f75ad3f2fd2e54f2a9e22cd3d79155a9dd19`**（25 檔，manifest 2,570 B）。
- Owner 視窗 `WIN-2ffca679906c` 已於 `2026-11-25T20:11:29+08:00` 到期（`remaining_s=0`、`usable=false`）。因此：
  - 產品 POS／四 NEG 尚未對**新候選**重跑；
  - Native OFF v2（正常 baseline vs 隔離 OFF、觀測器自測、W 樹快照比對）已實作但**未執行**；
  - `B0_CORE_ACCEPTED` **不成立**，直到上述真跑與同候選獨立判定完成。
- 恢復：Owner 以原機制重開視窗（同 task／scope／6h／12 ops）→ 更新 descriptor 的 `authorization_sha`／`expires_at` 與 `native_entry` 的 `EXPECTED_DESCRIPTOR_*` → 重 freeze → 跑 `40_OPS/run_ops_r4.py`（POS＋四 NEG）與 `40_OPS/native_off_r4.py` → 分離 Checker 同候選判定。

## 10｜R1／R2 執行結果（2026-11-25 20:26–20:45，Owner 窗口 WIN-7769f20a712c）

### 10.1 授權與候選

- 新 Owner 窗口：`WIN-7769f20a712c`（Owner 本人於原視窗機制輸入口令；`state=OPEN`、`remaining≈21,451 s`、`ceiling=READ_ONLY_PROBE`、`scope=b0_source_read_authority,sqs_thc_ph01_e00`、`max_ops=12`、`owner_fingerprint=412b351937be72a1`）。收據 raw SHA `8f61f584006fdeea19dbd312b0c3d6f94f89229f7ff0bc6c5c8d811701d6a0ff`（930 B）。
- Descriptor 更新後：`00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json` 3,846 B、`28a7d598…` → 再把每源 `usage_evidence_sha` 綁到新收據後為 **`c57518c457c5c3c9a4bf52f0a5ade422aed624249ff1e79e055e8d52f84f6dea`**（`valid_from 2026-11-25T20:26:58+08:00`、`expires_at 2026-11-26T02:26:58+08:00`）。
- 最終候選 freeze：**`dfc87f1800efb69db9185c67402608990bcba9d731d4a782a70ba8a31fe043c3`**（25 檔、manifest 2,570 B），與真 POS envelope 內的 `candidate_digest` 相符。

### 10.2 真 OPS（同候選、真來源、真權利）

| 例 | exit | stdout | stderr FirstFail | 無產品寫 |
|---|---|---|---|---|
| POS | 0 | 5,429 B（2 entries、`M=[]`、errors=[]） | — | `NO_PRODUCT_WRITE_OBSERVED` |
| NEG pin | 2 | 3,383 B | `SOURCE_PIN_MISMATCH` | 同上 |
| NEG span | 2 | 871 B | `SPAN_INVALID` | 同上 |
| NEG effect | 64 | 0 | `EFFECT_DENIED` | 同上 |
| NEG scope | 64 | 0 | `SCOPE_MISMATCH` | 同上 |

收據：`40_OPS/ops_r4_r1_{pos,neg_pin,neg_span,neg_effect,neg_scope}.json` 與 `.raw/{stdout,stderr}.txt`。無寫比對：W 樹（size＋mtime_ns＋raw SHA256）與 K 來源根在執行前後 digest 相同（`W_tree 43e4ead1…`）。

### 10.3 Native OFF（正常 baseline vs 隔離 OFF，含觀測器自測）

`40_OPS/native_off_r4.py` → `40_OPS/native_off_r4.json`，verdict **`NATIVE_OFF_EQUIVALENT_NO_DEPENDENCY`**：

| 項 | 正常 baseline | 隔離 OFF |
|---|---|---|
| 環境變數 | 158 | 15（剝除 `HGK_/FHS_/HERMES_/CODEX_/OPENAI_/OPENCODE/PYTHONPATH`，PATH 僅解釋器目錄） |
| exit | 0 | 0 |
| 穩定投影 | 2 entries、`M=[]`、`candidate_digest=dfc87f18…` | 完全相同 |
| 子進程 | 121（皆 `icacls` 與 venv redirector 的 `python.exe`） | 95（同種類） |
| 外部 TCP | 0 | 0 |
| W 樹寫入 | clean | clean |

觀測器自測：以本機 listener＋子進程驗證，`sees_child=true`、`sees_tcp=true`（listener 埠被觀測到）、`observation_ok=true`；因此「零觀測」不是觀測器壞掉造成的假陰性。`not_proven` 仍列：transitive import、kernel 級/registry 寫入、取樣窗後網路。

### 10.4 R1.1／R1.3 程式與測試

- R1.1：`native_entry._pinned_receipt`＋`_window_matches_receipt`，live 窗口必須與 pinned 收據的 `window_id`＋`owner_fingerprint` 一致，收據無法綁定即 `RIGHTS_UNVERIFIED`。
- R1.3：`return_.SOURCE_READ_LIMIT_SECONDS = 30.0`、`_read_with_budget`，逾時該源 `UNKNOWN_RECONCILE_REQUIRED`、兄弟續行。
- 新增 3 案（合計 135 案）：窗口 id 不符／fingerprint 不符／窗口缺識別、收據缺識別、S1 逾時而 S2 正常。

### 10.5 狀態

- `B0_ENGINEERING_CANDIDATE`：成立（freeze `dfc87f18…`）。
- `B0_PRODUCT_EXECUTED`：成立（真來源 POS＋四單變異 NEG＋無寫）。
- `B0_CORE_ACCEPTED`：**待獨立判定**（R1 四項的 Checker 收據 `30_VERIFY/verify_r1_receipt.json`；未取得前不得宣稱）。
- `B0_COMPLETE`：不成立（尚需 B2 ToolReadSet／B3 ledger 等當期義務，且不得以核心態代替）。

## 11｜Checker 第一輪（真判定）與 C-R1-01 修補

### 11.1 第一輪 Checker 的實際結果（lane 回報 `ERR_NO_ARM_EMITTED_NONCE`，但審查本身完成）

- 受檢 `dfc87f18…`；Checker 於 final message 給出：**R1.1 PASS**、**R1.2 NOT_VERIFIED**、**R1.3 FAIL（P1, `C-R1-01`）**、**R2 NOT_VERIFIED**、`independent_acceptance=REJECTED`。
- `C-R1-01`：逾時後無隔離狀態，允許對同一來源再次進入（違反 N07「未 reconcile 不重入」），且原測試等到被放棄的讀取結束才斷言，沒有測到重入。
- R1.2 疑點：TCP 歸屬略過未關聯 socket、部分子進程存取錯誤被跳過、允許清單偏寬、監看根未含 TEMP／cache／registry。
- R2 疑點：3 個 `00_PREFLIGHT` 檔 `EPERM`——Checker 以 `DESKTOP-57EO414\CodexSandboxUsers` 身分執行，而該身分在 `00_PREFLIGHT`（`/inheritance:r`）沒有任何 ACE，故只能核 22/25。
- 原始 stdout（865 KB）保留於 `30_VERIFY/verify_r1_dispatch.json.logs/`；非秘密內容，未含口令。

### 11.2 修補

1. **C-R1-01（P1）**：`return_._QUARANTINE`＋`quarantine_state()`＋`reconcile_source(source_id)`。逾時即隔離；隔離期間**在呼叫 reader 之前**就回 `UNKNOWN_RECONCILE_REQUIRED` 並附 resume 指示；只有 reconcile 後才能再讀。新測試 `test_N07_timed_out_source_is_quarantined_until_reconciled` 以呼叫計數證明「第二次沒有再進 reader」，並驗 reconcile 後可恢復。
   - 已知限制（照實）：隔離狀態是**進程內**的；CLI 每次執行都是新進程，跨進程重入仍以新進程重新驗權利／pin，屬重新開始而非繞過。
2. **R2 可讀性**：對 `CodexSandboxUsers` 授與 `00_PREFLIGHT` 的 `(OI)(CI)(RX)` 與檔層 `(R)`；**未給寫入**，`root.py` 的 sealed 檢查（broad principal 不得有寫入權）仍成立，POS 重跑 `exit 0`。
3. **R1.2 疑點**：本輪未改動觀測器語義，僅如實保留 `not_proven` 與 `foreign_children_baseline`／`foreign_children` 分欄；是否足以構成缺陷，交由第二輪 Checker 判定（不自評）。

### 11.3 修補後重跑（同候選）

- 新候選：**`ea2c87b17c794b243c4a8f2fc5b7208b8501ff3248f5de5910ff01bfaddf223e`**（25 檔、manifest 2,570 B）。
- 真 OPS（`40_OPS/ops_r4_r2_*.json`）：POS `0`／5,429 B；`SOURCE_PIN_MISMATCH` 2；`SPAN_INVALID` 2；`EFFECT_DENIED` 64；`SCOPE_MISMATCH` 64；五例皆 `NO_PRODUCT_WRITE_OBSERVED`。
- Native OFF（`40_OPS/native_off_r4.json`）：`NATIVE_OFF_EQUIVALENT_NO_DEPENDENCY`（正/隔離同 exit、同穩定投影 `ea2c87b1…`、外部 TCP 0、外來子進程 0、W 樹無寫、觀測器自測通過）。
- 第二輪 Checker（`B0R1-CHK2-9a3e57`）受檢同一候選；判定待回。

## 12｜Checker 第二輪（真判定）與處置

### 12.1 第二輪實際判定（`B0R1-CHK2-9a3e57`，受檢 `ea2c87b1…`）

| 項 | 判定 | 要點 |
|---|---|---|
| R1.1 撤權／信任邊界 | **PASS** | descriptor byte/SHA 釘住、收據 hash 驗證、live 窗口須同 `window_id`＋`owner_fingerprint`、非確定即 fail closed |
| R1.2 Native OFF | **PASS** | 正常 baseline 與隔離 OFF 真對照、觀測器自測、觀測未成立即不認證 |
| R1.3 N07 | **FAIL** | 逾時路徑本身正確（30 s、隔離、`UNKNOWN_RECONCILE_REQUIRED`、兄弟續行），但 `C-R1-01` 未閉合 |
| R2 候選／pin／OPS | **FAIL** | freeze 重算相符，但當時指向的 POS／pin／span 證據綁的是 `dfc87f18…`（前一個候選），不能證明跑的是本候選 |
| 獨立接受 | **REJECTED** | 因兩個 P1 |

收據（由 Checker final message 原樣轉錄）：`30_VERIFY/verify_r1_receipt.json`；原始 stdout 713,161 B 於 `30_VERIFY/verify_r1_round2_dispatch.json.logs/`。

### 12.2 處置

1. **C-R1-01（第 2 次實質修補，本 finding 額度用盡）**：`reconcile_source()` 改為**以 worker 執行緒終止為門**——執行緒仍存活即回 `False`、隔離保留；終止後（`_read_one` 的 `finally` 已關閉 handle）才解除。測試新增「執行緒存活時 reconcile 被拒」斷言，並保留「第 2 次呼叫不進 reader」的呼叫計數證據。
   - 跨進程：B0 依 §03.N 不得有持久 ledger、產品不得寫檔，隔離只能是進程內；新進程會重新驗權利／pin／全量資料。此項以原 clause 交付判定，由 Checker 決定 `PASS`／`HOLD`，不由我自評。
2. **C-R1-02**：屬證據指向錯誤（我給的路徑是舊候選的 r1 檔）。本輪改以 `daab388d…` 候選的 `ops_r4_r3_*` 為唯一證據，並在 Checker 指令中明示 r1／r2 只作歷史。

### 12.3 修補後重跑（候選 `daab388d5a38597b6ff2b0ec0376f105df6f54d2275b0b86dc23c17ef75df9ee`）

- OPS：POS `exit 0`／5,429 B；`SOURCE_PIN_MISMATCH` 2；`SPAN_INVALID` 2；`EFFECT_DENIED` 64；`SCOPE_MISMATCH` 64；皆 `NO_PRODUCT_WRITE_OBSERVED`；POS envelope 內 `candidate_digest` 等於上述 freeze。
- Native OFF：`NATIVE_OFF_EQUIVALENT_NO_DEPENDENCY`（正/隔離同 exit、同穩定投影、外部 TCP 0、外來子進程 0、W 樹無寫）。
- 第三輪 Checker（`B0R1-CHK3-7d10be`）受檢同一候選；判定待回。

### 12.4 第三輪為何中止、以及第三個修正

- 第三輪 Checker（`B0R1-CHK3-7d10be`）於受檢 `daab388d…` 期間，我在全套回歸中發現新測試的時序假設不穩（`reconcile_source(source_id)` 會被**別的 source 實例**的殘留條目滿足），於是改了 `return_.py`。此舉使受檢樹在 Checker 執行中途變更，其判定必然對不上 freeze——因此**主動 kill 該輪**（非車道故障，是我的變更使該輪失效），不採用其任何結論。
- 第三個修正（同屬 `C-R1-01` 的收斂，非新 finding）：`reconcile_source(key)` 改為**精確 key**，並新增 `quarantine_keys(source_id)`；避免以 `source_id` 解除時誤放行另一個 pin／版本實例。測試改用該 key，並在等待時 `join()` 具體 worker，不再靠固定 sleep。
- 全套回歸在修正後重跑（見 §13）。

## 13｜Checker 第四輪判定與兩個新缺陷

### 13.1 第四輪實際判定（`B0R1-CHK4-2b8f90`，受檢 `21cdf0ae…`）

| 項 | 判定 | 要點 |
|---|---|---|
| R1.1 | **FAIL**（`C-R1-03`, P1） | `_revocation_error` 在 bytes 的 SHA 等於 `authorization_sha`／`context_sha` 時**先回 None**，未檢查 `state`／schema／窗口綁定／到期；把可讀且被 hash 釘住的授權收據（無 `state`）放到撤權引用即可繞過 |
| R1.2 | **HOLD**（`C-R1-04`, P2） | 子進程只用 basename 允許（`icacls`／`attrib`／`whoami`），未核執行檔路徑與參數，無法證明同名子進程是唯讀 |
| R1.3 | **PASS** | 30 s 預算、精確 key 隔離、`UNKNOWN_RECONCILE_REQUIRED`、worker 未終止不得 reconcile、handle 於 `finally` 關閉、兄弟續行 |
| R2 | **PASS** | 獨立重算 25 檔 manifest（2,570 B）與 `candidate_digest` 相符；descriptor／授權 hash／五筆 OPS raw 與 exit 全對；POS envelope 綁定同一候選 |
| 獨立接受 | **REJECTED** | 因 P1 |

收據：`30_VERIFY/verify_r1_receipt_round4.json`；原始 stdout 於 `30_VERIFY/verify_r1_round4_dispatch.json.logs/`。

### 13.2 處置

1. **C-R1-03**：移除 `_revocation_error` 的 hash 短路。授權／context 文件是**簽發事實**、不是 live 撤權狀態，缺 `state` 一律 `RIGHTS_UNVERIFIED`。新增負例 `test_R1_pinned_receipt_bytes_cannot_substitute_for_revocation_state`（把 pin 住的授權 bytes 塞進撤權檔 → 必須拒）。
2. **C-R1-04**：`native_off_r4.py` 改為**路徑＋參數**分類——子進程須為 `System32` 下的真實系統執行檔；`icacls` 出現 `/grant`、`/deny`、`/remove`、`/reset`、`/setowner`、`/setintegritylevel`、`/restore`、`/save`、`/inheritance:w` 任一寫動詞即判 foreign；`attrib` 帶 `+/-` 屬性旗標即判 foreign；python 僅在 argv 含 `b0_reader.cli`（venv redirector）時算 self_reexec。輸出新增 `child_classes_baseline`／`child_classes_off` 逐類計數。

## 14｜最終判定（第五輪 Checker PASS → 收斂）

### 14.1 第五輪判定（`B0R1-CHK5-c417d2`，受檢 `f3fa76ea…`）

| 項 | 判定 |
|---|---|
| R1.1 撤權／信任邊界 | **PASS**（收據 hash 驗證、窗口身分綁定、撤權 bytes 需 OPEN＋schema＋scope＋身分＋未到期、引用逐次重驗） |
| R1.2 Native OFF | **PASS**（觀測器自測可信、正常/隔離同 exit 與同穩定投影、無 TCP、無寫、無 foreign child、逐筆 path/argv 證據） |
| R1.3 N07 | **PASS**（30 s 預算、精確 key 隔離、worker 終止才可 reconcile、handle 於 finally 關閉、兄弟續行） |
| R2 候選／pin／OPS／契約 | **PASS**（獨立重算 25 檔／2,570 B manifest、descriptor pin、授權 digest 與到期、五筆 OPS exit/FirstFail 全對、POS envelope 綁同一 digest） |
| 缺陷 | **[] 無** |
| 獨立接受 | **ACCEPTED** |

收據：`30_VERIFY/verify_r1_receipt.json`（第五輪，ACCEPTED）；前三輪逐輪收據保留為 `verify_r1_receipt_round{4,5}.json` 與各輪 logs。

### 14.2 產品狀態（照 r4 §08.3 分帳）

| 狀態 | 判定 | 依據 |
|---|---|---|
| `B0_SPEC_READY`／ACTIVE | 成立 | r4 定案 ＋ 本輪施工 |
| `B0_ENGINEERING_CANDIDATE` | 成立 | freeze `f3fa76ea…`（25 檔）、137 案 OK |
| `B0_PRODUCT_EXECUTED` | 成立 | 真來源 POS ＋ 四單變異 NEG（`ops_r4_r5_*`）、無產品寫 |
| `B0_CORE_ACCEPTED` | **成立** | 核心產品／安全負例／Native OFF／同候選獨立驗收（第五輪 ACCEPTED）／獨立契約核對 均具 |
| 直接交接 | **B1／B2／B3 各自 ACCEPTED**（`60_B1/receipts/b{1,2,3}_receipt_r5_2026-11-25.json`，同一 POS envelope、`candidate_digest=f3fa76ea…`） | 各 Consumer 以自己的權利入口重驗收據 hash `8f61f584…` 與 live 窗口 |
| `B0_COMPLETE` | **成立（附明列殘餘）** | 當期適用產品義務、真安全負例、Native OFF、同候選獨立接受、輸出契約、合法直接接收皆閉合 |
| `B1_INPUT_READY` | 成立 | B1 對本候選真接收 ACCEPTED |
| `B1_TECHNICALLY_READY`／`B1_READY_EXECUTE` | 不成立 | B1 自身 RepoRoot／commit／BASE／五 Kernel／FDA 與效果授權未取證 |

### 14.3 明列殘餘（不影響上述判定，但不可當成已證）

1. Native OFF 的 `not_proven` 三項：transitive import 的缺席、kernel 級／registry 寫入、取樣窗關閉後的網路活動。
2. 逾時隔離為**進程內**（§03.N 禁產品持久 ledger）；跨進程以新進程重驗權利／pin／全量資料，非同一隔離狀態延續。
3. `00_PREFLIGHT` 為讓 Checker 唯讀可核，對 `CodexSandboxUsers` 加了 `(RX)`（無寫入）；此為證據可讀性措施，已記於 Workorder §1.5。
4. 本輪所有真 OPS 皆在 Owner 窗口 `WIN-7769f20a712c` 有效期內（至 `2026-11-26T02:26:58+08:00`）執行；窗口到期後新的真讀需重新授權。
