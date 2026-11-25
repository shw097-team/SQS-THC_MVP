# Independent Checker (VERIFY_SECURITY) — B0 r4 差額複核（窄版）

你是分離的只讀 Checker。**不得修改任何 Maker 候選檔、不得寫入 `20_DEV/`、`00_PREFLIGHT/`、`40_OPS/`、`60_B1/`**；唯一可寫位置是 `30_VERIFY/verify_r1_receipt.json` 與 `30_VERIFY/verify_r1_notes.md`。

## 0｜環境

- cwd＝`C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace`（以下稱 W）。
- 規格根 S（只讀）＝`C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8\SST_PLP_PH01_W0_B0_執行控制小包\B0_NATIVE_FIRST_2026-11-25_r4_CODEX_FINAL`，正文＝`SST_PLP_PH01_W0_B0_執行控制小包_實質正文_2026-11-25_r4_Native-first_定案.md`。
- 受檢候選 freeze：`40_OPS/candidate_freeze.json`，**candidate_digest＝`f3fa76eaa1c083af39c88610492a5fcad482dc5b5bbb7eb9a79e2234c8dca49e`**（25 檔）。請**自己重算** manifest 驗證此 digest，不要相信既有數值。
- 禁止：連網、pip 安裝、改 ACL、執行 `40_OPS` 的產品命令、以 Maker 的 serializer 當 oracle。

## 1｜先固定 oracle（先於讀候選）

依 S 正文下列條文，先寫下你認為正確的期望，再讀候選：

1. §02.F（v2 wire 必填、`authority` 欄位、`acl_epoch`/`rights_epoch` 可 null 條件、單源 raw SHA）
2. §04.ROOT（可信 context、allow-list、祖先／reparse／ADS／同 handle）
3. §04.RETURN（RETURN 前再驗權利、撤權即移除內容）
4. §04.N1（descriptor 為受管部署資料、不可由 caller 自授權）
5. §04.0／§04.R／§06 N07（每源 30 秒上限、timeout 後 UNKNOWN reconcile、真暫態最多額外一次、拒權不 retry）
6. §06 N05／N08（無產品寫、Native OFF）

## 2｜受檢四項（只判這四項，其餘不擴張）

### R1.1 撤權／信任邊界

- 讀 `20_DEV/b0_reader/native_entry.py`：`_pinned_receipt`、`_window_matches_receipt`、`_revocation_error`。
- 判點：
  a. live Owner 窗口是否**必須**是 pinned 收據所指的同一個窗口（`window_id`＋`owner_fingerprint`），而非只靠 `state=OPEN` 或到期上限；
  b. 收據缺窗口識別／hash 不符時是否 fail closed；
  c. ROOT 與 RETURN 前是否都會再驗（追 `read_sources` → `_read_one` → `_revalidate_source`）；
  d. caller 是否能自授權（自行指定 context／root／verified）。
- 對照測試：`20_DEV/tests/test_product_read.py` 的 `test_R1_live_window_must_be_the_window_the_receipt_was_issued_for`、`test_R1_receipt_without_window_identity_cannot_authorise`。

### R1.2 Native OFF 與無產品寫

- 讀 `40_OPS/native_off_r4.py` 與其輸出 `40_OPS/native_off_r4.json`。
- 判點：
  a. 是否為**正常 baseline 與隔離 OFF 的真對照**（不是兩個 reduced run）；
  b. 觀測器是否有自測（能否看到已知子進程與已知連線），且 `observation_ok` 為真；
  c. 是否記錄子進程／連線／產品寫入，並排除合法 `icacls` 與 venv redirector 造成的假陽性；過濾是否過寬而可能漏真實依賴；
  d. `not_proven` 是否誠實（transitive import、kernel 級寫入、取樣窗後網路）。

### R1.3 N07 恢復與停止

