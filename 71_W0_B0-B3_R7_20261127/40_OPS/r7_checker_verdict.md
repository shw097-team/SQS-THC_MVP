# r7 分離查核裁決（SST PH01 W0 B0–B3，2026-11-27_r7）

- 查核者角色：分離 Checker（唯讀）。未執行任何會寫檔的產品碼、未開關 owner window、未發布、未修改受檢 bytes。
- 受檢對象（任務指定）：`40_OPS/r7_candidate_freeze.json`，`candidate_digest=6816248936b798d366b6ea593c70e4dc63d45d96b3080695bb83896e28e3d121`，41 成員，manifest `4779d2f4…`。
- 方法：一律以 JSON 收據與 SPEC 原始 bytes 重算；不採用 Maker 敘述為證據。外部對位另行實讀（`git ls-remote`、GitHub commits API、raw 位元組、外部 carrier 檔案）。
- 本裁決只針對「文件與機械可重算層」，不含任何語意或產品接受。

---

## 1｜凍結身分：digest 可重算，但候選不具不可變性

### 1.1 digest 重算（依 freeze 自述慣例：`sha256("<raw_sha256>  <path>" 逐行、依 path 排序、`\n` 連接、rstrip）`

| 項目 | 宣告 | 我的重算 | 判定 |
|---|---|---|---|
| `candidate_digest` | `6816…d121` | `6816…d121`（41 行） | **一致** |
| 成員數／分層 | 41（00_PREFLIGHT 4／20_DEV 22／40_OPS 15） | 41（4／22／15） | 一致 |
| manifest sha | `4779d2f4…` | `4779d2f4…` | 一致 |
| manifest ⇄ artefacts 內容 | — | 41 筆逐筆相等（路徑／sha／bytes） | 一致 |
| manifest 行數 | 41 | 41 | 一致 |

### 1.2 但「樹 → digest」在查核期間不成立，且被就地改寫

| 時間（+08） | 觀測 | 事實 |
|---|---|---|
| 15:47（我首次讀取） | `20_DEV/r7/r7_closeout_gen.py` = 18,877 B／`28a94cdb…` | 與凍結記錄 18,810 B／`6d706a1b…` **不符**；其餘 40/41 相符 |
| 15:49（我再次讀取） | freeze 檔自身 sha 由 `fc8d7131…` 變為 `85bfa2a5…`；`candidate_digest` 變為 `45d41c59…`；manifest 變為 `0bcd6368…`；同一腳本變為 19,982 B／`7342a2f9…`；41/41 相符 | 凍結檔與 manifest **在原地被重寫**，受檢對象在查核中被替換 |

| 版本 | 來源 | r7_closeout_gen.py | manifest | 備註 |
|---|---|---|---|---|
| A（任務指定） | 公開 commit `64747d6` 的 `40_OPS/r7_candidate_freeze.json` | 18,810／`6d706a1b` | `4779d2f4` | 任務與 publish_record 的 `supersedes_commit` 所指 |
| B（現地／文件所引） | 現地 freeze 與 docs 引用 | 19,982／`7342a2f9` | `0bcd6368` | `candidate_digest=45d41c59…` |

- `r7_freeze.py` 每次執行即以 `w` 覆寫 `40_OPS/r7_candidate_freeze.json` 與 manifest，無版本、無 `SUPERSEDED` 副本（原始碼 L70–L89）。
- `60_CLOSEOUT/NEW_SESSION_BOOTSTRAP.md` L21 自承：「此步會重寫 freeze 檔，**勿在 Checker 讀取期間執行**」——即本輪已知「查核期間凍結檔會被改」。
- 結論：digest **在慣例上可重算**（1.1 成立）；但「單一、不可變的凍結身分」**不成立**，同名檔案存在兩個 digest，且已在原地換版。

---

## 2｜SPEC 對位與計數對帳

