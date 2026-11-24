# SST_PLP_PH01_W0_B0｜CLOSEOUT / HANDOFF

- artifact_id: SST-PH01-W0-B0-CLOSEOUT-HANDOFF-20261124-R2
- subject: `SST/SQS-THC/PH01/E00`｜OriginalWave `P1-W00M`｜BID `0`｜FUO `SourceReadSet`、`SourceErrorEnvelope`
- effect_intent `SOURCE_READ`｜product WriteSet `[]`｜preimage `N/A`｜`FIN_ORDER=DENY`
- **status: `B0_ENGINEERING_COMPLETE / PRODUCT_NOT_EXECUTED`**（工程報告標籤，非 canonical verdict）
- 四 Ready：Draft `AUTHOR_DOCUMENT_WITH_TYPED_MISSING_ONLY`；Atom `false`、Execute `false`、Accept `false`
- 產品：`product_actual=NOT_EXECUTED`、`expected_world_raw=EXPECTED_NOT_OBSERVED`；無原 Reader/Consumer ACK、無 R16
- 分帳：本根僅 B0；非 SQS-THC 工程（車道修復）在 `C:\Projects\Agent_Workspace\FHS_NEXT_Workspace\LANE_REPAIR_20261124\`

---

## SST_PLP_PH01_W0_B0_CLOSEOUT

### C01｜來源與 pin（本輪重核，byte-equal）

| 錨 | SHA-256 | bytes |
|---|---|---|
| `SST_PLP_PH01_W0_全批次藍圖.md` | `dd37a40b112bf5aac379adb44285ec01409519f7af64418298375833859d01a1` | 457,294 |
| `SST_PLP_PH01_W0_B0_藍圖_實質正文_2026-11-24_r2.md` | `93f49dc8bde3f32133ac3b69e04a6e5c58292a0d780141d8de07ffe626fcb90c` | 45,229 |
| B0 證據型附錄 r2 | `197d1b997c4b927421044e18b70e0eeac02d9bfaa726fe87fd9555262b3a0886` | 54,880 |
| 全批次最小執行控制包 r1 | `063bb31591a2508a271c2f7a88ca7e8c260a3e194453f8815936175027baa6f0` | 50,879 |
| B0 執行控制小包 r2（本件操作正文，首釘） | `1117efe048943f0bec2e82bb667b7b2251e2f8e54470086bef660d42078a5ada` | 60,116 |

`F-01 LOCATOR_DRIFT`：B0 正文引用的 `…\SST_PLP_PH01_W0_B0-m\…` 在本機不存在；同名同 SHA 實體位於 `…_B0-B8\…`。以 SHA 判同一性，未換版。證據 `00_PREFLIGHT/source_pins_measured.json`。

### C02｜車道（前置，FHS 工程，已分帳）

| 項 | 修復前 | 修復後（Owner 授權「授權修復」） |
|---|---|---|
| Codex pin | `9e1da794…`/0.167.0-alpha.4.1 不存在（`ERR_LANE_TOOLCHAIN_BINARY_MISSING`, exit 3） | `c38161ad8494f88c`/0.169.0-alpha.11.1，`094d4db4…`，`--verify` exit 0 |
| Hermes 路徑 | `…\Packages\OpenAI.Codex_…\…\hermes-agent` 不存在（`ERR_ISOLATED_HOME_MISSING`, exit 1） | `%LOCALAPPDATA%\hermes\hermes-agent`（v0.23.3 `caafe5389ae5`） |
| opencodex root | `%LOCALAPPDATA%\HG-KSEOS\runtime\opencodex-2.11.0` 不存在 | `%APPDATA%\npm\node_modules\@bitkyc08\opencodex`（2.11.0） |
| relay / front door | 10101、10100 未監聽 | 兩者 `/healthz` 200；sanctioned pair `opencode-go/deepseek-v4.1-flash` |
| active-policy | 指定舊樹檔案 `a3df95…`（15111B），digest 永不符 | 重新指定現行 `5466e064…`（16199B），保留原 order_text，`supersedes` 記舊值 |

證據與 preimage：`FHS_NEXT_Workspace\LANE_REPAIR_20261124\`（`LANE_REPAIR_20261124.json`、`preimage/`、`*_probe.json`、`README.md`）。
已知殘留：三車道同模型 → model-axis SoD `ABSENT / OPEN_OWNER_ORDERED`；`ERR_LANE_NOT_ADMITTED` 仍載於 11-16 記錄；VERIFY_SECURITY 之 rank1 `openai-codex/gpt-6.1-sol` 為 401，本輪以 `--require-arm` 選定 deepseek，未改 registry rank。

### C03｜DEV ECP（Maker 候選）

- 施工者：EXECUTE 車道（Codex CLI），receipt `20_DEV/exec_build_receipt.json`（`bb0ad7cb…`）：`ok=true, served_arm=opencode-go/deepseek-v4.1-flash, usage 200, nonce=true, 607s`。
- 產物（15 檔，freeze `40_OPS/candidate_freeze.json`，tree `397d1ecaec6a7909…`）：
  `b0_reader/{__init__,errors,root,bytes_,fields,return_,controls,cli}.py`＋`tests/test_b0_{root,bytes,fields,return,cases}.py`＋`RUN_TESTS.cmd`＋`WORKORDER_B0_DEV.md`。
- 四 Op 對映：`B0.ROOT`→`root.check_root`（realpath containment／逐層 reparse／ADS／`icacls` ACL／namespace·version）；`B0.BYTES`→`bytes_.read_bytes`（strict UTF-8、raw SHA、CRLF 保留的 clause span/sha）；`B0.FIELDS`→`fields.split_fields`（R/P/M，M⊆R、P∩M=∅、R 不刪）；`B0.RETURN`→`return_.build_read_set`（`write_set=[]`、逐 ref 分帳、不開寫入檔）。
- 作者控制面：`controls.evaluate` 只做作者文件界線判定，非原 CaseRegistry。

### C04｜OPS ECP（工程證據，非產品 Raw）

- 蒐集器 `40_OPS/collect_evidence.py`；輸出 `40_OPS/ops_run.json`（`3a116e4c…`）。
- 實跑：`python -m unittest discover -s tests -v`（cwd `20_DEV`）→ **exit 0、59 tests OK、0.57s**；跑前後 tree `397d1eca…` 不變（read-only 成立）。
- 界線：`claim_ceiling=ENGINEERING_EVIDENCE_NOT_PRODUCT_RAW`；無原 Runner/RawSchema，故不構成產品 OPS Raw。

### C05｜TQAEP（獨立 checker，兩輪）

| 輪 | receipt | 結果 |
|---|---|---|
| R1 | `30_VERIFY/verify_receipt.json`（`d07cfdb4…`），session 1 690s | **21 PASS / 1 FAIL**：`build_read_set_complete` 缺 top-level `write_set`（`return_.py:171`）→ 真缺陷 |
| 修補 #1 | `20_DEV/exec_repair1_receipt.json`（`e63ab597…`），EXECUTE 車道 69.9s | `return_.py:178` 加 `"write_set": []` 與斷言；Maker 測試同步 |
| R2 | `30_VERIFY/verify_round2_receipt.json`（`d4268105…`） | **22 PASS / 0 FAIL**；delta：case 14 轉 PASS，其餘不變 |

- findings：`30_VERIFY/findings.json`（R1，`234c4ed8…`）、`30_VERIFY/findings_round2.json`（R2，`445277f5…`），含 `provenance`（checker 為 read-only sandbox，JSON 由其訊息內嵌、Commander 原樣落檔）。
- `candidate_tree_sha256` 差異說明：checker 自算 `65e6661a…`（其 15 檔集合與排序），本報告 canonical freeze 為 `397d1eca…`（`40_OPS/candidate_freeze.json` 定義，排除 receipt／attempt log／`__pycache__`）。兩者為**不同定義**的樹雜湊，不可互比。
- Harness 觀察（非候選缺陷）：checker 環境曾報 `No usable temporary directory found`，致其執行 Maker 套件時 33 個 setup error；同一套件在 Commander 環境 exit 0。記為環境差異，未據此判候選 FAIL。

### C06｜逐 Case 結果（Maker 22 個 CaseID 測試全綠；checker 22 點 oracle 全 PASS）

| CaseID | 期望 FirstFail | Maker | Checker |
|---|---|---|---|
| `B0.POS.REQ-12__AUTHOR-SPLIT-01` | `NONE_IF_VALID` | PASS | PASS |
| `B0.NEG.REQ-12__AUTHOR-SPLIT-01.DELETE_CHILD` | `AUTHOR:TRACE_ORPHAN` | PASS | PASS |
| `B0.NEG.REQ-12__AUTHOR-SPLIT-01.DELETE_NEG` | `AUTHOR:NEG_MISSING` | PASS | PASS |
| `B0.NEG.REQ-12__AUTHOR-SPLIT-01.FIELD_read` | `AUTHOR:CHILD_RULE_HOLD:REQ-12::AUTHOR-SPLIT-01` | PASS | PASS |
| `B0.POS.AUTHOR_SOURCE_AUTHORITY` / `B0.NEG.…` | `NONE_IF_VALID` / `AUTHOR:SOURCE_AUTHORITY_HOLD` | PASS | PASS |
| `B0.POS.AUTHOR_CONTROL_SCHEMA` / `B0.NEG.…` | `NONE_IF_VALID` / `AUTHOR:CONTROL_SCHEMA_HOLD` | PASS | PASS |
| `B0.POS.AUTHOR_FOUR_READY` / `B0.NEG.…` | `NONE_IF_VALID` / `AUTHOR:FOUR_READY_HOLD` | PASS | PASS |
| `B0.POS.AUTHOR_READ_WRITE_SCOPE` / `B0.NEG.…` | `NONE_IF_VALID` / `AUTHOR:READ_WRITE_SCOPE_HOLD` | PASS | PASS |
| `B0.POS.AUTHOR_UNKNOWN_UNDO` / `B0.NEG.…` | `NONE_IF_VALID` / `AUTHOR:UNKNOWN_UNDO_HOLD` | PASS | PASS |
| `AUTHOR.EXEC.C01.SUBJECT` | `AUTHOR:SCOPE_MISMATCH` | PASS | PASS |
| `READ_WRITESET/DEV_EFFECT` | `AUTHOR:EFFECT_UNBOUND` | PASS | PASS |
| `CLAIM_QUALIFIED` | `AUTHOR:CLAIM_CEILING_DENY` | PASS | PASS |
| `AUTHOR.READSET.ONE_MISSING` | `NONE_IF_VALID`＋`missing=[x]` | PASS | PASS |
| `AUTHOR.READSET.COMPLETE` | `NONE_IF_VALID`＋`missing=[]`＋`write_set=[]` | PASS（修補後） | PASS（R1 FAIL→R2 PASS） |
| `AUTHOR.READSET.DROP_REQUIRED` | `AUTHOR:TOOL_REQUIREDNESS_HOLD` | PASS | PASS |
| `SEC.PATH_ESCAPE` | `PATH_ESCAPE` | PASS | PASS |
| `EDGE.STALE_EPOCH` | `NAMESPACE_MISMATCH` | PASS | PASS |

### C07｜未閉合（不因綠燈關閉）

| ID | 內容 | Owner | Resume predicate |
|---|---|---|---|
| `BR.B0.READER` | OriginalReader callable/version/argv/ABI | 原 Source／PH00 Reader | 同 tuple 原 Reader 可解析 `ReadSetRef`，給實際 exit/raw |
| `BR.B0.EFFECT` | OperationType/EffectRegistry/receiver/permission | 原 EffectRegistry Owner | 原 enum 可解析且同 scope 適用 |
| `BR.B0.SCHEMA` | ReadSet/Raw schema、`$id`、roundtrip 向量 | 原 schema Owner | 已知 schema roundtrip，禁 extra 不放行 |
| `BR.B0.RUNNER` | CaseRegistry／Runner／POS-NEG fixture／原 RawSchema | 原 Case/Oracle Owner、R16 | 每 Case 可重開同 tuple 原 POS 與單變異 NEG |
| `BR.B0.AUTH` | issuer/permission ref、scope、expiry、epoch、撤銷 | 原 Policy/Issuer | 原授權 locator+raw SHA；**本輪未開 Owner 窗、未輸入口令** |
| `BR.B0.SCOPE` | `acl_epoch`／`rights_epoch` 實值 | 原來源 Owner／Rights Reader | 每來源真 scope/rights，同 epoch |
| `U02.CHANNEL` | 合法持久接收通道與原 ACK | 原 Artifact Store/Consumer | BIND_INTEGRATION，精確 tuple 回讀 |
| `LANE.ADMIT` | `ERR_LANE_NOT_ADMITTED`、同模型 SoD | Policy/Registry Owner | 原 guard 給 ADMITTED 或 Owner 明文裁決 |
| `PUB.GHP-02` | 公開交付 admission | 原 Publisher/Owner | GHP-02 就位 |

LastGood：pin 五項＋freeze `397d1eca…`＋R2 findings。修補計數：finding 1 用 1/2 次（有實質 delta）；無 `PARK_UNTIL_DELTA` 項。

---

## SST_PLP_PH01_W0_B0_HANDOFF

### H01｜給 B1 的可接收介面（現況：不可宣稱 ReadyExecute）

B0→B1 必須同 subject/scope/version/pin/epoch 的 `SourceReadSet` wire，mandatory `source_ref, sha, acl_epoch`，經原 Reader 通道回傳並由 B1 readback。
本輪 `build_read_set` 已產出契約形狀（`source_ref/source_sha/clause_span/clause_sha/required_fields/missing_fields/observed/locator`＋`write_set=[]`），但 `acl_epoch`／`reader`／channel 為 `null`／本地字串 → **不得**當 B1 正式輸入，只可作 ReadyDraft 與介面預演。
B2 同三欄；B3 需 `source_ref, sha, authority, missing`。

### H02｜可直接重用的命令與 ref（本輪實測）

| 用途 | 命令 | 實測 |
|---|---|---|
| 車道 pin 驗證 | `python C:/Projects/Agent_Workspace/FHS_NEXT/HG-KSEOS/scripts/hgk-lane-toolchain.py --verify` | exit 0，0.169.0-alpha.11.1 |
| relay / front door | `scripts/start-hgk-hermes.ps1 -Action StartOpenCodex`；`python scripts/hgk-exec-model-frontdoor.py --declaration config/hermes-codex-lane.json` | `/healthz` 200；sanctioned pair |
| EXECUTE 派工 | `hgk-lane-dispatch.py --lane EXECUTE --require-arm opencode-go/deepseek-v4.1-flash --codex-home %LOCALAPPDATA%/HG-KSEOS/codex-hermes --cwd <W>` | 需帶 `--nonce`，否則是 `ERR_NO_ARM_EMITTED_NONCE` |
| 獨立驗收 | 同上，`--lane VERIFY_SECURITY --require-arm …` | 不帶 arm pin 會落 401 的 `gpt-6.1-sol` |
| Maker 測試 | `cd 20_DEV && python -m unittest discover -s tests -v` | 59 OK |
| OPS 證據 | `python 40_OPS/collect_evidence.py` | exit 0、tree 不變 |

### H03｜恢復條件（全部成立才可升格）

1. `BR.B0.AUTH`＋`BR.B0.SCOPE`：原 Policy/Issuer 給 scope/effect/target/expiry/epoch 與每來源 `acl_epoch`（需 Owner 口令窗口，由本人輸入）。
2. `BR.B0.READER/SCHEMA/RUNNER`：原 Reader、Raw schema、CaseRegistry/fixture 就位，方能由作者候選升為產品 slice。
3. `LANE.ADMIT` 或 Owner 就同模型 SoD 明文裁決；第二人制度若適用，缺獨立簽署即 `SINGLE_HUMAN_POLICY_CONFLICT`。
4. 上述成立後，以原 callable 重跑四 Op 與 22 Case，產品 Raw 由原 Reader 產生（非本報告），才可標 `B0_COMPLETE / B1_READY`。

### H04｜公開交付

- **未建立 repo、未 push**（Owner 未答 GHP-02 授權項）；`SQS-THC_MVP` 無任何遠端動作。
- 憑證檔 `API KEY\GITHUB-REPO_SHW097-4.txt` 存在但**未讀取、未傳入任何客戶端**。
- 若後續授權：僅推 `20_DEV`／`30_VERIFY`／`40_OPS`／本 MD；不含知識庫原文、憑證、口令 envelope、受限 raw。

### H05｜狀態聲明

本件為工程交付報告，非產品 ledger、非原 ACK、非 R18 Release。Maker 綠燈與 checker PASS 只證明「作者候選在作者 oracle 下自洽」；`product_actual` 維持 `NOT_EXECUTED`，`FIN_ORDER=DENY` 不變。未刪除任何原義務，未以完成旗標替代原 Reader 驗收。
