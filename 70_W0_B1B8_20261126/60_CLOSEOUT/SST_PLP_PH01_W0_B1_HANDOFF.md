# SST_PLP_PH01_W0_B1_HANDOFF

- subject `SST/SQS-THC/PH01/E00`｜OriginalWave `P1-W00M`｜BID `1`｜effect `SOURCE_READ`
- 供 **B4**（唯一直接 Consumer）與經 B4 間接的 B6 使用；本檔不代 B4/B6 發任何效果授權，不改 W0M／PH01 active pin
- 母檔：`SST_PLP_PH01_W0_B1_CLOSEOUT.md`（判定與證據在該檔；本檔只交接口、可重跑入口與現況）

## 1｜四 Ready 現況（照 SPEC §02.READY 分帳）

| Ready | 判定 | 依據 |
|---|---|---|
| `ReadyDraft` | **成立** | 30 unit／60 case 已解析、payload pin 30/30、合法 scope 與真 pin |
| `ReadyAtom` | **部分** | 11 unit 有真 observation；19 unit 為 typed missing（見母檔 §4.2）；作者細規 `SEMANTIC_ORACLE_UNBOUND` |
| `ReadyExecute` | **成立（本批四 Op 範圍）** | 授權 RepoRoot＋真 git 能力＋當前窗口權利；四 Op 已真跑 |
| `ReadyAccept` | **不成立** | 60 原 Case 未執行、無分離 Checker 判定 |

## 2｜可直接消費的 typed 輸出（B4 用）

抽取自 `40_OPS/b1_run_20261126T113131.json`（SHA256 `2247f43a…`）。**B4 不得自行重算或改寫；如需新 pin 走新 transaction。**

```
RepoReadSet@1 {
  subject        = "SST/SQS-THC/PH01/E00"
  original_wave  = "P1-W00M"
  bid            = 1
  effect         = "SOURCE_READ"
  write_set      = []
  preimage       = "N/A"

  repo {
    root            = "C:\Projects\Agent_Workspace\SQS-THC"
    commit          = "9a70501ad4bbf315c675894a7a58c0f98bf18f47"
    tree            = "688de895b003c35da1b85c0c7926089a44e78855"
    branch          = "main"
    dirty           = true          # 132 status entries at read time
    remotes         = []
    remote_head     = null
    remote_state    = "NO_REMOTE_CONFIGURED"
    git_version     = "git version 2.56.1.windows.1"
  }
  tree_entries = 295
}
```

### 2.1｜CommitPathSpan（已觀測，含 blob 與 raw SHA）

| unit | key | path | git blob | bytes |
|---|---|---|---|---|
| U0001 | BASE-001 | `src/kernel/fsdt/__init__.py` | `c21ec7b7af…` | 8,034 |
| U0002 | BASE-002 | `src/kernel/temporal/__init__.py` | `de8eeba844…` | 5,048 |
| U0003 | BASE-003 | `src/kernel/knowledge/__init__.py` | `c9476a2710…` | 6,722 |
| U0004 | BASE-004 | `src/kernel/harness/__init__.py` | `1be286eb13…` | 7,253 |
| U0005 | BASE-005 | `src/kernel/capability/__init__.py` | `43a3a23fc7…` | 4,449 |
| U0010 | BASE-010 | `adapters/xq-read-watch.yaml` | 見收據 `measured[]` | 見收據 |
| U0009 | BASE-009 | `data_plane/config/*.yaml`（2 檔） | `f077290d9c…`／`6267f8d09c…` | 1,262／1,549 |

完整 `raw_sha256`、`mode`、`git_bytes_field` 與每檔 AST symbol 清單在收據 `rows[].resolutions[].measured[]`，B4 應直接引用該路徑而不要抄表。

### 2.2｜FDA 七槽（全部 HOLD，B6 需知）

```
for slot in [watch_ui, radar_signal, xs_compile, xs_backtest,
             at_simulated_order, broker_external_event_read, broker_live_submit]:
    verdict            = "TYPED_MISSING_ABSENT_IN_TREE"
    first_fail         = "B1_SOURCE_DECLARED_PATH_MISSING"
    source_guide       = ABSENT
    lease / window_raw = ABSENT
    gui_started        = false
broker_live_submit:
    invariant          = "DENY_INVARIANT"
    allowed_effect_pos = null
```

### 2.3｜UnknownPhysicalEdgeSet（20 條，全 UNKNOWN）

`EXIT.startup.CORE`、`EXIT.startup.POLICY`、`EXIT.build.REPO`、`EXIT.CI.TEST`、
`EXIT.profile.sqs-orchestrator`、`EXIT.profile.sqs-data-analysis`、`EXIT.profile.sqs-risk`、
`EXIT.runtime.DISPATCH`、`EXIT.runtime.STOP`、`EXIT.GENIE.SW-01` … `EXIT.GENIE.SW-08`、
`EXIT.DEV-admission.POLICY`、`EXIT.DEV-admission.REPO`、`EXIT.DEV-admission.PIPD`