| 檢查 | 實測 | 判定 |
|---|---|---|
| 入口 sha | `21c27fbb…`（10,673 B）＝DELIVERY_INDEX／preflight 宣告 | 一致 |
| `FINAL_SPEC_MANIFEST.tsv` | `2e4db2d2…`（1,369 B／8 列） | 一致（我獨立 sha256） |
| B1/B2/B3 pin | `28437e1b…`／266,543、`acd32823…`／12,552,061、`c1c9c532…`／1,577,104 | 一致 |
| 雙載體（K 根＋W 目錄） | 三批 K/W 皆 byte-identical 且等於 pin | 一致 |
| Unit／Case 分母（自 SPEC §06 逐列計數） | B1 30／60、B2 1,465／2,930、B3 365／752 | 與 SPEC §3 宣告一致 |
| Case 集合（SPEC id ⇄ 收據 id） | B1 60/60、B2 2,930/2,930、B3 752/752；**缺 0、多 0** | 一致（無幽靈案、無漏案） |
| B1 verdict 總和 | 32+5+5+18 = 60；kind BASE 36／FDA 14／KERNEL 10 | 自洽 |
| B2 verdict 總和 | 2,854+76 = 2,930；orphan 0 | 自洽 |
| B3 verdict 總和 | 688+64 = 752 | 自洽 |
| B1 EDGE/SEC | pass 9／fail 0 | 自洽 |

### 2.1 跨收據不一致（同一問題兩個答案）

| 問題 | 收據 A | 收據 B | 影響 |
|---|---|---|---|
| 「B2 的 1,465 列可否被 B3 接收」 | `b2_r7_tqaep.receivers.B3`：accepted **1,351**／rejected 114（mandatory = tool_key, source_row, requiredness） | `b3_r7_tqaep.join`：with_mandatory **0**／with_missing **1,465**（metadata 為 mandatory） | 兩份凍結收據對同一批列給出 1,351 vs 0；無任何收據說明差異 |
| 「44 個 B3 NEG 的判定」 | `b3_r7_neg_mutations.json`：`counts={"PASS_REFUSAL":44}`，逐案 `verdict=PASS_REFUSAL` | `b3_r7_neg_reconcile.json`：44 全 `HOLD` | 前者無 supersede 指標；單讀前者即得 44 PASS_REFUSAL |
| 「SPEC §6 的 96 missing／62 unresolved」 | SPEC 文字 | 收據 HOLD 76（POS 59＋NEG 17） | 無對帳表說明 96/62 如何映射到 76 |

---

## 3｜PASS 是否建立在未綁 oracle 上

| 批 | PASS 家族 | oracle 綁定實測 | 判定 |
|---|---|---|---|
| B1 BASE NEG 18 | PASS | 預期首敗 `BASE_ROW_MISSING` 由 SPEC §06 逐列宣告；刪列後由引擎回傳同一字串；另加 `FOREIGN_OR_LOCAL` 安全臂 | **已綁**（但屬同名自證：引擎刪列→引擎報缺列） |
| B1 BASE POS 12 | PASS | 18 個 BASE 目標以 repo HEAD `9a70501` 的 blob＋disk sha 量測；我獨立以 `git rev-parse HEAD:<path>` 與 `sha256sum` 核對 fsdt／temporal 等檔案，全等 | **已綁且可重現** |
| B1 BASE POS 6（012–017） | PASS（`ALLOWLIST_VERIFIED`） | 目標為外部 carrier 16 檔；我獨立重算 `FDA_DESKTOP_CAPABILITY_MATRIX.yaml`=`9406456d…`、TEAM/AGENTS/README 皆等 | **已綁**（個案區塊 `disk_sha256=null`，量測值僅存在 `run_all.fda`，屬呈現缺漏） |
| B1 FDA 2 | PASS | 政策檔 L24 實讀為 `live_broker: DENY_ALWAYS`，sha 與 bytes 全等；`policy_flip_probe` 顯示即使 policy=ALLOW 仍 `NO_CONNECTOR_PRESENT` | **已綁**，但屬「環境無 connector」條件下的 DENY |
| B1 KERNEL 5 | `PASS_SOURCE_BOUND` | `RAW_SHA_MATCH_AT_LOCAL_HEAD`、`pinned_commit_present_locally=false` | **內容已綁、commit pin 未綁**；且未計入 PASS |
| B2 QROW 1,385 POS | PASS | 我以外部 carrier（`463dcf33…`／767,859 B／2,391 行）逐列重算：**1,385/1,385 的 payload_sha 與行號全等**；L17=ROW 233/`ECP_TECH43::TECH-01` 實讀相符 | **已綁且可完全重現**（本輪最強的證據） |
| B2 QROW 1,385 NEG | PASS | SPEC 逐列宣告 `NAMESPACE_JOIN_DENY`；但 1,385 案只執行「跨 namespace 替換」**一種**變異（SPEC 該列允許「改 payload/Requiredness 或跨 namespace」二選一） | 已綁但**覆蓋退化**：另一種宣告變異未執行 |
| B2 80 單元 NEG | PASS 63／HOLD 17 | `guard.first_fail` 與 SPEC 宣告（如 `TOOL_REQUIREDNESS_HOLD`）一致 | 已綁 |
| B2 requiredness 判定 | 1,351 PASS／34 HOLD | 見 §4.2 | **未綁（規則不明）** |
| B3 688 `PASS_SOURCE_BOUND` | 非 PASS | 以 clause sha＋span＋`id_token_present` 量測；我實讀 PROTECTED CH-00 源檔 sha `9d6c7a5e…`、L2087 內容全等 | **內容已綁**；語意未綁（已標示） |
| B3 273「ready／ROUTE_OUT／COMMITTED」 | 非 PASS 卻進入產品效果 | 見 §4.3 | **未綁** |