- 讀 `20_DEV/b0_reader/return_.py`：`SOURCE_READ_LIMIT_SECONDS`、`_read_with_budget`。
- 判點：逾時是否回該源 `UNKNOWN_RECONCILE_REQUIRED`（非靜默截斷）、兄弟來源是否續行、是否可能重入未 reconcile 的來源、被放棄讀取的 handle 是否會逸出。
- 對照測試：`test_N07_source_read_budget_reports_unknown_and_keeps_siblings`。

### R1.3b 逾時隔離（上一輪 C-R1-01 的修補，必核）

- 上一輪判定 `C-R1-01`（P1）：逾時後無隔離狀態，允許重入。本輪修補為 `return_._QUARANTINE`＋`quarantine_state()`＋`reconcile_source()`，逾時源在 reconcile 前不得重入。
- 請核：a) 逾時是否寫入隔離；b) 第二次呼叫是否**在呼叫 reader 前**就拒；c) reconcile 後是否恢復；d) 是否仍有跨進程（CLI 每次新進程）繞過隔離的殘留風險——若有，明確寫成 HOLD／缺陷，不要放寬。
- 對照測試：`tests/test_product_read.py::test_N07_timed_out_source_is_quarantined_until_reconciled`、`test_N07_source_read_budget_reports_unknown_and_keeps_siblings`。

### 上一輪兩個 P1 的處置（必判，不要沿用舊結論）

1. `C-R1-01`（逾時隔離的解除條件、跨進程）：本輪把 `reconcile_source(key)` 改為**精確隔離 key**（另有 `quarantine_keys(source_id)`），並**以 worker 執行緒是否終止為門**——執行緒仍存活時回 `False`、隔離保留；終止後才解除。跨進程部分：B0 依 §03.N 明定**不得有持久冪等 ledger、產品不得寫檔**，因此隔離狀態只能是進程內；新進程會重新驗權利／pin／整份資料。
   請判：(a) 執行緒終止作為「讀取已結束、handle 已釋放」的證據是否充分（`_read_one` 的 `finally` 是否必然關閉 handle）；(b) 跨進程缺口在該 SPEC 約束下應判 `PASS`、`HOLD`（附原 clause）還是 `FAIL`。**若判 HOLD／FAIL，請直接寫明，不要放寬。**
   對照測試：`tests/test_product_read.py::test_N07_timed_out_source_is_quarantined_until_reconciled`（含「執行緒存活時 reconcile 被拒」的斷言）。

2. `C-R1-02`（證據指向不同候選）：上一輪你讀到的是 `ops_r4_r1_*`（`dfc87f18…`，屬已作廢候選）。本輪受檢與證據皆為 `daab388d…`：`40_OPS/ops_r4_r5_pos.json`、`ops_r4_r5_neg_{pin,span,effect,scope}.json` 及其 `.raw/`。`ops_r4_r1_*`／`ops_r4_r2_*`／`ops_r4_r3_*` 只作歷史，**不得**當作本次證據；若你仍看到任何本次證據綁定非 `daab388d…`，請照實判 FAIL。

### 上一輪兩個新缺陷的處置（必判，不要沿用舊結論）

