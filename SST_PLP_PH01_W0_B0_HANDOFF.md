# SST_PLP_PH01_W0_B0_HANDOFF

- subject `SST/SQS-THC/PH01/E00`｜OriginalWave `P1-W00M`｜BID `0`｜effect `SOURCE_READ`
- 供 B1／B2／B3 最小接收使用；本檔不代 B1 發任何 Permit，不改 PH01／W0M active pin
- 同源：`SST_PLP_PH01_W0_B0_CLOSEOUT.md`（判定與證據在該檔；本檔只交接口與現況）

## 1｜可實際呼叫的入口（已實測）

```text
cwd   = C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\20_DEV
cmd   = python -B -m b0_reader.cli read --request-json -
stdin = 一個 UTF-8 JSON object（B0ReadRequest/2），無 BOM、無前後文字
stdout= 一個 UTF-8 JSON object（SST.B0.SourceReadSet/2）或空（exit 64/70）
```

| 實測項 | 值 |
|---|---|
| `--help` | exit 0，261 bytes（`usage: python -B -m b0_reader.cli read [-h] --request-json -`） |
| 空 stdin／無可信 context | exit 64、stdout 0 bytes、stderr `TRUST_CONTEXT_UNBOUND` |
| 可信 context 解析 | `b0_reader.native_entry.resolve_context_for_current_principal()` → principal `DESKTOP-57EO414\user`、兩來源、`valid_from 2026-11-25T12:11:29+08:00`、`expires_at 2026-11-25T20:11:29+08:00` |
| 部署 descriptor | `W/00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json`，3,612 bytes，SHA256 `b8759ca7f5c213024c4046db07494cabb355d39d051b0082ff043845e9fb45e0`（`native_entry.py` 內固定常數；不接受 `--context`／env／cwd 決定） |
| 程式 API | `b0_reader.return_.read_sources(request, *, trusted_context) -> (envelope, exit_code)`（`trusted_context` 只能由受權內部接線建立） |
| 候選 freeze | `candidate_digest=5ec38e9c1835dba89c5755acd2f2c720aadd9193dd96d08d0a1fe7ddfa36c456`（25 檔；Commander 與產品獨立重算一致） |
| request 範本 | `W/40_OPS/b0_read_request_2026-11-25.json`（`request_digest=0d681d2a47dbccd091edb5dee6f1734361abb2bc576865fab6b8f4460b86e00c`） |

## 2｜本次真輸出的 v2 內容（B1/B2/B3 可直接比對）

實跑 raw：`40_OPS/ops_r4_h_pos.raw/stdout.txt`（5,429 bytes），exit 0；`40_OPS/ops_r4_h_pos.json` 記 argv／cwd／exit／無寫。

| 欄 | 值 |
|---|---|
| `wire_version` | `SST.B0.SourceReadSet/2` |
| `subject/original_wave/bid` | `SST/SQS-THC/PH01/E00`／`P1-W00M`／`0`（integer） |
| `spec_version` / `candidate_digest` | `2026-11-25_r4_Native-first` / `5ec38e9c1835dba89c5755acd2f2c720aadd9193dd96d08d0a1fe7ddfa36c456` |
| `scope` | `scope_id=SQS-THC-PH01-E00-B0-SOURCE-READ`、`source_ids=[SST.ALL.W0.BLUEPRINT, SST.W0M.MAIN]`、`consumer_ids=[B1,B2,B3]`、purpose 固定字串 |
| `source_manifest` | `inherited_sha=2012a28f630f4e28d60309de0bb5734ce138b18c677445a475c670f1d9f4245e`、`verification=UNVERIFIED`、`evidence_ref=null`（原件未取得，不得當 ratified） |
| `write_set`/`preimage`/`fin_order` | `[]`／`"N/A"`／`"DENY"` |
| `errors` | `[]` |

**逐 source entry（真值）**