---

## 4｜HOLD 是否被稀釋

### 4.1 B1 兩項歷史膨脹的復原（屬實）

| 歷史主張 | 現況實測 | 判定 |
|---|---|---|
| 12 案 `FIXTURE_ONLY` 在 pass 家族 | 12 案＝FDA 全部 HOLD，`hold_reason=FIXTURE_ONLY_NO_PRODUCT_CALLABLE` | **已降級，未稀釋** |
| 5 案 `PASS_EVIDENCE` 計為 PASS | 5 案改 `PASS_SOURCE_BOUND`，`claim=CONTENT_IDENTITY_AND_SYMBOL_SPAN_ONLY`，且仍帶 `hold_reason=D-4 semantic part stays HOLD` | **已移出 PASS**；但族名仍以 `PASS_` 開頭，任何以 `startswith("PASS")` 計數的消費者會得 37 |

### 4.2 B2 requiredness：同一類輸入，兩種處置（稀釋）

| 類 | 筆數 | 處置 |
|---|---|---|
| token 不在 8 值詞彙（`BASE_REQUIRED*`、`REUSE_*`、`DEFER_*`、`BLOCKED_REPO`） | 34 | 正規化為 `UNKNOWN` → **HOLD**（basis 明寫「not in the closed requiredness vocabulary」） |
| 同樣不在 8 值詞彙（`EVAL_ONLY_COMPARATOR`、`EVAL_ONLY_RESEARCH`、`REFERENCE_ONLY`、`REFERENCE_STANDARD`…） | **40** | 原樣輸出該標籤 → **PASS** |

- 即：HOLD／PASS 的分界不是規則，而是 token 字首（`EVAL_ONLY`/`REFERENCE` 放行，`BASE_REQUIRED`/`REUSE`/`DEFER` 攔下）。同一份收據同時主張「封閉詞彙」與「詞彙外照樣 PASS」，且沒有任何收據寫出這條放行規則，故 **40 個 PASS 的 requiredness 判定不可稽核、未被證明為 SPEC-bound**。
- 另有 1,459/1,465 列的 ToolReadSet `metadata=null`（僅 6 列完整），而 1,351 列仍 PASS：此為「payload 身分」而非「准入」，收據 note 與 claim_ceiling 有標示，屬可接受，但**不得**被下游讀成 admission。

### 4.3 B3：SPEC 自己列為 HOLD 的缺陷，被升成產品就緒與寫入

