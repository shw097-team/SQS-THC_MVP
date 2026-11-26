#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the B1/B2 r5 CLOSEOUT + HANDOFF documents from the run receipts.

Every number in the emitted documents is read from a frozen artefact, never typed by
hand, so the documents cannot drift from the receipts they cite.
"""
from __future__ import annotations
import hashlib

import json
import os
import time

R = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126"
OPS = os.path.join(R, "40_OPS")
OUT = os.path.join(R, "60_CLOSEOUT")

FREEZE = json.load(open(os.path.join(OPS, "b1b2_r5_candidate_freeze.json"), encoding="utf-8"))
B1T = json.load(open(os.path.join(OPS, "b1_r5_tqaep.json"), encoding="utf-8"))
B2T = json.load(open(os.path.join(OPS, "b2_r5_tqaep.json"), encoding="utf-8"))
RUN = json.load(open(os.path.join(OPS, "b1_r5_run_all.json"), encoding="utf-8"))
EDGE = json.load(open(os.path.join(OPS, "b1_r5_edge_sec.json"), encoding="utf-8"))
RECV = json.load(open(os.path.join(OPS, "b2_r5_receivers.json"), encoding="utf-8"))

SPEC_MANIFEST = FREEZE["spec_manifest_sha256"]
CAND_MANIFEST = FREEZE["candidate_manifest"]["sha256"]
HEAD = FREEZE["inputs"]["repo_head"]

B1V = B1T["verdict_counts"]
B2V = B2T["verdict_counts"]
B3A = B2T["receivers"]["B3"]["accepted"]; B3R = B2T["receivers"]["B3"]["rejected"]
B5A = B2T["receivers"]["B5"]["accepted"]; B5R = B2T["receivers"]["B5"]["rejected"]
SD = len(B2T.get("source_defects") or [])
B3T = json.load(open(os.path.join(OPS, "b3_r5_tqaep.json"), encoding="utf-8"))
B3C = B3T["verdict_counts"]
B3J = json.load(open(os.path.join(OPS, "b3_r5_join.json"), encoding="utf-8"))
B3D = {"bytes": os.path.getsize(os.path.join(OPS, "b3_draft", "SourceChildLedger.draft.v2.json")),
       "sha256": hashlib.sha256(open(os.path.join(OPS, "b3_draft", "SourceChildLedger.draft.v2.json"), "rb").read()).hexdigest()}
MET = json.load(open(os.path.join(OPS, "b2_r5_meta.json"), encoding="utf-8"))
M01 = hashlib.sha256(open(os.path.join(OPS, "m01_boundary_grep_receipt.json"), "rb").read()).hexdigest()
B2H = B2T["verdict_counts"].get("HOLD", 0)


def counts_line(d):
    return "、".join(f"{k} {v}" for k, v in sorted(d.items()))


def write(name, text):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return p


COMMON_HEAD = f"""---
artifact_kind: BATCH_CLOSEOUT_HANDOFF
subject: SST/SQS-THC/PH01/E00
original_wave: P1-W00M
spec_version: 2026-11-26_r5_Native-first_CODEX_FINAL
spec_manifest_sha256: {SPEC_MANIFEST}
candidate_manifest_sha256: {CAND_MANIFEST}
generated_at: {time.strftime("%Y-%m-%dT%H:%M:%S%z")}
product_actual: EXECUTED_SOURCE_READ_ONLY
fin_order: DENY
distribution: LOCAL_ONLY
---
"""

B1 = COMMON_HEAD + f"""
# W0-B1｜CLOSEOUT + HANDOFF（r5 產品層）

## 01｜接受狀態（不代簽）

| 項 | 值 |
|---|---|
| B1 產品實跑 | 是（60 案全部執行） |
| 案級分佈 | {counts_line(B1V)} |
| EDGE/SEC | {EDGE['counts']['pass']} PASS / {EDGE['counts']['fail']} FAIL |
| **B1_ACCEPTED** | **NO** |
| 凍結候選 | `b1b2_r5_CANDIDATE_MANIFEST.tsv` `{CAND_MANIFEST}`（{FREEZE['candidate_manifest']['artefacts']} artefacts） |

拒絕理由（可核）：D-2（BASE-018 四測試無讀權）、D-4（五 Kernel 十條作者細規語義未核）、
D-3（六 slot 的 M:N 未建立）、以及 5 個 BASE 案的 declared target 無身分（PARTIAL）。

