# WORK ORDER｜SST_PLP_PH01_W0_B0 DEV（bounded writer: Codex EXECUTE lane）

- subject: `SST/SQS-THC/PH01/E00`｜bid 0｜wave `P1-W00M`
- effect_intent: `SOURCE_READ`｜product WriteSet `[]`｜preimage `N/A`｜`FIN_ORDER=DENY`
- 寫入範圍（唯一）：`C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\20_DEV\`
- 禁止：寫 W 以外任何路徑、讀取或輸出憑證/口令、產生產品 ledger、呼叫網路、安裝套件、修改任何 repo、建立 git commit。
- 語言/執行環境：Python 3.11+（僅 stdlib；測試用 `unittest`），Windows 路徑。

## 1｜交付物

```
20_DEV/b0_reader/__init__.py
20_DEV/b0_reader/errors.py        # typed codes + envelope builders
20_DEV/b0_reader/root.py          # B0.ROOT
20_DEV/b0_reader/bytes_.py        # B0.BYTES
20_DEV/b0_reader/fields.py        # B0.FIELDS
20_DEV/b0_reader/return_.py       # B0.RETURN
20_DEV/b0_reader/cli.py           # 唯讀 CLI
20_DEV/tests/test_b0_root.py
20_DEV/tests/test_b0_bytes.py
20_DEV/tests/test_b0_fields.py
20_DEV/tests/test_b0_return.py
20_DEV/tests/test_b0_cases.py     # §06 主表 14 Case + 6 補充
20_DEV/RUN_TESTS.cmd              # python -m unittest discover -s tests -v
```

## 2｜契約（不得自行改名或增欄）

### 2.1 `SourceErrorEnvelope`
```json
{"schema":"B0.SOURCE_ERROR_ENVELOPE/1","subject":str,"scope":str|null,"batch_id":"B0",
 "errors":[{"affected_locator":str,"code":str,"detail":str,"first_fail":str,"retryable":bool}]}
```
`first_fail` 依原 Case 標籤（見 §4），不可用通用碼覆蓋。

### 2.2 `SourceReadSet`
```json
{"schema":"B0.SOURCE_READ_SET/1","subject":str,"scope":str|null,"batch_id":"B0","version":str,
 "entries":[{"source_ref":str,"source_sha":str,"clause_span":[int,int]|null,"clause_sha":str|null,
   "acl_epoch":str|null,"rights_epoch":str|null,"reader":"B0.ROOT+BYTES+FIELDS(engine)",
   "original_id":str|null,"child_id":str|null,"polarity":"POS"|"NEG"|null,
   "requiredness":"required"|null,"owner":str|null,
   "required_fields":[str],"missing_fields":[{"field":str,"reason":str}],
   "observed":{str:any},"locator":str}],
 "errors":[...]}