| 欄 | `SST.ALL.W0.BLUEPRINT` | `SST.W0M.MAIN` |
|---|---|---|
| `source_ref.locator` | `…\藍圖\SST_PLP_PH01_W0_全批次藍圖.md` | `…\SST_PLP_PH01_ALL_WNM_2026-11-24_r2\SST_PLP_PH01_W0M_實質正文.md` |
| `namespace` / `source_version` | `SST/SQS-THC/PH01/P1-W00M` / `2026-11-24_r2` | 同 |
| `sha` | `dd37a40b112bf5aac379adb44285ec01409519f7af64418298375833859d01a1` | `5670990d8f0faa571e21460919b4afd8c681396340583b47ed36a8a3b787da96` |
| `byte_length` | 457,294 | 311,983 |
| `encoding` | `UTF-8` | `UTF-8` |
| `clause_span` / `clause_sha` | `[572,579]` / `77132f0636e30b0cf8d5df1ae3438228b18d847d718e5ffbf5c56825229f9bf6` | `[295,307]` / `4f0db2cb1d7c…` |
| `original_id`/`child_id` | `REQ-12` / `REQ-12::AUTHOR-SPLIT-01` | 同 |
| `polarity`/`requiredness`/`owner` | `POSITIVE_READ_AND_DEV_DENY` / `AUTHOR_SPLIT_UNRATIFIED` / `PR-07` | 同 |
| `required_fields` (R) | `["read"]` | `["read"]` |
| `observed` (P) | `read="READ 只讀合法來源，不能繼承 DEV 效應。"`、`span=[573,573]`、`value_sha=78a231eaa93d64fed87001426970d5133e89847b3f7668e514d6b0f259798dab` | 同值、`span=[299,299]`、同 `value_sha` |
| `missing` (M=R−P) | `[]` | `[]` |
| `authority` | 14 欄齊；`os_principal=DESKTOP-57EO414\user`；`rights_check_ref`/`revocation_check_ref`＝Owner 視窗收據與 `window.json#state`；`checked_at=2026-11-25T12:57…+08:00`；`valid_from=12:11:29+08:00`；`expires_at=20:11:29+08:00`；`epoch_strategy=LIVE_REVALIDATE`；`disclosure=LOCAL_ONLY` | 同 |
| `acl_epoch`/`rights_epoch` | `null`／`null`（本機無 provider 版本化服務，依 §02.F 以 `LIVE_REVALIDATE` 承擔；非降級逃驗） | 同 |
| `provenance` | `requirement_ref`＝該來源、`requirement_sha`＝該來源 raw SHA、`requirement_span`＝上列 span、`rule_ref`＝`00_PREFLIGHT/required_set_req12_read_all_2026-11-25.json`（SHA `50ca45c106bb…`） | `rule_ref`＝`…_w0m_2026-11-25.json`（SHA `bc7afa530677…`） |

## 3｜B1／B2／B3 各自接收條件（同版三端最小修訂）

| Consumer | 必驗（不得由 B0 代做） | 本次實況 |
|---|---|---|
| **B1** | 共同 envelope、`source_ref`/`sha`/`authority` 必有、`acl_epoch`／`rights_epoch` 欄存在可 null、原 R/P/M 與 tuple、自身 RepoRoot/commit/BASE/Kernel/FDA | **已真接收 ACCEPTED**（`60_B1/receipts/b1_receipt_r4_2026-11-25.json`，`snapshot_sha=82640619aa80…`）；B1 自身技術前置仍未取證 |
| **B2** | 同上；Q1–Q4 自身 requiredness 不由 B0 推論 | **已真接收 ACCEPTED**（`b2_receipt_r4_2026-11-25.json`，同 snapshot）；Q1–Q4 未建 |
| **B3** | 同上＋`missing` 必有；另需 B2 `ToolReadSet`；只有其合法 Writer 可持久 ledger | **已真接收 ACCEPTED**（`b3_receipt_r4_2026-11-25.json`，同 snapshot）；ToolReadSet／ledger 未建 |

接收演算法（`§03.2` 六步）仍是唯一路徑：鎖 envelope → exact tuple／scope／pin → 用自身可信權利入口重驗 usage／身份／時效／撤權（有 provider epoch 比 current，否則 live revalidate）→ 從原 RequiredSetSpec 重取 R 比對 P/M → 只取真正需要且齊全的 entry → 回傳含 consumer_id、驗證器/version、accepted/rejected、FirstFail 的**真結果**。**聊天 ACK 不算**。

## 4｜交付載點與發布