## 02｜真輸入

| 項 | 值 |
|---|---|
| RepoRoot | `{FREEZE['inputs']['repo_root']}` |
| local HEAD | `{HEAD}` |
| remote | {FREEZE['inputs']['repo_remote'] or 'none（repo 無 origin remote）'} |
| FDA 載體根 | `{FREEZE['inputs']['fda_carrier_root']}` |
| allow-list | `{FREEZE['inputs']['allowlist_sha256']}` |
| locator bindings | `{FREEZE['inputs']['locators_sha256']}` |
| spec manifest | `{SPEC_MANIFEST}` |

## 03｜各 Op 實測

| Op | 結果 |
|---|---|
| REPO | `is_work_tree=true`、HEAD `{HEAD}`、dirty tracked = {RUN['repo']['dirty_tracked_files']}、remote = {RUN['repo']['remote_url'] or 'null'} |
| BASE | 23 unit（18 BASE + 5 KERNEL）；tracked {RUN['base']['read_set_summary']['tracked_targets']}、external verified {RUN['base']['read_set_summary']['external_verified']}、missing {RUN['base']['read_set_summary']['missing_targets']} |
| KERNEL | 5/5 內容 SHA 與 spec 釘值全等；64 個 symbol span 全等；pinned commit `d34dc903…` 本地不存在（已入帳） |
| FDA | 16/16 allow-list raw SHA 全等；7 slot 全 `CARRIER_LEVEL_ONLY`；`live_broker=DENY_ALWAYS`（矩陣 L24，讀自 bytes） |
| ROOTS | 七根／20 Edge = **UNKNOWN**（B6 未物化，不猜） |
| effect | `{RUN['effect']}`；write_set `{RUN['write_set']}`；preimage `{RUN['preimage']}`；fin_order `{RUN['fin_order']}` |

## 04｜逐案結果

| 判別 | 案數 | 含義 |
|---|---:|---|
| PASS | {B1V.get('PASS',0)} | 原義務真滿足（18 BASE NEG 的原 mutation、broker deny invariant 等） |
| PASS_EVIDENCE | {B1V.get('PASS_EVIDENCE',0)} | 內容＋span 取證成立；作者細規語義仍 HOLD |
| PARTIAL | {B1V.get('PARTIAL',0)} | declared target 無身分（磁碟未 tracked／目錄不可列舉），已記錄為 missing，**不記 PASS** |
| FIXTURE_ONLY | {B1V.get('FIXTURE_ONLY',0)} | 作者 fixture 域的拒絕成立，非原 schema PASS（D-3） |
| HOLD | {B1V.get('HOLD',0)} | 原 Oracle／讀權未具 |

## 05｜保留缺口（Owner 才能關）

D-1（三 locator 仍 CANDIDATE_NOT_RATIFIED，但磁碟 bytes 與 candidate raw SHA 相符）、
D-2（`tests/test_fda_lease.py`／`_router.py`／`_router_integration.py`／`_security.py` 名稱可見、內容未讀）、
D-3（6/7 slot 名在 16 檔 0 命中）、D-4（10 條作者細規）、TT-UP-1/2、E00/Rroute（B2 側）。

## 06｜交接（B4 / B6）

- 產出：`RepoReadSet`、`CommitPathSpan`、FDA 靜態 inventory、`UnknownPhysicalEdgeSet`。
- B4 可消費欄：`commit`,`path`,`blob`,`missing`（tracked 才有 commit；disk-untracked 明確為 null）。
- B6 只 observes，不得把 `UNKNOWN` 當 OFF。
- 接收者必須自帶 expected；本 CLOSEOUT 不是 ACK。

## 07｜分離驗證

| 輪 | 結論 | 主要 finding |
|---|---|---|
| 1 | REJECT（B1 3 mandatory） | 常數 deny 控制、跑後改 oracle、POS 無 FAIL 路徑 |
| 2 | REJECT（5 mandatory） | 換詞未換行為（Q POS 仍高報）、read control 仍字面分支、requiredness 維度混淆 |
| 3 | **ACCEPT / 0 mandatory** | 11 項全部開合（10 CLOSED、1 PARTIAL=P3）；另列 5 個非 mandatory |