每條：`physical_status=UNKNOWN`、`missing=["physical call-chain artefact"]`。
**靜態無命中不是 OFF 的證據**——B6 不得以此關閉任何邊。

## 3｜可重跑入口（已實測）

```text
cwd = C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126\20_DEV\b1_reader
cmd = python -B run_b1.py
out = ..\..\40_OPS\b1_run_<UTCstamp>.json
```

- 需 `python`（3.14.9）與 `git`（2.56.1.windows.1）；`PYTHONDONTWRITEBYTECODE=1` 或不加 `-B` 會產生 `__pycache__`，本輪一律 `-B`。
- 讀取對象：K 的 B1 SPEC（路徑以 `listdir` 定位，不硬編長字串）＋受權 RepoRoot。
- 每次執行前後自帶無寫比對（HEAD＋`sha256(git status --porcelain=v1)`），若 `before != after` 收據會直接寫 `WRITE_OBSERVED`。

批次接收（B1/B2/B3 共用同一 receiver，各自 context 與 own result）：

```text
cwd = C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\60_B1
cmd = python -B -m b1_consumer.cli receive \
        --envelope ..\40_OPS\ops_r4_r5_pos.raw\stdout.txt \
        --context  b1_receive_context_r6_2026-11-26.json \
        --out      receipts\b1_receipt_r6_2026-11-26.json
exit=0 (ACCEPTED) / 2 (rejected, typed) / 64 (context invalid)
```

context 必填鍵**恰為** 11 個：`context_version, consumer_id, candidate_digest, scope_id,
source_ids, rights_receipt_ref, rights_receipt_sha, rights_state_ref, rights_task_id,
rights_scope, verifier_version`（多一鍵或少一鍵即 `CONSUMER_CONTEXT_INVALID`）。

## 4｜權利鏈（B4/B6 須自行重驗，不可沿用 B1 結論）

| 項 | 值 |
|---|---|
| 當前窗口 | `WIN-4e4b8cdc56c7`，task `SST_PLP_PH01_W0_B1-B8_CONSTRUCTION`，scope `[sqs_thc_ph01_e00, w0_b1_b8_construction]`，ceiling `REPOSITORY_WRITE`，TTL 至 2026-11-26T19:25:31 +08:00 |
| 收據 | `…\owner_ws\artifacts\OWNER_WINDOW.json`，SHA256 `6ea926d1e8b75a9ae6c53b7255a793ef76fa29d0a7e7df26a3330482807904e8` |
| live state | `C:\Users\user\.hgk-owner\window.json`（`state=OPEN`、`broker_alive=true` 於 11:31 量測） |
| 驗證規則 | 收據 hash 必等於 context pin；`receipt.task_id`／`scope` 必與 context 全等；live `window_id` 必等於收據 `window_id`；窗口到期 ≤ 收據到期；過期即 `RIGHTS_EXPIRED` |
| 到期後 | 需 Owner 重開新窗口；舊收據不得回放 |

## 5｜B1 → B4 交接門

| 門 | 狀態 |
|---|---|
| B0 `SourceReadSet/2` 真接收 | ✅ r6 ACCEPTED（同窗口） |
| B1 `RepoReadSet` | ✅ 已產（commit/tree/blob/missing 俱在） |
| B1 `CommitPathSpan` | 🟡 11 observed／19 typed missing |
| B1 `UnknownPhysicalEdgeSet` | 🟡 20 edges，全 UNKNOWN |
| B1 技術准入（完整） | ❌ 受 H-B1-01（FABRIC/FDA 不在 repo）阻塞 |
| B1 → B4 `ReadyAccept` | ❌ 60 原 Case 未執行 |

**B4 可開始的部分**：以已 observed 的 5 Kernel／BASE-001..005、010 作 fit-gap 起點（KEEP/ADAPT 判定的真實輸入已具備）。
**B4 不可假設的部分**：`FABRIC/**`、FDA 七槽、`BASE-013..018` 的「原功能」——這些在原 repo 未被觀測到，B4 只能記 `UNKNOWN`／`HOLD`，不得寫成 DEFER 或「已移除」。

## 6｜交錯影響

- **B2 不受影響**：B2 requires 僅 `B0 SourceReadSet/2`，可立刻開工。
- **B6 受影響**：20 Edge 的 `OldSymbol`／physical inventory 全缺；H-B1-01 未解前 B6 無法閉合（詳母檔 §9）。
- **B0 不重凍**：B0 producer bytes 未變（`f3fa76ea…` 重算相符），僅 receiver 端換窗口，依 §02.R3 不重 freeze。

## 7｜本檔不宣稱

- 不宣稱 `B1_ACCEPTED`／`B1_READY_EXECUTE`／`W0Accepted`／`SourceFreezeRatified`。
- 不宣稱五 Kernel 的**語義**已通過（只證原 symbol 存在；作者細規未核）。
- 不宣稱 19 項原功能不存在。
- 不宣稱 FHS 任一 Edge 已 OFF。
