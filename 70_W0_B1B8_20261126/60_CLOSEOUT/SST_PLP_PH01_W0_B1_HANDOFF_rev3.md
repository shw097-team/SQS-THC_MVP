# SST_PLP_PH01_W0_B1_HANDOFF_rev3

> 取代 `_rev2`（rev 1／rev 2 保留 LastGood）。母檔：`SST_PLP_PH01_W0_B1_CLOSEOUT_rev3.md`。
- subject `SST/SQS-THC/PH01/E00`｜BID `1`｜effect `SOURCE_READ`｜`write_set=[]`｜`FIN_ORDER=DENY`
- 交接給 **B4**（唯一直接 Consumer）與經 B4 間接的 **B6**；本檔不代 B4／B6 發任何效果授權，不改 W0M／PH01 active pin

## 1｜可消費的 typed 證據

### 1.1｜RepoReadSet@2（B4 直接引用，不得自行重算）

```
repo { root   = "C:\Projects\Agent_Workspace\SQS-THC"
       commit = "9a70501ad4bbf315c675894a7a58c0f98bf18f47"
       tree   = "688de895b003c35da1b85c0c7926089a44e78855"
       branch = "main"; dirty = true; status_entries = 132
       remotes = []; remote_head = null }
tree_entries = 295 ; disk_files_indexed = 25853
```

### 1.2｜23 BASE unit 落點（0 absent）

| 類別 | 數 | unit |
|---|---|---|
| `OBSERVED_TRACKED_AT_HEAD` | 11 | BASE-001..005、010 ＋ 部分 |
| `OBSERVED_IN_WORKING_TREE_UNTRACKED` | 5 | BASE-006、007、008、011、012 |
| `PARTIAL_TRACKED_AND_OTHER` | 1 | BASE-009（4 目標全有 locator，無缺件） |
| `OBSERVED_IN_FDA_CARRIER_CONTENT_IDENTICAL` | 6 | BASE-013..018 |

逐檔 `raw_sha256`／`content_sha256_lf`／`git_blob_sha1`／`bytes`／AST symbols 在
`40_OPS/b1_run_20261126T120202.json` 的 `ops.B1.BASE.rows[].resolutions[].measured[]`。

### 1.3｜FDA content pin（取代原「碰撞」）

```
primary = ...\FHS\Fabric\FABRIC\fabric-desktop-automation          (LF)
mirror  = ...\FHS\Fabric\Fabric-rebind-publish\FABRIC\fabric-desktop-automation (CRLF)
verdict = IDENTICAL_MODULO_EOL ; byte_diff = 15 ; content_diff = 0
reorg receipt manifest_sha256 = d35bef595fb300f697c5133f8b02dfd22115b44ac028fda729a1f36f88fcb122 (52 entries, checker 175/175)
```

**B4／B6 引用 `content_sha256_lf`，不得以 raw SHA 差異判為版本衝突。**

action classes（5）：`XQ_LAUNCH_LOCATE`、`XS_COMPILE_PASS`、`XS_COMPILE_FAIL_READBACK`、`XQ_PAPER_CONFIG`、`XQ_LOG_EXPORT_READBACK`；`live_broker: DENY_ALWAYS`。
provider 資格（兩份皆具）：PYWINAUTO_WIN32 10/10、CUA 10/10、UFO2 7/7。
可複用 fixture receipts：`FDA_F01_LIVE_FIXTURE_RECEIPT.json`、`FDA_F06_F07_…`、`FDA_F09_RADAR_RECEIPT.json`、`FDA_F10_F11_READBACK_RECEIPT.json`、`FDA_XQ_BUILD_FINGERPRINT_RECEIPT.json`。
**這些是歷史 Build 的資格收據，未經核為當前 build／scope，不得冒新版本實測。**

### 1.4｜UnknownPhysicalEdgeSet（20 條，全 UNKNOWN）