1. `C-R1-03`（P1）：`_revocation_error` 已**移除 hash 短路**——不再因 bytes 的 SHA 等於 `authorization_sha`／`context_sha` 就回 None；授權文件缺 `state` 一律 `RIGHTS_UNVERIFIED`。請核 `native_entry.py` 的 `_revocation_error` 現行版本，並看負例 `tests/test_product_read.py::test_R1_pinned_receipt_bytes_cannot_substitute_for_revocation_state`。若你認為仍有其他等價繞過（例如把 context 檔塞進撤權引用），請直接寫成新缺陷。
2. `C-R1-04`（P2）：`40_OPS/native_off_r4.py` 的子進程分類改為**image path ＋ 參數**：必須是 `%SystemRoot%\System32\` 下的真實執行檔；`icacls` 出現 `/grant`、`/deny`、`/remove`、`/reset`、`/setowner`、`/setintegritylevel`、`/restore`、`/save`、`/inheritance:w` 任一即 foreign；`attrib` 帶 `+/-` 旗標即 foreign；`python` 僅在 argv 含 `b0_reader.cli`（venv redirector）時算 self_reexec。輸出含 `child_classes_baseline`／`child_classes_off` 與 `child_paths`。請判此證據是否足以解除 HOLD；不足則明確寫出還缺什麼（例如需逐筆 path+args 清單）。

### R2 候選／pin／OPS 與契約

- 自行重算 freeze manifest（UTF-8 相對 POSIX 路徑排序、`path<TAB>sha<TAB>byte_length<LF>`、其 SHA256）。
- 對照 descriptor `00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json` 的 `authorization_sha`／`expires_at` 是否與收據 `C:\Projects\Agent_Workspace\FHS_NEXT_Workspace\FHS_vNEXT_W0W1_CLOSEOUT_W2_ENTRY_20261115\owner_ws\artifacts\OWNER_WINDOW.json` 一致，且 `native_entry` 的 `EXPECTED_DESCRIPTOR_SHA`／`BYTES` 與檔案實測相符。
- 讀 `40_OPS/ops_r4_r5_pos.json` 與 `ops_r4_r5_neg_{pin,span,effect,scope}.json`、`.raw/stdout.txt`：exit／stderr FirstFail 是否符合 §04.D（pos 0；pin `SOURCE_PIN_MISMATCH` 2；span `SPAN_INVALID` 2；effect `EFFECT_DENIED` 64；scope `SCOPE_MISMATCH` 64），且 envelope `candidate_digest` 等於你重算的 digest、兩個 entry 的 raw sha 與 §02.F 要求一致。
- 上一輪有 3 個 `00_PREFLIGHT` 檔因 ACL 讀不到（`EPERM`）。本輪已對 `DESKTOP-57EO414\CodexSandboxUsers` 授與 **唯讀** `(R)/(I)(RX)`（未給寫入）。請確認現在能讀全 25 檔並重算 manifest。
- **契約 oracle 自建**：用你自己的解析器（不得 import `b0_reader`）驗 v2 必填與型別。

## 3｜輸出

你的 sandbox 為唯讀，**無法寫檔**（上一輪即因此無法交付）。所以：**不要嘗試寫檔**，改為在 final message 內先輸出一個 fenced ```json 區塊（完整 receipt），再輸出判定摘要。Commander 會把你的 bytes 原樣記入 `30_VERIFY/verify_r1_receipt.json` 並保留你的原始 stdout 作佐證。

receipt 形狀：

```json
{
  "checker": "VERIFY_SECURITY",
  "candidate_digest_recomputed": "<64 hex>",
  "candidate_digest_matches": true/false,
  "items": [
    {"id": "R1.1", "verdict": "PASS|FAIL|HOLD|NOT_VERIFIED", "reason": "...", "evidence": ["path:line"]},
    {"id": "R1.2", "verdict": "...", "reason": "...", "evidence": []},
    {"id": "R1.3", "verdict": "...", "reason": "...", "evidence": []},
    {"id": "R2",   "verdict": "...", "reason": "...", "evidence": []}
  ],
  "defects": [{"id": "C-R1-01", "severity": "P0|P1|P2", "where": "file:line", "what": "...", "why_it_matters": "..."}],
  "independent_acceptance": "ACCEPTED|REJECTED|INSUFFICIENT",
  "notes_path": "30_VERIFY/verify_r1_notes.md"
}
```

規則：
- 只憑你能引用到 `path:line` 或具體證據者給 PASS；看不到／不能離線證明者給 `NOT_VERIFIED`，不要用「看起來沒問題」代替。
- 發現真缺陷寫進 `defects`，不要自己改程式。
- `independent_acceptance` 只在你四項皆 PASS 且無 P0/P1 缺陷時給 `ACCEPTED`。
- 最後一行單獨輸出（literal，勿改寫）：`NONCE=B0R1-CHK5-c417d2`