- 本地（真路徑）：`C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\`
  - `SST_PLP_PH01_W0_B0_CLOSEOUT.md`、`SST_PLP_PH01_W0_B0_HANDOFF.md`（本輪分檔交付；舊 `SST_PLP_PH01_W0_B0_CLOSEOUT_HANDOFF.md` 保留為歷史，不覆寫）
  - 程式／測試：`20_DEV/b0_reader`（11 模組）、`20_DEV/tests`（10 檔含 `trust_fixture.py`，132 案）
  - 規則／接線：`00_PREFLIGHT/`（descriptor + 2 份 RequiredSetSpec）
  - 證據：`40_OPS/`（dev0 基線、五個真跑 raw、freeze）、`30_VERIFY/`（checkpoint、lamp probe、checker 收據）
- 遠端：見 CLOSEOUT 發布段（同批增量上推 `shw097-team/SQS-THC_MVP`；只放可公開內容，`authorization_ref` 等以本地 locator＋SHA 表示，不含口令／raw 權利證據）。

## 5｜B0→W0M 實證反饋（不改上位 active pin）

| 項 | 可泛化原則 | 不可泛化特例 |
|---|---|---|
| 來源身份 | 一來源一 entry、`sha`＝單源 raw bytes SHA；clause 只認原 bytes slice（CRLF／CR／LF 不先正規化） | 本批兩個來源皆 LF 檔；CRLF 只由工程 fixture 驗證 |
| 權利 | OS 可讀 ≠ 資料可用；`RIGHTS_*` 不 retryable；`LIVE_REVALIDATE` 必須在 ROOT／RETURN／接收前各驗 | 本機無 provider epoch 服務，`acl_epoch/rights_epoch=null` 只在「原義證無此服務」時成立 |
| 錯誤碼 | FirstFail 次序固定（Invocation→Root/權利→Bytes→Fields→Return），typed code 不得塌陷成單一通用碼 | `SOURCE_UNAVAILABLE` 的真暫態重試成功面未測 |
| 無寫 | 產品只暫態回傳；證據寫入必須另分 principal／path／effect | 本輪無寫觀測以 W 樹與 K 來源根 size+mtime＋無 `__pycache__` 為限，非全碟保證 |
| 接線 | 可信 context 由受權內部接線建立並釘部署 pin；caller 不得自授權 | 本機以同一 OS principal 的 ACL 與部署 pin 承擔；`NATIVE_OFF` 的 network/transitive 面未證 |

**受影下一層**：W0M 的 B0 子列可改指本 r4 結果（仍須保留其餘批次原義）；B1/B2/B3 需以同 freeze 接收；未閉合項見 CLOSEOUT §6（H1–H7）。本檔不修改 PH01／W0M 任何 active pin，亦不宣稱 W0 Accepted 或 SourceFreezeRatified。

## 6｜信任錨與 ACL（本輪新增，B1/B2/B3 必讀）

- 部署 descriptor：`W/00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json`，3,612 bytes，SHA256 `b8759ca7f5c213024c4046db07494cabb355d39d051b0082ff043845e9fb45e0`，`native_entry.py` 內固定常數。
- 該目錄 ACL 已收緊（只授 `DESKTOP-57EO414\user`、`SYSTEM`、`Administrators`）；`require_sealed` 只套 descriptor 與其直屬父目錄，祖先仍做 reparse／identity。日後搬動 descriptor 或改 ACL，產品會 fail closed（`TRUST_CONTEXT_UNBOUND`／`PATH_IDENTITY_UNVERIFIED`），並需重 freeze。
- 來源檔（K）不要求 sealed；其安全由「當次 OS token 讀取權＋同 handle 身份＋讀後 hash／identity 複核」承擔。此分界為刻意設計，不得為求綠燈互換。

## 8｜B1/B2/B3 真實接收入口（可重跑）

```text
cd W/60_B1
python -B -m b1_consumer.cli receive \
  --envelope ../40_OPS/ops_r4_h_pos.raw/stdout.txt \
  --context b1_receive_context_2026-11-25.json \
  --out receipts/b1_receipt_r4_2026-11-25.json
```

- `B2`／`B3` 只換 `--context b2_receive_context_2026-11-25.json`／`b3_receive_context_2026-11-25.json`，其可信權利入口與判定各自獨立（不可互代）。
- 收據欄位：`consumer_id`、`verifier_version`、`snapshot_sha`、`candidate_digest`、`accepted[]`（source_id／sha／clause_sha／R／P／M）、`rejected[]`、`errors[]`、`rights{receipt_sha,state_sha,window_id}`、`verdict`。
- 負例測試：`cd W/60_B1 && python -B -m unittest discover -s tests`（15 案）。