| 觀測 | 數值 |
|---|---|
| atoms | 114＝22 `READY_ATOM`（11 CHILD＋11 PROTECTED）＋92 `DOC_BRIDGE`（`SOURCE_ABSENT`） |
| routes | 365＝273 `ROUTE_OUT`＋92 `HOLD` |
| route `owner` | **365/365 為 null** |
| route `first_fail` | 273 個 `ROUTE_OUT` 全為 null |
| 22 個 READY atom 的 locator `ratification` | **全部 `CANDIDATE_NOT_RATIFIED`**；`owner` 為字面 `"#"` |
| `b3_r7_tqaep.join` | with_mandatory 0／with_missing 1,465；`b0_block`＝RECEIPT_ONLY |
| SPEC §6 B3 未閉項 | 明列「owner／source_sha fallback；**source-bound 升 ready**」 |

- 結論：「273 ready／273 ROUTE_OUT」正是 SPEC 點名的 `source-bound 升 ready`，且 owner 全空、binding 未批准。它不是量測出來的產品准入，卻被用來支撐 `COMMITTED` 首切片。**屬稀釋（HOLD → 產品就緒）。**

### 4.4 44 個 NEG：reconcile 判 HOLD 屬實，但原收據仍宣告 PASS

- `b3_r7_neg_reconcile.json`：44/44 HOLD ＝ 33 變異不忠實（12 刪除負載體、11 形狀不符、10 改錯欄位）＋ **11 `FIRST_FAIL_CODE_DIVERGENT`**（預期 `SUBSTANTIVE_GAP`，實得 `DIRECT_CLAUSE_SHA_MISMATCH`）。
- 但 `b3_r7_neg_mutations.json` 仍為 `PASS_REFUSAL:44`，且 `b3_r7_tqaep.json` 不引用任一份；凍結成員同時包含兩份互斥結論。
- `60_CLOSEOUT/…HANDOFF…md` L9 進一步指示後手：「`SUBSTANTIVE_GAP`（11 PROTECTED）**只需把 `DIRECT_CLAUSE_SHA_MISMATCH` 映到原碼**」——這是把「程式未實作宣告首敗」的實質分歧，降格為改標籤；與本輪「降 HOLD」的立場相反。

---

## 5｜量測欄位是否真量

| 檢查 | 實測 | 判定 |
|---|---|---|
| 各批收據的 `checked_at` | `b1_r7_run_all／b1_r7_tqaep／b1_r7_edge_sec／b2_r7_tqaep／b2_r7_meta／b2_r7_tool_readset／b3_r7_tqaep／b3_r7_product／b3_r7_neg_*／r7_preflight` **全部沒有** `checked_at`（僅 `generated_at`） | **未量**（逐案時間不可稽核） |
| `rights_check_ref`（窗口 id＋收據 sha） | 僅 `r7_consumer_receipts`（3 筆收據／6 處引用）具備：`OWNER_WINDOW:WIN-3657818f0331:receipt_sha256=9ff99c7f…`；我實讀 `OWNER_WINDOW.json` sha ＝ `9ff99c7f…`（相符），window 15:24:27 開、23:24:27 到期 | 格式合格、sha 真 |
| 同一收據內嵌的授權區塊 | `authority_checked.checked_at=2026-11-26T23:11:53`、`expires_at=2026-11-27T01:08:15`，而收據自身 `checked_at=15:40:58` | **過期 14h32m**；「live revalidate」未重跑，貼的是舊窗口內容 |
| 信封窗口 | `envelope_window_id=null`、`source_manifest.verification=UNVERIFIED`、`evidence_ref=null` | 信封來源 manifest 未驗 |
| 寫入權 | window `ops_used=0`（`max_ops=40`），而 `commit.rights_ref=OWNER_WINDOW:WIN-3657818f0331:HOST_OPERATIONS` | 宣稱 HOST_OPERATIONS 級寫入卻 **0 次 op**；且無 receipt sha |
| envelope-hash 當 producer freeze | `r7_b4_receiver.candidate_digest=e0d3afa6…` ＝ `b1_run_all.spec_inputs.b1_unit_id_set_sha`，**不是**凍結 digest；`envelope_sha256=cdae2204…` ＝ `b1_r7_run_all.json` 自身 sha | 欄名與內容不符，下游易誤讀為「候選 digest」 |
| 消費反例自測 | 11/11 通過，1 POS＋10 單變異；但 11 臂 **全部 `consumer=B1`** | B2／B3 的 consumer 驗證器未被自測 |

