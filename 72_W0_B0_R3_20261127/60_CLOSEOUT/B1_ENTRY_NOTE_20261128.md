# B1 進場備忘（B0 交接給 B1）— 2026-11-28

本件只做**交接與合法獨立工程準備**，不是 B1 的產品實作、不是 B1 的接受，也不改 B0 受檢候選。
B0 側來源：`SST_PLP_PH01_W0_B0_CLOSEOUT_HANDOFF_r33.md`（`## SST_PLP_PH01_W0_B0_CLOSEOUT` / `## …_HANDOFF` 兩章）、
`30_VERIFY/verdict_r32_round10.json`（ACCEPT，綁定 `c1f852cd50247aaa…`）。

## 1｜B1 可直接承接的 B0 成果（已接受）

| 項 | 實際載點 | 值 |
|---|---|---|
| B0 Reader（四 Op） | `20_DEV/b0_reader/`（重定位副本） | `native_entry.py` 三常數指向 descriptor r10；產品 WriteSet 恆為 `[]` |
| 共用嚴格 Receiver | `10_CODE/b0_r3_receiver/` | 受檢候選 13 成員之一部；round 10 ACCEPT |
| B1 真入站 callable | `10_CODE/consumers/b1.py`（`consumers.b1.receive_envelope`，CLI `python -B -m consumers.b1 receive`） | 自帶 `EXPECTED`／`consumer_use`，漂移即 `CONSUMER_EXPECTATION_DRIFT` |
| 可信 deployment | `00_PREFLIGHT/DEPLOYMENT_prod_20261127_r12.json` | sha `30f402a3f47ed399…`（= `deployment.py` `PINNED['prod']`） |
| 來源 envelope | `40_OPS/b0_sourcereadset_r11_20261127.json` | sha `fc7269789632cf29…`，5473 B |
| 原規則 pin | `00_PREFLIGHT/required_set_req12_read_all_2026-11-25.json`（`50ca45c1…`）／`…_w0m_2026-11-25.json`（`bc7afa53…`） | `provenance.rule_sha` 必須等於該 digest |
| B1 實收收據 | `40_OPS/r13_inbound_b1_receipt.json` | 2/2 ACCEPTED、`mandatory_satisfied=true`、13 欄＋evidence |
| 逐源 R/P/M 與 clause | 收據 `rows[].evidence` | 兩源 `R=['read']`、`P=['read']`、`M=[]`；clause sha 與 span 皆列 |
| 授權事實 | OWNER window `WIN-056f06fe7b02`（已 CLOSED）、receipt sha `bd0e539a2afae874…` | 新接收須重新取得合法權利 |

**上限**：以上只證 B0 的 SourceReadSet 可被 B1 真消費；**不**接受 B1 自身產品（Repo/BASE/FDA/ROOTS），
也不構成 B1 的 ReadyExecute。

## 2｜B1 自身義務（仍全數歸 B1）

活動入口：`C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8\W0_B0-B3_r7\00_唯一交付入口_W0_B0-B3_2026-11-27_r7.md`
→ `SST_PLP_PH01_W0_B1_執行控制小包_實質正文_2026-11-27_r7_Native-first_CODEX_FINAL.md`（另有 `FINAL_SPEC_MANIFEST.tsv` 與 `證據型附錄/`）。

依該正文 §02.R3 與 §03，B1 四個 Op 與其阻擋碼：

| Op | 語意 | WriteSet | 阻擋 |
|---|---|---|---|
| `B1.REPO` | RepoRoot→commit/tree/blob/path/missing，精確 16 檔 allow-list，declared／resolved／tracked／untracked／external carrier 分欄 | `[]` | `ROOT_UNBOUND`；remote≠local |
| `B1.BASE` | RepoReadSet→18 BASE／5 Kernel | `[]` | 缺原 BASE→typed missing |
| `B1.FDA` | 七槽×五 action×lease/build/Reader | `[]` | live submit／replace／cancel→`EFFECT_DENIED` |
| `B1.ROOTS` | 七 HardRoot／20 Edge→physical chain | `[]` | 未觀測→`UNKNOWN`；grep 空不證 OFF |

歷史分佈須保：原 30 Unit／60 Case；32 PASS／5 PASS_EVIDENCE／5 PARTIAL／12 FIXTURE_ONLY／6 HOLD／0 FAIL（不升批接受）。
`F01/D-1`（BASE-009、BASE-017）等 declared path 未具權採納前不得改；Repo/Source Owner 須逐 target 批准
namespace/root/path/commit/blob/raw/用途/接收權。

## 3｜B1 既有可取用資產（只讀）

- `C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\60_B1\b1_consumer\`（歷史 consumer：`receiver.py`、`cli.py`、`__init__.py`）—
  已被 B0 的嚴格 receiver 取代為入站實作，但其 CLI/測試習慣可重用；不得當作 B1 產品接受。
- `60_B1\b1_receive_context_2026-11-25.json`、`…_r6_2026-11-26.json`：歷史接收脈絡，只作比對。
- `60_B1\receipts\`、`60_B1\tests\`：歷史收據與測試，屬 LastGood，不得改寫。
- B1 自身 LastGood／finding 累計帳：**本輪未在 B1 活動根定位到獨立帳冊**（B1 尚未開工），
  進場時須依 §02.R3 建立並承接原 30 Unit／60 Case 額度，不得因新 session 重置。

## 4｜限制與不可越界

- 不得以 B0 的 `r13_inbound_b1_receipt.json` 代替 B1 產品接受；不得改寫 B0 受檢候選或 `FREEZE_r33`。
- 不得散布 LOCAL_ONLY 原件；公開投影只經 `REDACTION_NOTICE` 分帳（本地 `30f402a3…` ↔ 公開副本相異）。
- 任何新真來源讀取／接收需合法 OWNER 效果；`FIN_ORDER=DENY`、產品 `write_set=[]`、`preimage=N/A` 不變。
- B0 無 PARK 項；B1 不因 B0 非阻擋殘留（舊 r8–r10 收據帶 clause 明文、DRAFT 列不走返回前逐源重驗等）全域停等，
  但不得繞過真正受影的資料權或必要安全前置。

## 5｜建議第一步（可執行）

1. 核 B1 r7 入口與 `FINAL_SPEC_MANIFEST.tsv` 實體 sha；確認 A5/A6 採納與 blocked effects。
2. 在 `FHS-5_Workspace` 下建 B1 工程根；`RepoRoot` 先做 `rev-parse`／`ls-tree`／`cat-file` 只讀取證（16 檔 allow-list）。
3. 以本件 §1 的 deployment／envelope／`consumers.b1` 做一次真入站，確認 B1 端可消費 B0 結果（不升 B1 產品接受）。
4. 建 B1 finding/attempts 帳，承接原額度；再進 18 BASE／5 Kernel 取證。