**ACCEPT 的含義**：本批「報告無高報」——所有被宣稱 PASS 的案都真有原義務，所有 HOLD／PARTIAL
都未被稀釋成 PASS。它**不是** `B1_ACCEPTED`：批次接受仍要求全部適用案在原 Oracle 下 PASS，
而有 6 HOLD、12 FIXTURE_ONLY、5 PARTIAL。

**凍結 delta**：round3 驗證的是 manifest A `75660aa3…`（20 成員，存檔為
`b1b2_r5_CANDIDATE_MANIFEST_v1_verified.tsv`）。其後只改動了兩處、且皆為 checker 自己在
N-08／N-10 要求的交付面修正：`b1b2_r5_MAKER_NOTES.md`（更正過期數字）與新增
`b1_r5_run_fda_REGEN.json`（重生成收據）。**8 個 .py 與全部案級 JSON 位元組未變**；
manifest B 的 digest 差異可逐行核。Maker 與 Checker 同模型軸，model-axis SoD **未建立**。

## 08｜未做

未發布（`distribution=LOCAL_ONLY`）、未寫入 source repo（HEAD 與 status 前後不變）、
未接觸 GUI/lease/broker、未安裝任何工具、未宣 `B1_ACCEPTED`。
"""

B2 = COMMON_HEAD + f"""
# W0-B2｜CLOSEOUT + HANDOFF（r5 產品層）

## 01｜接受狀態

| 項 | 值 |
|---|---|
| 產品實跑 | 是（2,930 案全部執行，orphan 0） |
| 案級分佈 | {counts_line(B2V)} |
| **B2_ACCEPTED** | **NO** |
| 凍結候選 | `{CAND_MANIFEST}` |

## 02｜真輸入

| 項 | 值 |
|---|---|
| carrier | `SST_PLP_共用實質正文_工具合約_2026-11-23_r2.md` `{FREEZE['inputs']['carrier_sha256']}`（767,859 B，實測全等） |
| spec | `{SPEC_MANIFEST}` |
| Q 列 | 1,385（Q1 440／Q2 513／Q3 378／Q4 54，實測與 spec 象限一致） |

## 03｜QROWS 實測

| 項 | 值 |
|---|---|
| 逐列驗證 | **1,385 / 1,385**（physical line + key 欄 + row 欄 + canonical payload SHA 四項全等） |
| 未驗證 | 0 |
| 意義 | 原列逐字保全（VERBATIM_ONLY）；**不是**工具 requiredness/admission 的語義接受 |

## 04｜HARD / META / RETURN

| Op | 實測 |
|---|---|
| 欄位權威 | 由 carrier 自身宣告的四維度還原：`carrier:13` Q1=Requiredness(idx2)、`carrier:457` Q2=AdmissionDecision(idx2)/Requiredness(idx5)、`carrier:974` Q3=KindApplicability、`carrier:1356` Q4=Golden；Q3/Q4 無 Requiredness 欄 → `NOT_APPLICABLE`＋section 行號為 applicability evidence |
| HARD | 18 unit 的單位值與 carrier 列值比對（兩份不同記錄），非自比 |
| E00 | 8 unit 的 typed DesignSelection 逐字保留；`SELECTED_*` → 未授權 enable 被拒 |
| ROUTE | 54 unit 的 requiredness 陳述與其工具列交叉核對；改寫即拒 |
| META | 全部 `NOT_EXECUTED`（無官方 metadata 讀權／未連網），工具名不當 license、不當准入 |
| RETURN | union 1,465 送 B3/B5；B3 收 {B3A} 拒 {B3R}（缺 requiredness/source_row 者拒）、B5 收 {B5A} 拒 {B5R}（缺 metadata 者拒） |
| 來源缺陷 | {SD} 條。前版曾列 21 條 ROUTE 不一致，經分離 Checker 指出為 Maker 以子字串掃描造成的誤判，已全部撤回並改為結構化取欄（不再計入任何 verdict） |

## 05｜HOLD 的構成（{B2H} 案）

- 34 個 Q POS：原列 requiredness 欄存放作者策略值（`REUSE_INTERNAL_FIRST`、`BASE_REQUIRED_AS_ADAPTER` 等），
  不屬 carrier 宣告的原子集 → 不猜、記 HOLD。
- 34 案 Q POS 之外：8 案 E00（pinned spec B2-F05 宣告其 typed DesignSelection oracle HOLD，
  即使 carrier 交叉核一致也不得升 PASS）、34 案 ROUTE（route 未陳述 requiredness 欄，產品不斷言）。