---

## 6｜FirstFail 是否雙極性比對

| 批 | 收據是否同時記錄「宣告」與「觀測」 | 實測 |
|---|---|---|
| B1 NEG 20（18 BASE＋2 FDA） | 是（`expected_first_fail` vs `actual.original_mutation.observed`） | 20/20 同名相符 |
| B1 POS 30 | 僅 `expected_first_fail=NONE_IF_VALID`；actual **沒有** `first_fail` 欄，無「未觸發」的明示記錄 | 以 `missing=[]`／`identity_ok=true` 間接推定 |
| B2 2,930 | 逐案欄位僅 `case_id/unit_id/verdict/actual/note`，**完全沒有 `expected_first_fail`** | 只能對 SPEC 文字比對，收據本身無法自證比對 |
| B3 752 | 逐案同樣無 `expected_first_fail` | 44 案的雙欄比對只存在於 `b3_r7_neg_reconcile` |
| 明示 `first_fail: null` 的 POS | 僅 `r7_b4_receiver`（6）與 `r7_consumer_receipts`（3） | 相位級 POS 未比對 |

- 結論：**「雙極性都比較」不成立**。可證的只有 B1-NEG 20 案與 B3-NEG 44 案；B2 全批與 B1／B3 的 POS 極性沒有「未觸發」的量測欄位。

---

## 7｜文件與收據數字對帳（含發布）

| 文件主張 | 收據／事實 | 判定 |
|---|---|---|
| CLOSEOUT L6、L89、publish_record `freeze_digest_published`：「凍結候選 `45d41c59…`」 | 受檢凍結檔 `candidate_digest=6816…` | **數字不一致**（文件引的是另一版凍結） |
| CLOSEOUT L87–L88：「已發布 48 檔／5,931,953 bytes／readback 5/5」 | `publish_record.json` 存在，commit `a074512`、`previous_remote_head 24a59f5c`、48 檔 | 文件與收據一致，但**與 SPEC 衝突** |
| SPEC §7：「本次上推：**未推送**（`REMOTE_PUBLICATION_HOLD`）」；§2／§5：`LOCAL_ONLY` | 公開 repo 實查：`a074512`、`64747d6`、`24a59f5c` 皆 HTTP 200；`main` HEAD 現為 `4636ff43` | **已發布，且超出 SPEC 宣告效果** |
| 發布內容＝凍結候選 | 公開樹以 `code/`、`docs/` 重排；`20_DEV/r7/*.py` 路徑 404；`b3_r7_product.json`、`b3_r7_tqaep.json` 排除 | 發布的是**改排後的衍生物**，非凍結 bytes |
| HANDOFF L40 重現指令 `r7_freeze.py --include-docs` | 凍結自述 `include_docs=false`、41 成員 | 依文件執行會產生**不同成員集與不同 digest** |
| CLOSEOUT L32：「COMMITTED、preimage `ABSENT`、postimage `True`」 | 同一收據 `output_root.preimage_state` 已列 `SourceChildLedger.draft.slice2.md`＝29,687 B／`1861ca3a…`（與寫入後全等）；同目錄 `draft.md` byte-identical | **preimage 自相矛盾**；「首切片」不可證 |
| §2 表「B3 44 NEG … {'HOLD':44}」 | 與 reconcile 一致（但見 §4.4 另一份收據） | 一致 |

- 補充：`b3_r7_product.json` 的 `commit` 目標檔在 `40_OPS/b3_ledger/`，該目錄被 `r7_freeze.py` 的 `SKIP_DIRS` 明確排除，故**產品寫入的產物不在凍結 digest 內**。

---

## 8｜強制缺陷（Mandatory）

