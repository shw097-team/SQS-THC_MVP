# SST_PLP_PH01_W0_B1_HANDOFF_rev2

> **本檔取代 `SST_PLP_PH01_W0_B1_HANDOFF.md`（rev 1）**；rev 1 保留為 LastGood。
> rev 2 依 Owner 指示加入全碟／`FHS` 深度搜索的結果：**30/30 unit 皆有實體 locator，0 typed-missing**。

- subject `SST/SQS-THC/PH01/E00`｜OriginalWave `P1-W00M`｜BID `1`｜effect `SOURCE_READ`
- 供 **B4**（唯一直接 Consumer）與經 B4 間接的 B6 使用；不代 B4/B6 發任何效果授權，不改 W0M／PH01 active pin
- 母檔：`SST_PLP_PH01_W0_B1_CLOSEOUT_rev2.md`

## 1｜四 Ready（SPEC §02.READY 分帳）

| Ready | 判定 | 依據 |
|---|---|---|
| `ReadyDraft` | **成立** | 30 unit／60 case 解析、payload pin 30/30、合法 scope 與真 pin |
| `ReadyAtom` | **大部分** | 30/30 有實體 locator；作者細規仍 `SEMANTIC_ORACLE_UNBOUND`；FDA 卡在 carrier 權威（H-B1-01） |
| `ReadyExecute` | **成立（本批四 Op 範圍）** | 授權 RepoRoot＋真 git 能力＋當前窗口 |
| `ReadyAccept` | **不成立** | 60 原 Case 未執行、無分離 Checker |

## 2｜B4 可直接消費的 typed 輸出

抽取自 `40_OPS/b1_run_20261126T114524.json`（`ce84f3b8…`）。**B4 不得自行重算或改寫。**

```
RepoReadSet@2 {
  subject = "SST/SQS-THC/PH01/E00"; original_wave = "P1-W00M"; bid = 1
  effect = "SOURCE_READ"; write_set = []; preimage = "N/A"

  repo { root  = "C:\Projects\Agent_Workspace\SQS-THC"
         commit = "9a70501ad4bbf315c675894a7a58c0f98bf18f47"
         tree   = "688de895b003c35da1b85c0c7926089a44e78855"
         branch = "main"; dirty = true; status_entries = 132
         remotes = []; remote_head = null; remote_state = "NO_REMOTE_CONFIGURED" }
  tree_entries = 295          # tracked at HEAD
  disk_files_indexed = 25853  # working tree (excluding .git and caches)
}
```

### 2.1｜18 BASE ＋ 5 KERNEL：全部已定位

| unit | key | 落點類別 | locator |
|---|---|---|---|
| U0001–U0005 | BASE-001..005 | tracked@HEAD | `src/kernel/{fsdt,temporal,knowledge,harness,capability}/__init__.py` |
| U0006 | BASE-006 | untracked | `agents/profiles/sqs-{orchestrator,data-analysis,risk}/`（各 `SOUL.md`／`config.yaml`／`mcp.json`／`distribution.yaml`／`README.runtime-contract.md`／`fixtures/`） |
| U0007 | BASE-007 | untracked | `SQS/TWICT_RUNTIME_PACK_MANIFEST.yaml` |
| U0008 | BASE-008 | untracked | `SQS_ENGINEERING_BASE_DISPOSITION.yaml`、`SQS_STACK_MANIFEST.yaml` |
| U0009 | BASE-009 | 混合 | tracked `data_plane/config/{data_policy,provider_profile}.yaml`；untracked `data_plane/src/{backfill_daily,check_daily}.py` |
| U0010 | BASE-010 | tracked@HEAD | `adapters/xq-read-watch.yaml` |
| U0011 | BASE-011 | untracked | `adapters/fda-xq-globalwinner-route.yaml` |
| U0012 | BASE-012 | untracked | `AGENTS.md`／`README.md` |
| U0013–U0017 | BASE-013..017 | **FDA carrier** | 見 §2.2 |
| U0018 | BASE-018 | 路徑不同 | `evidence/review/FDA_USER_GUIDE.md`（20,138 B）；`independent_checker.py`／`test_xq_build_drift.py`／`tests/test_fda_*` 在 FDA carrier |

逐檔 `raw_sha256`／`git_blob_sha1`／`bytes`／AST symbol 清單在收據 `rows[].resolutions[].measured[]`，B4 應直接引用而不抄表。

### 2.2｜FDA carrier（兩份，全數不同 → 需 Owner 指名）

```
carrier A = C:\Projects\Agent_Workspace\FHS\Fabric\FABRIC\fabric-desktop-automation
carrier B = C:\Projects\Agent_Workspace\FHS\Fabric\Fabric-rebind-publish\FABRIC\fabric-desktop-automation
兩者皆非 git repo、無 pin/seal；15/15 artefact 存在；15/15 SHA256 不同
→ AUTHORITY_COLLISION_HOLD（H-B1-01）
```

可複用事實（兩份皆具，數值見收據）：