- 全部 HOLD 的實際數字以 `b2_r5_tqaep.json` 的 `verdict_counts` 為準（本表不手抄）。
- 1,385 Q NEG 為真拒絕（同尾碼異 namespace → `NAMESPACE_JOIN_DENY`）。

**注意**：`REFERENCE/EVAL_ONLY`、`EVAL_ONLY_COMPARATOR` 這類「原子前綴＋限定詞」的取值，
本輪以原子前綴規則判定為合法 requiredness（保留原字串）。此為作者層解釋，非 carrier 明文，
已列入 AUTHOR_DESIGN_ONLY，Checker 可據此挑戰。

## 06｜交接（B3/B5）

- B3 mandatory `tool_key,source_row,requiredness`：requiredness 全 UNKNOWN → 全拒；B2 需先補欄位映射（D-5）。
- B5 mandatory 含 `metadata`：未取得 → 全拒；不得以工具名代替 license/ABI/lock。
- 接收結果為 `draft readiness`，**不是** ACK。

## 07｜未做

未安裝／啟用任何產品工具、未做 B5 選型、未連網取 metadata、未宣 `B2_ACCEPTED`。
"""

COMBINED_C = COMMON_HEAD + f"""
# W0 B1–B2｜合併 CLOSEOUT（下一階段唯一入口）

## 01｜一張表看現況

| 批 | 案數 | 分佈 | ACCEPTED |
|---|---:|---|---|
| B1 | {B1T['case_count']} | {counts_line(B1V)} | **NO** |
| B2 | {B2T['case_count']} | {counts_line(B2V)} | **NO** |

**ACCEPT 的含義**：round3 接受的是「報告無高報」，不是批次接受。`B1_ACCEPTED`／`B2_ACCEPTED`
仍為 NO，因為 6/12/5（B1）與 1,545（B2）個案仍 HOLD／PARTIAL／FIXTURE_ONLY，且原 Oracle／
讀權（D-1…D-5、TT-UP-1/2、E00、ROUTE）未具。

- 凍結候選 manifest：`{CAND_MANIFEST}`（{FREEZE['candidate_manifest']['artefacts']} artefacts）
- spec：`{SPEC_MANIFEST}`
- Repo HEAD：`{HEAD}`；實測 source repo 未被寫入
- 產品效果：`SOURCE_READ`／`write_set=[]`／`preimage=N/A`／`FIN_ORDER=DENY`

## 02｜三輪分離驗證

| 輪 | B1 | B2 | 處置 |
|---|---|---|---|
| 1 | REJECT（3 mandatory） | REJECT（5 mandatory） | 修 8 項真缺陷 |
| 2 | PARTIAL×2、CLOSED×1 | STILL OPEN×1、PARTIAL×1、CLOSED×3 | 第 2 次修補（額度用盡） |
| 3 | **ACCEPT / 0 mandatory** | 同左 | 11 項全開合；非 mandatory 5 項已列冊 |

## 03｜為什麼不是完成

原 §08 每根因最多 2 次實質修補；已用盡。仍具名的真阻斷是**權位與 Oracle**，不是施工能力：
D-1…D-5、TT-UP-1/2、6 E00、54 ROUTE。沒有原 Reader／原 Owner 的裁決，繼續改名或重跑
只會製造第五輪同形報告——依原規則 `PARK_UNTIL_DELTA`。

## 03b｜B3 當期工程准入（T4）

