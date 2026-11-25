# WORK ORDER｜SST_PLP_PH01_W0_B0 r4 Native-first DEV（bounded writer = Codex EXECUTE 車道）

- subject `SST/SQS-THC/PH01/E00`｜OriginalWave `P1-W00M`｜BID `0`｜effect `SOURCE_READ`
- product `WriteSet=[]`／`preimage=N/A`／`FIN_ORDER=DENY`
- 唯一規格根 S：`C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8\SST_PLP_PH01_W0_B0_執行控制小包\B0_NATIVE_FIRST_2026-11-25_r4_CODEX_FINAL`
- 唯一正文：`SST_PLP_PH01_W0_B0_執行控制小包_實質正文_2026-11-25_r4_Native-first_定案.md`（raw SHA256 `582a54048d8b63e37be3d803c829a12ffe164be72963f026cea1a1b6183345d9`，99,791 bytes）
- 車道：EXECUTE = Codex CLI（opencode-go/deepseek-v4.1-flash）。本工單只授權**工程**寫入，不授任何產品寫入效果。
- 本檔是 r4 施工工單。歷史 `WORKORDER_B0_DEV.md`（v1 契約）、`exec_*_receipt.json` 保留為 LastGood 歷史，不刪不改。

## 1｜寫入範圍（精確 WriteSet，逐檔核 preimage）

寫入根 W = `C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace`；下列以外**不得**寫（含 TEMP/TMP 不得落 W 外）。

### 1.1 既有檔（改前 current 必須等於 §1.3 preimage）

```
20_DEV/b0_reader/__init__.py
20_DEV/b0_reader/errors.py
20_DEV/b0_reader/root.py
20_DEV/b0_reader/bytes_.py
20_DEV/b0_reader/fields.py
20_DEV/b0_reader/return_.py
20_DEV/b0_reader/cli.py
20_DEV/tests/test_b0_root.py
20_DEV/tests/test_b0_bytes.py
20_DEV/tests/test_b0_fields.py
20_DEV/tests/test_b0_return.py
20_DEV/tests/test_b0_cases.py
20_DEV/RUN_TESTS.cmd
```

### 1.2 本批新增（先記入本工單，再建）

```
20_DEV/b0_reader/native_entry.py    # §04.N1 可信啟動接線 resolve_context_for_current_principal()
20_DEV/b0_reader/winio.py           # Windows 同 handle 讀取／身份（ctypes + stdlib，無第三方）
20_DEV/b0_reader/requiredset.py     # RequiredSetSpec 載入與 R/rules 驗證（純資料，不執行其內容）
20_DEV/tests/test_product_read.py
20_DEV/tests/test_windows_security.py
20_DEV/tests/test_contract_probe.py
20_DEV/tests/test_native_off.py
20_DEV/tests/fixtures/…             # 只放 synthetic 測試輸入
```

`20_DEV/b0_reader/controls.py` 保持原檔不改（作者層控制仍使用）。

### 1.3 DEV-0 preimage（2026-11-25 實測 raw SHA256 / bytes）

```
ded1d82e28a3e78d6a135423552e90bbc4eb19d34c05c170f28cc02387515331   617  b0_reader/__init__.py
240cecda8c49589dea28638717061bffadf865f47d5fbc1d926d2fb5c39e9620  2485  b0_reader/errors.py
e84c8cdd1e4beeb4a564fcfecc8f3442a78a64f7641b4c479344180c0873724d  8071  b0_reader/root.py
2cf306586d364c4c778b2acd25e9b01abe9accd45785a54b472e84a3e7e97d71  5079  b0_reader/bytes_.py
cd0c2e77cc0ce4bb93e8c9ccfb25c3ce56ea6e24dcfa38ec2926fa69e6050acb  3965  b0_reader/fields.py
265455d3c3cdd6ec2bf8824d5c540455af4e36b0592865089498edc45e08e7e1  5668  b0_reader/return_.py
c33985364ddde0b8f42e5ebb9c5c1f01d74cad74cc1504ff041231a4942c27cd  2172  b0_reader/cli.py
59d21d6a98f0cb566369080b2cc94eeb760d71996ca9a5a90a46f495cfe45c8d  4361  tests/test_b0_bytes.py
704214db3f8c2226cd141e87ee1300cbce4ce8a6216d66ee01a444dac508564b 10734  tests/test_b0_cases.py
a3efc85f05320c9c1248074298c5d24ecff0d38045b0338f736905c5324bd9e6  3246  tests/test_b0_fields.py
c0bdeb456767217729a813f2f98d67c85c0fbbc7a7bd51bc4c5025351da210c1  6133  tests/test_b0_return.py
57c0131489ba56848b83d783f3caac6d799eb43a1859c1cdb92e0fb345d80bbc  6339  tests/test_b0_root.py
b6a1d4f16eaed26d1deefa882bc0ebf5aabc01c9687a825fa2f85eb009d8e6db    64  RUN_TESTS.cmd
```