```
硬規則：`missing_fields` 只能是 `required_fields` 的子集；`observed` 的 key 與 `missing_fields[].field` 不得相交；**不得刪除 `required_fields` 任何元素**（刪 = `AUTHOR:TOOL_REQUIREDNESS_HOLD`）。

### 2.3 typed codes（固定字串）
`ROOT_NOT_FOUND`、`ROOT_NOT_DIR`、`PATH_ESCAPE`、`REPARSE_POINT`、`ADS_PATH`、`RIGHTS_DENIED`、`NAMESPACE_MISMATCH`、`VERSION_DRIFT`、`ENCODING_INVALID`、`SHA_MISMATCH`、`SPAN_OUT_OF_RANGE`、`REQUIREDNESS_HOLD`、`SCHEMA_INVALID`。

## 3｜四個 Op 的行為

### B0.ROOT — `check_root(allowed_root, source_ref, *, expected_namespace=None, expected_version=None) -> RootVerdict`
1. `allowed_root` 必須存在且為目錄，否則 `ROOT_NOT_FOUND`/`ROOT_NOT_DIR`。
2. 以 `os.path.realpath` 取 realpath，用 `os.path.commonpath` 判 `realpath(source)` 是否在 `realpath(root)` 之下；不在 → `PATH_ESCAPE`（含同層前綴 `C:\a\bb` vs `C:\a\b` 的假包含）。
3. 逐層祖先（含 source 本身）`os.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT` → `REPARSE_POINT`（junction/symlink 皆拒，附 offending path）。
4. ADS：去掉磁碟機代號後，任一路徑分段含 `:` → `ADS_PATH`。
5. 權限：以 `icacls` 讀 DACL 原文入 `acl_raw`，並實際 `open(..., "rb")` 一次；`PermissionError` → `RIGHTS_DENIED`。`acl_epoch` 未由原 Owner 提供時固定 `null`（不得自造）。
6. `namespace`/`version` 若提供 expected 而實測不符 → `NAMESPACE_MISMATCH`/`VERSION_DRIFT`。
7. 回傳 `{"ok":bool,"realpath":str,"acl_raw":str,"code":str|null,"first_fail":str|null}`；失敗時**不得先讀內容**。

### B0.BYTES — `read_bytes(verdict, *, expected_sha=None, clause_span=None) -> dict`
1. 只在上一步 `ok` 時讀 bytes（`open(rb)`）。
2. 嚴格 UTF-8：`bytes.decode("utf-8")` 失敗 → `ENCODING_INVALID`（不得用 errors="replace" 掩蓋）。
3. `source_sha = sha256(bytes)`；`expected_sha` 有值且不符 → `SHA_MISMATCH`（拒漂移，不回退）。
4. `clause_span=[a,b]`（1-based、inclusive）：越界 → `SPAN_OUT_OF_RANGE`；`clause_sha = sha256(exact bytes of those lines incl. terminating "\n" except last)`；行切分只依 `\n`，保留 `\r` 原樣（CRLF 檔不得被正規化）。
5. 回傳 `{"ok","source_sha","clause_span","clause_sha","text","line_count","code","first_fail"}`。

### B0.FIELDS — `split_fields(required_fields, observed, *, verified_by_source) -> dict`
1. `R = list(required_fields)`（保序、保重複偵測）。
2. `P = {f: v for f,v in observed.items() if f in R and verified_by_source.get(f) is True}`；未在 R 的 key → `SCHEMA_INVALID`。
3. `M = [{"field":f,"reason":"NOT_OBSERVED"|"NOT_VERIFIED_BY_SOURCE"} for f in R if f not in P]`。
4. 不變式斷言：`set(M) ⊆ set(R)`、`set(P) ∩ set(M) = ∅`、`len(R)` 不變；違反 → `REQUIREDNESS_HOLD` 並在 envelope 帶 `first_fail="AUTHOR:TOOL_REQUIREDNESS_HOLD"`。
5. 回傳 `{"ok","required_fields","observed","missing_fields","invariants":{"subset":true,"disjoint":true,"r_unchanged":true}}`。

### B0.RETURN — `build_read_set(subject, scope, version, refs, *, expires_transient=True) -> dict`
1. 逐 ref 串 ROOT→BYTES→FIELDS；每個 ref 的錯誤進 `errors`，合法項照常進 `entries`（一缺欄不得全域阻斷）。
2. 產品 `write_set` 必須為 `[]`；函式內**不得**開任何寫入檔（測試會以 `unittest.mock.patch("builtins.open")` 監看）。
3. 回傳 `SourceReadSet`（含 `errors`）；另提供 `to_envelope(errors, subject, scope)`。

### CLI（唯讀）
`python -m b0_reader.cli read --allowed-root PATH --source PATH [--expected-sha HEX] [--span A:B] [--required-field F ...] --json`
輸出單一 JSON 到 stdout；exit 0=全部合法、2=有 typed error。**不得**寫任何檔。

## 4｜Case 矩陣（每 Case 由同一 valid baseline 建構，只做一次單變異）

| CaseID | 期望 first_fail |
|---|---|
| B0.POS.REQ-12__AUTHOR-SPLIT-01（4 欄全 provided / verified） | `NONE_IF_VALID` |
| B0.NEG.REQ-12__AUTHOR-SPLIT-01.DELETE_CHILD（刪 child_id） | `AUTHOR:TRACE_ORPHAN` |
| B0.NEG.REQ-12__AUTHOR-SPLIT-01.DELETE_NEG（刪 polarity=NEG 的設計項） | `AUTHOR:NEG_MISSING` |
| B0.NEG.REQ-12__AUTHOR-SPLIT-01.FIELD_read（只改 `read` 欄值） | `AUTHOR:CHILD_RULE_HOLD:REQ-12::AUTHOR-SPLIT-01` |
| B0.POS.AUTHOR_SOURCE_AUTHORITY | `NONE_IF_VALID` |
| B0.NEG.AUTHOR_SOURCE_AUTHORITY（改受保護欄 scope） | `AUTHOR:SOURCE_AUTHORITY_HOLD` |
| B0.POS.AUTHOR_CONTROL_SCHEMA | `NONE_IF_VALID` |
| B0.NEG.AUTHOR_CONTROL_SCHEMA | `AUTHOR:CONTROL_SCHEMA_HOLD` |
| B0.POS.AUTHOR_FOUR_READY | `NONE_IF_VALID` |
| B0.NEG.AUTHOR_FOUR_READY（把 false 改成 true） | `AUTHOR:FOUR_READY_HOLD` |
| B0.POS.AUTHOR_READ_WRITE_SCOPE | `NONE_IF_VALID` |
| B0.NEG.AUTHOR_READ_WRITE_SCOPE（write_set 塞值） | `AUTHOR:READ_WRITE_SCOPE_HOLD` |
| B0.POS.AUTHOR_UNKNOWN_UNDO | `NONE_IF_VALID` |
| B0.NEG.AUTHOR_UNKNOWN_UNDO（UNKNOWN 直接 retry） | `AUTHOR:UNKNOWN_UNDO_HOLD` |
| AUTHOR.EXEC.C01.SUBJECT（換 subject） | `AUTHOR:SCOPE_MISMATCH` |
| READ_WRITESET/DEV_EFFECT | `AUTHOR:EFFECT_UNBOUND` |
| CLAIM_QUALIFIED（claim 升格） | `AUTHOR:CLAIM_CEILING_DENY` |
| AUTHOR.READSET.ONE_MISSING | `NONE_IF_VALID` + `missing_fields==[x]` |
| AUTHOR.READSET.COMPLETE | `NONE_IF_VALID` + `missing_fields==[]` |
| AUTHOR.READSET.DROP_REQUIRED | `AUTHOR:TOOL_REQUIREDNESS_HOLD` |
| SEC.PATH_ESCAPE（`../` 逃出 root） | `PATH_ESCAPE` |
| EDGE.STALE_EPOCH（epoch 不符） | `NAMESPACE_MISMATCH`（本 B 以 namespace/epoch 同欄承載） |

實作要求：作者層的 control 類 Case 用 `b0_reader.controls.evaluate(doc, contract)`（可另建 `controls.py`）驗：`doc` 是作者契約投影（`subject`、`effect_intent`、`write_set`、`ready_*`、`claim_ceiling`、`unknown_policy`、`read_set`），回傳 `(ok, first_fail)`。此模組只做作者文件界線檢查，**不得**冒充原 CaseRegistry。

## 5｜完成判準（你必須自己跑過）
1. `python -m unittest discover -s tests -v` 全綠，且每個 Case 至少一個測試函式以 CaseID 命名（例：`test_B0_NEG_REQ_12_DELETE_CHILD`）。
2. 測試自建 fixture：在 `tempfile.TemporaryDirectory()` 內造檔（含一個 CRLF 檔、一個 UTF-8 失敗位元組檔、一個 junction 檔若權限允許則 skip）。**不得**在 W 內留下暫存。
3. 全部程式碼含 module docstring 標明 `AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED`。
4. 不得引入第三方套件。
5. 最後輸出：測試摘要（通過數/失敗數）與 `b0_reader` 各檔 sha256。

## 6｜明示界線
本 work order 只授權 DEV 隔離作者候選；原 `OperationType`/`EffectRegistry`/`OriginalReader`/`CaseRegistry`/`RawSchema` 仍未綁（BR.B0.*），因此本產出**不得**自稱 `ReadyExecute`/`ReadyAccept`，不得寫產品 ledger，不得宣稱 B1 可接收。