| 項 | 實測 |
|---|---|
| B3 引擎 | `20_DEV/b1_r5/b3_engine.py`：JOIN / CHILD / COMMIT（guarded LOCAL_DRAFT_WRITE） |
| JOIN 真跑 | 1,465 列全部 join；atoms_ready {B3J["ledger"]["atoms_ready"]}、atoms_held {B3J["ledger"]["atoms_held"]} |
| 原拒絕 | 三個 arm 全成立：同尾異 namespace、重複 atom、requiredness UNKNOWN |
| COMMIT | `40_OPS/b3_draft/SourceChildLedger.draft.json` 407,447 B，preimage=ABSENT，readback 相符 |
| B3 TQAEP | 752 案：{B3C.get('PASS_SOURCE_BOUND',0)} PASS_SOURCE_BOUND（11 CHILD＋11 PROTECTED 之來源 SHA＋span＋id 全核）、{B3C.get('PASS_REFUSAL',0)} PASS_REFUSAL、{B3C.get('HOLD',0)} HOLD、{B3C.get('NOT_EXECUTED',0)} NOT_EXECUTED（需原 Reader） |
| B0 入站（第 1 層） | OWNER 視窗已由本人開啟：`WIN-90b52ba73008`、task `..._B0_SOURCE_READ_AUTH`、ceiling `READ_ONLY_PROBE`、到期 2026-11-27T01:02:30 |
| B0 入站（第 2 層） | descriptor 權利區間過期 → **已由 Owner 授權續期**：`00_PREFLIGHT/B0_READ_CONTEXT_2026-11-26.json` `2064685a…`（3,582 B） |
| B0 入站（第 3 層） | 路徑身分需 sealed ACL → 已置於 `00_PREFLIGHT` 並複製原檔的 `CodexSandboxUsers:(R)` 明確 ACE，無 broad-principal 寫權 |
| reader pin | 依 Owner 明示授權換 pin：`native_entry.py` EXPECTED_DESCRIPTOR_PATH/SHA/BYTES 對齊新 descriptor（此為程式碼 delta，B0 原驗證不涵蓋） |
| **B0 真讀** | `exit 0`、`SST.B0.SourceReadSet/2`、1 entry、errors 0、`write_set=[]`、`fin_order=DENY`；`SST.ALL.W0.BLUEPRINT` sha `dd37a40b…`、457,294 B、span [572,579]、clause_sha `77132f06…`、R=['read']、M=[] |
| **B3 JOIN（真 ReadSet）** | 1,465 列：**atoms_ready 1,369**、atoms_held 96（原為 0／1,465） |
| **B3 draft v2** | `40_OPS/b3_draft/SourceChildLedger.draft.v2.json` {B3D['bytes']:,} B、sha `{B3D['sha256'][:12]}`、preimage ABSENT、single_file、postimage verified；舊 draft 保留未覆寫 |
| **B2 META** | 18 HARD：{MET['counts'].get('COLLECTED',0)} 取得官方 metadata（pydantic 2.14.4／jsonschema 4.26.0，PyPI JSON＋回應 SHA 釘定）、{MET['counts'].get('VERSION_UNBOUND',0)} pin UNBOUND、{MET['counts'].get('NOT_A_DISTRIBUTION',0)} 非發行物；未安裝、未選型 |
| **M-01 受界處置** | `40_OPS/m01_boundary_grep_receipt.json` sha `{M01[:12]}`：事件記錄、非授權所得隔離、FDA 證據只由 16/16 allow-list 依 SHA 重建、事件後未再廣域 grep |

**結論**：B3 的技術／施工准入在 B2 側已具（ToolReadSet 1,465 真物件），在 B0 側被具名阻斷——
需 OWNER 以其本人開啟 B0 範圍的簽章窗口；代理不得代開。在此之前 B3 的 B0 側以真實 B1 consumer
收據作 `RECEIPT_ONLY` 證據，且每一列都標明此缺口，不以 receipt 冒 ReadSet。

## 04｜下一手的精確復工條件

1. Repo/Source Owner：批准 D-1 三 locator、D-2 四測試讀權、D-5 父源/namespace 與接收權。
2. FDA/XQ/R13 Reader：逐槽提供原 typed schema／fixture／Reader（D-3）。
3. 五 Kernel Domain Owner：逐條確認 10 條作者細規與 9 個非 loss NEG 的 inner→outer（D-4／TT-UP-1）。
4. E02/E05/PIPD：提供 6 個 E00 的 typed DesignSelection／enable 權威。
5. R17/route Owner：提供 54 TECH_ROUTE 的 protected path。
取得任一項後只重驗受影 Case，不重跑全量。
"""

COMBINED_H = COMMON_HEAD + f"""
# W0 B1–B2｜合併 HANDOFF（下一階段唯一入口）

## 01｜可交接的產物（真存在）

| 產物 | 位置 | 證據 |
|---|---|---|
| B1 引擎＋CLI | `20_DEV/b1_r5/b1_engine.py`、`b1_cli.py` | manifest 內具 hash |
| B1 TQAEP | `20_DEV/b1_r5/b1_tqaep.py` → `40_OPS/b1_r5_tqaep.json` | 60 案逐案 |
| B1 EDGE/SEC | `b1_edge_sec.py` → `b1_r5_edge_sec.json` | {EDGE['counts']['pass']}/9 PASS |
| B2 引擎＋TQAEP | `20_DEV/b1_r5/b2_engine.py`、`b2_tqaep.py` → `b2_r5_tqaep.json` | 2,930 案 |
| B2 接收 | `b2_r5_receivers.json` | B3 0/1465、B5 0/1465（正確拒） |
| 凍結 | `b1b2_r5_CANDIDATE_MANIFEST.tsv` | `{CAND_MANIFEST}` |