## 1.4 本輪受影變更（Commander 記錄，2026-11-25）

1. `20_DEV/b0_reader/native_entry.py` 部署 pin 隨 descriptor 換版刷新兩次（唯一定義見下表；以最後一列為準）：
   - `00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json` 首建 `14fa622c…`／3624 → Owner 重開視窗後 `2a4a77e9…`／3606 → 修正 descriptor 的 `allowed_principal` 大小寫與 `expires_at` 時區後 **`b8759ca7f5c213024c4046db07494cabb355d39d051b0082ff043845e9fb45e0`／3612**（現行）。
   - 每次刷新都是 descriptor 換版後的受影 pin 同步，不是新契約；候選 freeze 以現行值為準。
2. 工程執行環境：Hermes 預設設 `TMPDIR`，而 `_mint_isolated_context` 只讀 `TEMP`，會使 8 個隔離 fixture 誤判 `TRUST_CONTEXT_UNBOUND`。可重現的可用組合是 `unset TMPDIR; TEMP=TMP=<W>/20_DEV/.tmp_tests`；此環境敏感度列為 finding（候選修法：guard 同時考慮 `TMPDIR`／`TMP`，或以 W 內核實根判 containment）。
3. **受權範圍內的 host 收緊（非改 K、非改他人 ACL）**：Checker P1 指出 `icacls` 結果未被使用；實作 sealed 檢查後量到 `00_PREFLIGHT` 與其子檔對 `NT AUTHORITY\Authenticated Users` 有 `(I)(M)`（`C:\Projects` 繼承），部署信任根因此不成立。處置：對**本批自有** `W/00_PREFLIGHT` 目錄 `/inheritance:r /grant:r` 只授 `DESKTOP-57EO414\user`、`SYSTEM`、`Administrators`，並 `icacls <dir>\* /reset` 讓子檔重新繼承；K 知識庫、原 repo、他人檔案 ACL 一律未動。收緊後 `resolve_context_for_current_principal()` 可用且 `require_sealed` 通過。
4. `native_entry._owner_window_is_valid` 對 Owner 視窗 JSON 採「必填鍵 ⊇」而非「全等」（`owner_window.py` 會多寫 workspace／fingerprint 等鍵），否則真視窗永遠被判無效；此為與 Owner 既有機制的介面對齊，非放寬。
5. 檔案寫入集不變；第 3 項是 ACL（非檔案內容）動作，已在此具名記錄。

## 2｜規格即 oracle（不得改欄名、不得自創 normative 欄）

實作前必讀正文：`§02.A`、`§02.F`（v2 wire 全欄位表）、`§02.E`（SourceErrorEnvelope／exit）、`§02.R`（型別與集合封閉定義）、`§04.0`、`§04.ROOT`、`§04.BYTES`、`§04.FIELDS`、`§04.RETURN`、`§04.D`（FirstFail 次序／retry）、`§04.N`（CLI 契約）、`§04.N1`（可信接線與 descriptor 最小欄）、`§06.0–06.4`（測試契約與 freeze 算法）。與本工單衝突時以正文為準，並在回報列出衝突點。

硬性不變量（違反＝缺陷，不得用測試繞過）：

1. `wire_version` = literal `SST.B0.SourceReadSet/2`；一來源一 entry；`sha` = 該來源全部 raw bytes SHA256（非集合 hash）。
2. 頂層固定：`subject`/`original_wave`/`bid`(int 0，非 bool)、`spec_version`、`candidate_digest`、`scope`、`source_manifest`、`entries`、`errors`、`write_set=[]`、`preimage="N/A"`、`fin_order="DENY"`、`extensions={}`。每請求 source_id 恰有一個 entry 或一個 fatal error。
3. entry：`source_ref{source_id,namespace,locator,source_version}`、`sha`、`byte_length`、`encoding`、`clause_span`、`clause_sha`、`original_id`、`child_id`、`polarity`、`requiredness`、`owner`、`provenance{requirement_ref,requirement_sha,requirement_span,rule_ref,rule_sha}`、`required_fields`(=原 R)、`observed{field:{value,source_sha,span,value_sha}}`、`missing[{field,reason,source_ref}]`、`authority{…全 13 欄…}`、`acl_epoch`、`rights_epoch`。缺任一必填＝WIRE_INVALID。
4. `missing` = R − P，逐欄一筆、不得重複；`P=keys(observed)`；`P∩M=∅`；`required_fields` 永遠等原 R，不得刪。
5. 所有 integer 拒 bool；span `a≥1, b≥a`；SHA 64 小寫 hex；集合按 Unicode code point 升序；duplicate key／NaN／未知 normative 欄拒。
6. exit：0＝全部成功且 M 空；2＝有 M 或來源級 error；64＝invocation／context 不成立（stdout 空）；70＝未知內部狀態（不得輸出可能部分授權內容）。
7. 產品**不得**寫任何檔／ledger／cache／bytecode；四 Op 只暫態回傳。
8. caller 不得自授 allowed-root／required-set／authority／`verified=true`；`read_sources(request, *, trusted_context)` 的 context 只能由受權內部接線建立。