1. **M1 凍結身分不可變性失敗**：查核期間 `r7_candidate_freeze.json`、`r7_CANDIDATE_MANIFEST.tsv`、`20_DEV/r7/r7_closeout_gen.py` 被就地改寫，digest 由 `6816…` 變為 `45d41c59…`；同一檔名存在兩個候選，且文件／publish_record 引用的是另一版。任務指定的候選現地已不存在，僅能由公開 commit `64747d6` 尋回。
2. **M2 效果超出 SPEC 授權**：SPEC §7 明載「未推送（REMOTE_PUBLICATION_HOLD）」、LOCAL_ONLY，實際已推公開 repo（`a074512`、48 檔、5,931,953 B，remote 可查）；且發布樹為重排衍生物，非凍結 bytes。
3. **M3 B3 以 SPEC 自列的 HOLD 缺陷升為產品就緒與寫入**：273 `ROUTE_OUT`／`ready` 建在 `source-bound 升 ready` 上，route `owner` 365/365 為 null，22 個 READY atom 的 binding 全為 `CANDIDATE_NOT_RATIFIED`、owner 為 `"#"`；同時 `b3_r7_tqaep.join` 自證 with_mandatory＝0。
4. **M4 B3「首切片 preimage ABSENT」與同一收據矛盾**：`output_root.preimage_state` 已列 `slice2.md` 為 29,687 B／`1861ca3a…`，與寫入後全等；同目錄 `draft.md` byte-identical。preimage 狀態未被寫前探測（`b3_prior_draft_inventory` 只盤 `70_` 舊輪，未盤輸出目錄自身）。
5. **M5 同一 44 案存在兩份互斥凍結收據**：`b3_r7_neg_mutations.json` 仍宣告 `PASS_REFUSAL:44`，無 supersede 指標；只有 `b3_r7_neg_reconcile.json` 判 HOLD。
6. **M6 B2 requiredness 判定非規則而是字首啟發**：34 案（詞彙外）→ `UNKNOWN`／HOLD，40 案（同樣詞彙外）→ 原樣標籤／PASS；放行規則未在任何收據或 SPEC 段落寫出。
7. **M7 跨收據計數矛盾**：同一批 1,465 列，B3 可接收數為 `b2_r7_tqaep` 的 1,351 與 `b3_r7_tqaep` 的 0；SPEC §6 的「96 missing／62 unresolved」與 HOLD 76 之間無對帳。
8. **M8 權利與時間未真量**：所有相位收據（B1／B2／B3／preflight／selftest／neg）皆無 `checked_at`、無 `rights_check_ref`；consumer 收據內嵌授權區塊的到期時間（01:08:15）早於收據自身 `checked_at`（15:40:58）14h32m，屬舊窗口內容貼用；window `ops_used=0` 卻宣稱 HOST_OPERATIONS 級 `LOCAL_DRAFT_WRITE`。
9. **M9 FirstFail 雙極性比對未實作**：B2 全批 2,930 案無 `expected_first_fail` 欄；B1／B3 POS 極性無「未觸發」欄；只有 B1-NEG 20 案與 B3-NEG 44 案可比。
10. **M10 文件數字與收據不一致**：CLOSEOUT L6／L89 及 publish_record 把 `45d41c59…` 標為「凍結候選」，與受檢 `6816…` 不同；HANDOFF 的重現指令 `--include-docs` 與凍結設定相反。

---

## 9｜次要缺陷（Minor）

1. B1 五案 `PASS_SOURCE_BOUND` 的族名以 `PASS_` 開頭、且仍帶 `hold_reason`；以 `startswith("PASS")` 聚合會把 37 當成通過數。
2. B1 012–017 的個案區塊 `disk_sha256=null`，量測值只存在 `run_all.fda`；僅看 tqaep 無法稽核 `pin_match`。
3. B1 外部 carrier 的 PASS 依賴 `00_PREFLIGHT/b1_source_allowlist.json`（`generated_at=2026-11-26T12:54:49`，前一日）作為期望值來源；該檔不在本輪 SPEC 內，屬作者自備清單。
4. B2 1,385 個 NEG 只執行「跨 namespace」一種變異，SPEC 該列允許的另一種（改 payload／Requiredness）未執行。
5. B2 `HARD` 單元統計（units 80／preserved 55／other 25）與 SPEC「18 HARD」不同層，收據未解釋 25「other」。
6. `r7_consumer_selftest` 11 臂全為 B1；B2／B3 consumer 驗證器未自測。
7. `r7_b4_receiver.candidate_digest` 實為 B1 unit-id-set sha；`envelope_sha256` 實為 `b1_r7_run_all.json` 的 sha，欄名易誤讀。
8. HANDOFF L4「唯一硬阻塞是 A 與 B」句法自相矛盾（列了兩項）。
9. `DELIVERY_INDEX.published.state="see publish record"`：已發布卻不在凍結成員內，索引與凍結成員邊界未明示。
10. B2 `requiredness_distribution` 的 `other_rows=20` 未展開，與 40 個詞彙外 PASS 標籤無對應。