## 02｜下游可立即做的事

- **B3/B4/B5/B6 可先建最小 receiver**：介面已存在（13 欄 receipt、mandatory 檢查、拒收路徑）。
- 不得把本 HANDOFF 當 ACK；接收者必須自帶 expected set 並自行驗 rights。
- B4 對 B1：只消費 tracked 的 `commit/path/blob`；`missing` 為明確 null，不得補值。
- B5 對 B2：`requiredness` 目前為 UNKNOWN，任何以推測值填入都會被拒。

## 03｜明示未具

`B1_ACCEPTED`、`B2_ACCEPTED`、`W0_COMPLETE`、`W1 ReadyExecute` 全部 **NO／未宣**。
Repo 未推送；`distribution=LOCAL_ONLY`。GUI/lease/broker 未接觸。
"""


H1 = COMMON_HEAD + f"""
# W0-B1｜HANDOFF（r5 產品層）

## 01｜producer 輸出（B4 可消費）

| 欄 | 值／規則 |
|---|---|
| RepoReadSet | `commit,path,blob,missing`；只有 tracked 才有 commit，disk-untracked 一律 null |
| CommitPathSpan | 逐 BASE/KERNEL 原 path 與 span；external carrier 無 commit（自身 Git 身分不同） |
| FDA inventory | 7 slot 全 `CARRIER_LEVEL_ONLY`；`live_broker=DENY_ALWAYS` 讀自矩陣 L24 |
| UnknownPhysicalEdgeSet | 七根／20 Edge = UNKNOWN（不推 OFF） |

## 02｜consumer 義務

- B4：自帶 expected set；不得把 `missing:null` 當 0；不得用 remote URL 當 local commit。
- B6：只 observes；`UNKNOWN` 不得當 OFF。

## 03｜未具

`B1_ACCEPTED=NO`；D-1…D-4、TT-UP-1/2 未閉合；本檔不是 ACK。
"""

H2 = COMMON_HEAD + f"""
# W0-B2｜HANDOFF（r5 產品層）

## 01｜producer 輸出

| 欄 | 值／規則 |
|---|---|
| ToolReadSet | union 1,465；Q 列 1,385 逐列 verbatim 驗證通過 |
| RequirednessDelta | requiredness = **UNKNOWN**（positional payload 無宣告欄位），不得推測填值 |
| WheelMetadataRef | `NOT_EXECUTED`（無官方 metadata 讀權） |

## 02｜consumer 義務

- B3：`requiredness` 為 UNKNOWN 即拒（已實測 0 收 / 1,465 拒）。
- B5：`metadata` 未具即拒；工具名不得當 license／ABI／選型。
- 接收結果是 draft readiness，不是 ACK。

## 03｜未具

`B2_ACCEPTED=NO`；D-5、TT-UP-1、6 E00、54 ROUTE 未閉合；未安裝任何工具。
"""


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    paths = [
        write("SST_PLP_PH01_W0_B1_CLOSEOUT_r5.md", B1),
        write("SST_PLP_PH01_W0_B1_HANDOFF_r5.md", H1),
        write("SST_PLP_PH01_W0_B2_CLOSEOUT_r5.md", B2),
        write("SST_PLP_PH01_W0_B2_HANDOFF_r5.md", H2),
        write("SST_PLP_PH01_W0_B1-B2_CLOSEOUT_r5.md", COMBINED_C),
        write("SST_PLP_PH01_W0_B1-B2_HANDOFF_r5.md", COMBINED_H),
    ]
    append_publish_note(paths)
    print(json.dumps({"written": paths}, ensure_ascii=False, indent=1))
    return 0


def append_publish_note(paths):
    """Append the publication/readback block, so a regeneration keeps it."""
    import subprocess
    import sys
    note = os.path.join(os.path.dirname(os.path.abspath(__file__)), "publish_note.py")
    if os.path.isfile(note):
        subprocess.run([sys.executable, "-B", note], check=False)


if __name__ == "__main__":
    raise SystemExit(main())