## 3｜各模組要求（重點，正文為準）

- `errors.py`：typed error 物件＋`SourceError` 序列化（`source_id,op,code,first_fail,affected_locator,retryable,attempt,resume`）；實作 `§04.D` 全部新碼；`RIGHTS_DENIED` 不 retryable；不得 traceback／洩內容；舊 v1 碼只留作者兼容並明示不升格。
- `winio.py`：`CreateFileW`（GENERIC_READ、`FILE_SHARE_READ`、`OPEN_EXISTING`、`FILE_FLAG_BACKUP_SEMANTICS` 供目錄、不建立）；`GetFinalPathNameByHandleW`、`GetFileInformationByHandle`（volume serial + file index）、`FileAttributeTagInfo` 判 reparse、`ReadFile` 由同 handle 讀；`CreateFileW` 失敗映射 typed code；禁止以 `open(path)` 作安全 fallback。
- `root.py`：移除 `source.parent` 推 root 的 fallback；路徑語法拒絕（`..`、relative、drive-relative、device／UNC／extended-device、NUL、wildcard、磁碟代號後 ADS 冒號、尾隨點／空白）；component-wise containment（`C:\ok2` 不在 `C:\ok`）；根→磁碟根每個祖先及根內每層核 reparse；`lstat`／ACL 未知即 `PATH_IDENTITY_UNVERIFIED`（不得 `except: pass`）；開 handle 前後 final path／identity 核對；`RIGHTS_*`／`EPOCH_STALE` 依 context 真值。
- `bytes_.py`：同 handle binary read；raw SHA（含 BOM/CR/LF）；strict UTF-8；只把檔首 BOM 當格式標記；物理行只以 CRLF/LF/CR 分隔；span 取行 a 開頭到行 b 原 terminator；`clause_sha` 對原 bytes slice（不得先 join LF）；讀後再核 identity／size／hash／權利，漂移即 `SOURCE_CHANGED`。
- `fields.py`：從已核 RequiredSetSpec 取 R 與 rules；只支持 `RAW_SPAN_UTF8`／`MD_LABEL`（prefix 完整 literal，恰一筆；0 筆 ABSENT、多筆 AMBIGUOUS、未支持 FORMAT_UNSUPPORTED）；P 只含同源 SHA／span／value_sha 相符欄；`observed.value_sha` = value 字串 exact UTF-8 SHA；caller 自報 observed／verified 一律不採。
- `return_.py`：`read_sources(request, *, trusted_context) -> tuple[dict,int]`；逐源分帳（兄弟可續）；RETURN 前再驗權利／身份／時效／撤權；自身型別與不變量檢查；不得以 checked_at 冒當前有效。
- `cli.py`：`python -B -m b0_reader.cli read --request-json -`（stdin 讀 `B0ReadRequest/2`）；`request_version`／`effect=SOURCE_READ`／`write_set=[]` 錯值→`EFFECT_DENIED` exit 64；不接受 `--context`／`--allowed-root`／`--source` 自我授權；stdout 恰一個 UTF-8 JSON object、無 BOM、無前後文字；`--help` 必須可用。
- `native_entry.py`：`resolve_context_for_current_principal()`；descriptor 固定 locator `W/00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json` + expected pin（部署常數，不得於啟動時自算現值）；驗 actual OS token／principal、descriptor 祖先與 ACL（不可被不可信 caller 改寫）、有效期／撤權、`context_version=B0TrustedContext/1`；任一不成立→`TRUST_CONTEXT_UNBOUND`（產品 CLI exit 64、stdout 空）。不得讀 request／cwd／env／source.parent 決定根或 pin。
- `requiredset.py`：載入 RequiredSetSpec（純資料：`requirement_ref/sha/span`、`original_id`、`child_id`、`polarity`、`requiredness`、`owner`、`required_fields`、`rules`）；驗 ref/pin/span 可回原來源；規則 JSON raw SHA 即 `provenance.rule_sha`；不執行內容；R 未知／規則不全→`REQUIRED_SET_UNBOUND`。