---

## 10｜裁決與可認證的宣稱上限

### 10.1 裁決：**REJECT**

理由（任一即足）：
- M1＋M10：受檢凍結身分在查核中被換版，文件引用另一個 digest，**無單一可釘住的对象**。
- M2：實際效果（公開推送）與 SPEC §7 明文相反。
- M3＋M4：B3 的 273 ready／ROUTE_OUT／COMMITTED 建在 SPEC 自列的 `source-bound 升 ready` 之上，owner 全空、binding 未批准，且 preimage 與同收據矛盾。
- M5＋M7：44 案在凍結內同時是 PASS_REFUSAL 與 HOLD；同一 1,465 列的可接收數為 1,351 與 0。
- M6＋M9：requiredness 與 FirstFail 的判定規則無法由收據或 SPEC 復原。

### 10.2 我願意認證的宣稱上限（Claim ceiling）

**可認證（機械、可重算、且我已獨立重現）**
- SPEC 文件層：入口 `21c27fbb…`、manifest `2e4db2d2…`（8 列全符）、B1／B2／B3 三 pin 與 K／W 雙載體 byte-identical。
- 案卷普查：B1 30/60、B2 1,465/2,930、B3 365/752；收據 case 集合與 SPEC 逐 id 相等（缺 0、多 0）。
- 內容身分（非語意）：B2 1,385 個 QROW 的 `payload_sha`＋行號可由外部 carrier `463dcf33…` 100% 重算；B1 BASE 18 組身分可由 repo HEAD `9a70501` 的 blob 與 disk sha 重現；B1 外部 carrier 與 FDA 政策 L24 `DENY_ALWAYS` 可實讀；B3 PROTECTED 條款 sha／行號可實讀。
- 判定收斂：B1 12 案 `FIXTURE_ONLY` 確已降為 HOLD、5 案 `PASS_EVIDENCE` 確已移出 PASS；B3 44 案在 `neg_reconcile` 確為 HOLD，其中 11 案是**真實的 FirstFail code divergence**。
- 准入狀態：`ReadyExecute=false` 且有兩個具名 blocker；四批 `accepted` 皆 false；`FIN_ORDER=DENY`。
- `candidate_digest=6816…` 依自述慣例對 41 筆記錄行可重算（僅對 commit `64747d6` 的樹成立）。

**不可認證（本候選未證明，任何人不得由此推稱）**
- 任何批次接受（B0／B1／B2／B3／W0）、任何 `ReadyExecute`、任何 `W0_COMPLETE`。
- 任何語意等價或原 Reader／原 oracle 已具；`PASS_SOURCE_BOUND` 只證 locator＋內容 sha，不證語意。
- B2 的 2,854 PASS 作為**准入**；它只是 payload 身分（1,459 列仍缺 metadata）。
- B3 的 273 ready／273 ROUTE_OUT／COMMITTED；owner 與 binding 皆未成立。
- 權利現時性：B0 SourceReadSet/2 未重讀，三端接收的是歷史信封；內嵌授權區塊已過期。
- 凍結的不可變性與可重現性：同名凍結檔已被就地換版，文件與發布引用另一 digest。
- 發布的授權：SPEC §7 明示未授權推送，實際已推送。

---

*本裁決僅讀取與重算，未修改任何受檢檔案；所引用數字皆取自 40_OPS 收據、00_PREFLIGHT 與 SPEC 原始 bytes，並經獨立重算或外部實讀。*