`EXIT.startup.CORE`、`EXIT.startup.POLICY`、`EXIT.build.REPO`、`EXIT.CI.TEST`、`EXIT.profile.sqs-{orchestrator,data-analysis,risk}`、`EXIT.runtime.DISPATCH`、`EXIT.runtime.STOP`、`EXIT.GENIE.SW-01..08`、`EXIT.DEV-admission.{POLICY,REPO,PIPD}`
每條 `physical_status=UNKNOWN`、`missing=["physical call-chain artefact"]`。**B6 不得據此關閉任何邊。**

## 2｜60 案 TQAEP 結果（供 B4 判斷成熟度）

| 判定 | 數 |
|---|---|
| PASS | 49 |
| HOLD_ORACLE_UNBOUND | 11（5 KERNEL 語義、6 FDA lease/window） |
| FAIL | 0 |

收據 `40_OPS/b1_tqaep_20261126T120202.json`，`cd4ca942482512058bc05dbac22cc9b7c300afb6ecbd9efc962164c6c74dfcce`。
**Maker 自檢**；`B1_ACCEPTED` 未成立（缺分離 Checker 同候選判定）。

## 3｜可重跑入口

```text
# 四 Op 取證
cwd = ...\70_W0_B1B8_20261126\20_DEV\b1_reader
cmd = python -B run_b1.py            -> ..\..\40_OPS\b1_run_<stamp>.json

# 60 原 Case
cmd = python -B b1_cases.py          -> ..\..\40_OPS\b1_tqaep_<stamp>.json
```

```text
# B0 v2 三端接收（各自 context，11 keys 恰滿）
cwd = ...\60_B1
cmd = python -B -m b1_consumer.cli receive --envelope ..\40_OPS\ops_r4_r5_pos.raw\stdout.txt \
        --context b1_receive_context_r6_2026-11-26.json --out receipts\b1_receipt_r6_2026-11-26.json
```

## 4｜權利鏈（B4／B6 須自行重驗，不得沿用 B1 結論）

| 項 | 值 |
|---|---|
| 窗口 | `WIN-4e4b8cdc56c7`；task `SST_PLP_PH01_W0_B1-B8_CONSTRUCTION`；scope `[sqs_thc_ph01_e00, w0_b1_b8_construction]`；ceiling `REPOSITORY_WRITE`；至 2026-11-26T19:25:31+08:00 |
| 收據 | `…\owner_ws\artifacts\OWNER_WINDOW.json`，`6ea926d1e8b75a9ae6c53b7255a793ef76fa29d0a7e7df26a3330482807904e8` |
| live | `C:\Users\user\.hgk-owner\window.json` |
| 規則 | 收據 hash = context pin；task／scope 全等；live `window_id` = 收據 `window_id`；窗口到期 ≤ 收據到期；過期即 `RIGHTS_EXPIRED` |

## 5｜B1 → B4 交接門

| 門 | 狀態 |
|---|---|
| B0 `SourceReadSet/2` 真接收 | ✅ |
| `RepoReadSet` | ✅ commit/tree/blob/missing 俱在 |
| `CommitPathSpan` | ✅ 23 BASE＋5 KERNEL＋6 carrier 全有 locator |
| FDA content pin | ✅ 15/15 content-identical |
| `UnknownPhysicalEdgeSet` | 🟡 20 edges UNKNOWN（設計如此） |
| `B1_ACCEPTED` | ❌ 待分離 Checker |

## 6｜本檔不宣稱

- 不宣稱 `B1_ACCEPTED`／`B1_READY_EXECUTE`／`W0Accepted`／`SourceFreezeRatified`。
- 不宣稱五 Kernel **語義**通過（只證原 symbol 存在；5 條 NEG 仍 HOLD）。
- 不宣稱 FDA 七槽與 carrier 五 action class 等價（M:N 映射已列，語義判定留 B4）。
- 不宣稱任一 FHS Edge 已 OFF；不宣稱 FDA 歷史資格收據適用當前 build。