## 4｜測試要求

1. 每個 Case 一個以 CaseID 命名的測試函式；`§06.1` 14 主案、`§06.2` 8 補充群身分保留（載體可依 r4 已採納差額更新，但不得改原安全意義）。
2. 新測試模組對應 `§06.3` N01–N09 與 `§06.3a`；N02/N07 用受權隔離真 OS 行為（TemporaryDirectory + 隔離根）；無法建置 junction 時記 HOLD 並說明缺什麼，不得以 monkeypatch 字串冒充。
3. `test_contract_probe.py` 必須是獨立 validator（自行依 `§02.F` 實作型別／集合／tuple 檢查），**不得 import** Maker 的 serializer 當 oracle。
4. fixture 自建於 `TemporaryDirectory`；不得在 W 留暫存；不得複製真權利資料入公開區。
5. 測試環境：`PYTHONDONTWRITEBYTECODE=1`、`python -B`、TEMP/TMP 指向 W 內隔離目錄。
6. 你要自己跑：`python -B -m unittest discover -s tests -v`，全綠才算交付；不得 skip 當 PASS（skip 需列出理由）。

## 5｜界線

- 不引入第三方套件；不呼叫網路；不建 git commit／不 push；不改 W 外任何檔（含 HG-KSEOS 車道配置、ACL、K 知識庫）。
- 不得自稱 `ReadyExecute`／`ReadyAccept`／`B1_INPUT_READY`；不得寫產品 ledger；不得偽造 raw／exit／consumer ACK。
- 模組 docstring 需標 `AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED`（工程候選，非產品驗收）。
- 發現與正文衝突或需新增非清單檔，先停下回報，不得自行擴張寫入集。

## 6｜回報格式（stdout 最後一段，繁體中文）

```
1) 變更檔案清單 + 每個檔的 raw SHA256 + bytes
2) unittest 摘要（ran / OK / FAILED / skipped 及原因）
3) 與正文衝突或未實作項目（逐條，含原因）
4) 已知限制／HOLD（例如無 junction 建置權）
```

## 1.5｜2026-11-25 20:26 後（R1／R2 差額）

1. **Owner 授權續期**：新窗口 `WIN-7769f20a712c`（Owner 本人口令，6h、12 ops、`READ_ONLY_PROBE`、scope `b0_source_read_authority,sqs_thc_ph01_e00`）。收據 raw SHA `8f61f584006fdeea19dbd312b0c3d6f94f89229f7ff0bc6c5c8d811701d6a0ff`（930 B）。descriptor 的 `authorization_sha`／`expires_at`／`valid_from` 及**每源** `usage_evidence_sha` 皆重綁到本收據，descriptor 現為 3,846 B／`c57518c457c5c3c9a4bf52f0a5ade422aed624249ff1e79e055e8d52f84f6dea`；`native_entry.EXPECTED_DESCRIPTOR_*` 同步。
2. **撤權綁定（R1.1）**：`native_entry._pinned_receipt`／`_window_matches_receipt`，live 窗口必須與 pinned 收據同 `window_id`＋`owner_fingerprint`，無法綁定即 `RIGHTS_UNVERIFIED`。
3. **每源 30 秒上限與隔離（R1.3／C-R1-01）**：`return_.SOURCE_READ_LIMIT_SECONDS=30.0`、`_read_with_budget`；逾時源寫入 `_QUARANTINE`，**reconcile 前不得重入**（連 reader 都不呼叫），`quarantine_state()`／`reconcile_source()` 提供狀態與解除。跨進程仍以新進程重驗（CLI 每次新進程），此限制已在 CLOSEOUT 註明。
4. **ACL：Checker 唯讀可讀性**：`00_PREFLIGHT` 對 `DESKTOP-57EO414\CodexSandboxUsers` 授與 `(OI)(CI)(RX)`，檔層再加 `(R)`；**未給任何寫入權**，`root.py` 的 sealed 檢查仍以「broad principal 不得有寫入權」為準，產品 POS 重跑 exit 0 未受影響。目的：解除前兩輪 Checker 只能讀 22/25 檔的證據可讀性缺口。
5. **檔案寫入集**：新增／修改 `20_DEV/b0_reader/{native_entry.py,return_.py}`、`20_DEV/tests/{test_product_read.py,trust_fixture.py,test_native_off.py}`、`40_OPS/{native_off_r4.py,candidate_freeze.json}`、`00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json`（ACL 另記於第 4 項，非內容變更）。