- `action_classes` 共 5：`XQ_LAUNCH_LOCATE`、`XS_COMPILE_PASS`、`XS_COMPILE_FAIL_READBACK`、`XQ_PAPER_CONFIG`、`XQ_LOG_EXPORT_READBACK`
- `live_broker: DENY_ALWAYS` → 佐證 `FDA:broker_live_submit = DENY_INVARIANT`
- provider 資格：`PYWINAUTO_WIN32`（10/10）、`CUA`（10/10）、`UFO2`（7/7 effective-load）
- 參照之 fixture receipt：`FDA_F01_LIVE_FIXTURE_RECEIPT.json`、`FDA_F06_F07_LIVE_FIXTURE_RECEIPT.json`、`FDA_F09_RADAR_RECEIPT.json`、`FDA_F10_F11_READBACK_RECEIPT.json`、`FDA_XQ_BUILD_FINGERPRINT_RECEIPT.json`

### 2.3｜UnknownPhysicalEdgeSet（20 條，全 UNKNOWN）

`EXIT.startup.CORE`、`EXIT.startup.POLICY`、`EXIT.build.REPO`、`EXIT.CI.TEST`、
`EXIT.profile.sqs-orchestrator`、`EXIT.profile.sqs-data-analysis`、`EXIT.profile.sqs-risk`、
`EXIT.runtime.DISPATCH`、`EXIT.runtime.STOP`、`EXIT.GENIE.SW-01`…`SW-08`、
`EXIT.DEV-admission.POLICY`、`EXIT.DEV-admission.REPO`、`EXIT.DEV-admission.PIPD`

每條 `physical_status=UNKNOWN`、`missing=["physical call-chain artefact"]`。**B6 不得以此關閉任何邊。**

## 3｜可重跑入口（已實測）

```text
cwd = ...\70_W0_B1B8_20261126\20_DEV\b1_reader
cmd = python -B run_b1.py
out = ..\..\40_OPS\b1_run_<stamp>.json
```

reader v2（`b1_reader2.py`）要點：

- git：`rev-parse --verify HEAD`、`rev-parse HEAD^{tree}`、`ls-tree -r -l -z`、`cat-file blob`（唯一讀取路徑，絕不 checkout／import）
- 磁碟索引：`os.walk(onerror=..., followlinks=False)`，跳過 `.git`／`__pycache__`／`node_modules`／venv 等
- 解析序：tracked exact → tracked glob → tracked dir → **磁碟 exact** → tracked basename → **磁碟 basename** → absent
- 每次執行自帶無寫比對（HEAD＋status sha），不等即寫 `WRITE_OBSERVED`

批次接收（三端共用 receiver，各自 context）：

```text
cwd = ...\60_B1
cmd = python -B -m b1_consumer.cli receive \
        --envelope ..\40_OPS\ops_r4_r5_pos.raw\stdout.txt \
        --context  b1_receive_context_r6_2026-11-26.json \
        --out      receipts\b1_receipt_r6_2026-11-26.json
exit=0 ACCEPTED / 2 rejected / 64 context invalid
```

context 必填鍵**恰 11 個**：`context_version, consumer_id, candidate_digest, scope_id, source_ids, rights_receipt_ref, rights_receipt_sha, rights_state_ref, rights_task_id, rights_scope, verifier_version`（多／少一鍵即 `CONSUMER_CONTEXT_INVALID`）。

## 4｜權利鏈（B4/B6 須自行重驗）

| 項 | 值 |
|---|---|
| 當前窗口 | `WIN-4e4b8cdc56c7`，task `SST_PLP_PH01_W0_B1-B8_CONSTRUCTION`，scope `[sqs_thc_ph01_e00, w0_b1_b8_construction]`，ceiling `REPOSITORY_WRITE`，TTL 至 2026-11-26T19:25:31 +08:00 |
| 收據 | `…\owner_ws\artifacts\OWNER_WINDOW.json`，SHA256 `6ea926d1e8b75a9ae6c53b7255a793ef76fa29d0a7e7df26a3330482807904e8` |
| live state | `C:\Users\user\.hgk-owner\window.json` |
| 驗證規則 | 收據 hash = context pin；`task_id`／`scope` 全等；live `window_id` = 收據 `window_id`；窗口到期 ≤ 收據到期；過期即 `RIGHTS_EXPIRED` |

## 5｜B1 → B4 交接門

| 門 | 狀態 |
|---|---|
| B0 `SourceReadSet/2` 真接收 | ✅ r6 ACCEPTED（同窗口） |
| B1 `RepoReadSet` | ✅ commit/tree/blob/missing 俱在 |
| B1 `CommitPathSpan` | 🟢 30/30 有 locator（0 typed-missing）；FDA 待權威指名 |
| B1 `UnknownPhysicalEdgeSet` | 🟡 20 edges 全 UNKNOWN |
| B1 技術准入（完整） | 🟡 僅 H-B1-01（carrier 指名）待解 |
| B1 → B4 `ReadyAccept` | ❌ 60 原 Case 未執行 |

**B4 可立即開始**：以 5 Kernel＋13 個已定位 BASE 作 fit-gap 起點（KEEP/ADAPT 的真實輸入已具備），FDA 部分先記 `CARRIER_PENDING_OWNER_DESIGNATION`。

## 6｜本檔不宣稱

- 不宣稱 `B1_ACCEPTED`／`B1_READY_EXECUTE`／`W0Accepted`／`SourceFreezeRatified`。
- 不宣稱五 Kernel 的**語義**通過（只證原 symbol 存在；作者細規未核）。
- 不宣稱 FDA 七槽的 SPeC 名稱與 carrier 詞彙等價（實測 carrier 用 5 action classes，slot 名 0 命中；M:N 映射待 B4 判）。
- 不宣稱 FHS 任一 Edge 已 OFF。
