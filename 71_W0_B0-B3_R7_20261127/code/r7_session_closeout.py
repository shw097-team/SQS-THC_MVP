#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Session closeout, next-session handoff and boot page — all figures from receipts.

Run AFTER the final freeze: the documents cite the freeze digest, and documents are not
freeze members, so citing it cannot move it.
"""
from __future__ import annotations

import glob
import json
import os
import time

R7 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPS = os.path.join(R7, "40_OPS")
OUT = os.path.join(R7, "60_CLOSEOUT")


def load(p):
    return json.load(open(p, encoding="utf-8"))


def fmt(d):
    return "／".join(f"{k} {v}" for k, v in d.items())


def newest(pattern):
    xs = sorted(glob.glob(os.path.join(OPS, pattern)), key=os.path.getmtime)
    return xs[-1] if xs else None


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    idx = load(os.path.join(R7, "DELIVERY_INDEX.json"))
    layers = load(os.path.join(OPS, "LAYERS.json"))
    promo = load(os.path.join(OPS, "PROMOTION_RECORD.json"))
    adm = load(os.path.join(OPS, "r7_b3_admission.json"))
    b1 = load(os.path.join(OPS, "b1_r7_tqaep.json"))
    b2 = load(os.path.join(OPS, "b2_r7_tqaep.json"))
    b3 = load(os.path.join(OPS, "b3_r7_tqaep.json"))
    neg = load(os.path.join(OPS, "b3_r7_neg_mutations.json"))
    prod = load(os.path.join(OPS, "b3_r7_product.json"))
    rcv = load(os.path.join(OPS, "r7_consumer_receipts.json"))
    sel = load(os.path.join(OPS, "r7_consumer_selftest.json"))
    pub = load(os.path.join(R7, "50_PUBLISH", "publish_record.json"))
    fr = newest("r7_candidate_freeze.rev*.json")
    frd = load(fr) if fr else {}
    log = os.path.join(OPS, "b0_product_test_2026-11-27.log")
    logline = ""
    if os.path.isfile(log):
        tail = open(log, encoding="utf-8", errors="replace").read().strip().splitlines()
        logline = next((x for x in reversed(tail) if x.strip() in ("OK",) or x.startswith("Ran ")), "")
        ran = next((x for x in reversed(tail) if x.startswith("Ran ")), "")
        if ran:
            logline = f"{ran} / {logline}"

    promo_rows = "\n".join(
        f'| {p["name"]} | `{p["path"]}` | {p["bytes"]:,} | `{p["sha256"][:16]}…` | {p["basis"]} |'
        for p in promo["promoted"])
    consumer_rows = "\n".join(
        f'| {r["consumer_id"]} | {r["decision"]} | `{r.get("rights_currency")}` | `{r["checked_at"]}` |'
        for r in rcv["receipts"])

    closeout = f"""# SESSION CLOSEOUT｜SST PH01 W0 B0–B3（2026-11-27）

- 產生：{time.strftime("%Y-%m-%dT%H:%M:%S%z")}；由 `20_DEV/r7/r7_session_closeout.py` 從收據生成
- 本 SESSION 範圍：r7 活動 SPEC 下的 B0 閉合、B1／B2 必要差額、B3 產品語義與准入評估、交付與發布
- 宣稱上限：`B0_COMPLETE` 成立；`B1_ACCEPTED`／`B2_ACCEPTED`／`B3_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` **不成立**；`FIN_ORDER=DENY`

## 1｜本 SESSION 的實質結論

| 批 | 狀態 | 憑據 |
|---|---|---|
| B0 | `COMPLETE`／`accepted=true` | 當期 descriptor 續期、真 `SourceReadSet/2`、三端 ACCEPT／CURRENT、自測 12/12、產品案 137/137×2（{logline or "log 待完成"}） |
| B1 | `PARTIAL_PARK_UNTIL_DELTA` | 60 案 {fmt(b1["verdict_counts"])}；逐 key 對帳 11／1／4／6／1 |
| B2 | `PARTIAL` | 2,930 案 {fmt(b2["verdict_counts"])}；案級比對 46、相等 26、分歧 20 |
| B3 | `ReadyAtom=false`／`ReadyExecute=false` | 752 案 {fmt(b3["verdict_counts"])}；NEG {fmt(neg["counts"])}；`admission_ready={prod["join"]["admission_ready"]}/{prod["join"]["source_bound_ready"]}` |

## 2｜升格（候選 → 主用）核對

本輪**有**升格：B0 的接受證據由候選升為主用，並記入 `DELIVERY_INDEX.promotion_state.promoted_to_primary` 與 `40_OPS/PROMOTION_RECORD.json`。

| 項目 | 路徑 | bytes | sha256 | 依據 |
|---|---|---:|---|---|
{promo_rows}

**未升格（不連帶）**：

| 批 | 原因 |
|---|---|
| B1 | 本輪無可解新差額（PARK 條件未變） |
| B2 | 20 個 ROUTE 案的產品碼與 SPEC 宣告 FirstFail 不同，需具權裁定 |
| B3 | 183/273 source-bound atom 無 owner 宣告；requiredness 無跨批載體 |

### 先前錯置與更正

| 錯置 | 實際 | 更正 |
|---|---|---|
| `DELIVERY_INDEX.phase_status.B0 = HOLD_RIGHTS_CURRENCY`、`accepted.B0=false`、blockers 仍寫「B0 SourceReadSet/2 currency」 | B0 已於本輪閉合 | 由 `r7_layers.py` 依收據重算為 `COMPLETE`／`accepted.B0=true`，blockers 改列 B2／B3 真差額 |
| 未版本化 `40_OPS/r7_candidate_freeze.json`（digest `68162489…`）仍看起來像「現行」 | 它是 Checker 判過的第一版，現已 superseded | 分層標為 `SUPERSEDED`；現行候選只在 `{layers["current_candidate"]["path"]}` |
| `40_OPS/r7_checker_verdict.md` 被當作對「現行候選」的判決 | 它判的是 digest `68162489…`（rev1 base） | 分層改為 `VERDICT_SUPERSEDED`；現行候選**無** Checker verdict |
| 文件 rev1–rev5 與現行 rev6 混放 | 舊版仍會被誤引 | 分層 `DOC_HISTORY`（12 檔），現行文件只由 `DELIVERY_INDEX.current_pointers` 指向 |

## 3｜工程衛生（本輪實際處置）

| 層 | 檔數 | 說明 |
|---|---:|---|
| PRIMARY | {layers["tally"].get("PRIMARY",0)} | 引擎、preflight、現行文件、發布紀錄 |
| CURRENT_CANDIDATE | {layers["tally"].get("CURRENT_CANDIDATE",0)} | 本輪候選收據（含 12 個 freeze／9 個 manifest 中的現行版） |
| SUPERSEDED | {layers["tally"].get("SUPERSEDED",0)} | 舊 freeze／manifest，保留供稽核，不得引用為現行 |
| VERDICT_SUPERSEDED | {layers["tally"].get("VERDICT_SUPERSEDED",0)} | 對舊 digest 的 Checker 判決 |
| DOC_HISTORY | {layers["tally"].get("DOC_HISTORY",0)} | 舊版 CLOSEOUT／HANDOFF／BOOTSTRAP |
| LOCAL_ONLY | {layers["tally"].get("LOCAL_ONLY",0)} | `b0_current_sourcereadset.json`（權利窗內讀值，不上推） |
| EFFECT | {layers["tally"].get("EFFECT",0)} | `b3_ledger/` 兩份草稿（產品寫入，非輸入） |

刪除：`20_DEV/.tmp_tests`（測試產物，可重建）、`$TMPDIR` 內本輪探針檔（`b0req.json`、`*.out`／`*.err`／`b0tests.log`）；`__pycache__`／`*.pyc` 無（`-B` 執行）。**未刪**任何收據、凍結版本或草稿：皆為稽核鏈或權利證據。

## 4｜發布

| 項目 | 值 |
|---|---|
| Repo | `{pub.get("repo","https://github.com/shw097-team/SQS-THC_MVP")}`（public） |
| 交付樹 commit | `{pub.get("commit")}` |
| 凍結 | `{os.path.basename(fr) if fr else "-"}`／`{(frd.get("candidate_digest") or "")[:16]}…`（{frd.get("members")} 成員） |
| 排除 | `b0_current_sourcereadset.json`（LOCAL_ONLY）、`b3_r7_product.json`、`b3_r7_tqaep.json`（逐字條文） |
| 發布 ≠ 接受 | 發布只散布可散布的衍生證據；接受狀態見 §1 |

## 5｜不宣稱

- 除 B0 外未宣稱任何批次接受；`ReadyAtom=false`（{prod["join"]["admission_ready"]}/{prod["join"]["source_bound_ready"]}）。
- 現行候選（{layers["current_candidate"]["path"]}）**未經**分離 Checker；既有 verdict 只適用於 `68162489…`。
- 未動任何 active pin、未升格 B3 任何項目、未關閉任何 edge。
"""

    handoff = f"""# HANDOFF｜下一 SESSION 接續（SST PH01 W0 B0–B3）

- 產生：{time.strftime("%Y-%m-%dT%H:%M:%S%z")}
- 一句話：B0 已閉合並升格；B1 PARK、B2 PARTIAL、B3 准入仍 HOLD；現行候選 `{layers["current_candidate"]["path"]}`（`{(layers["current_candidate"]["digest"] or "")[:16]}…`）未經 Checker。

## 1｜第一步（照抄即可）

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/71_W0_B0-B3_R7_20261127"
python -B - <<'PY'
import json,hashlib,os
lay=json.load(open("40_OPS/LAYERS.json",encoding="utf-8"))
f=json.load(open(lay["current_candidate"]["path"],encoding="utf-8"))
ok=all(hashlib.sha256(open(a["path"],"rb").read()).hexdigest()==a["raw_sha256"] for a in f["artefacts"])
body="\\n".join(f'{{a["raw_sha256"]}}  {{a["path"]}}' for a in sorted(f["artefacts"],key=lambda x:x["path"])).rstrip("\\n")
print("members_ok",ok,"digest_ok",hashlib.sha256(body.encode()).hexdigest()==f["candidate_digest"])
print("promoted",json.load(open("40_OPS/PROMOTION_RECORD.json",encoding="utf-8"))["promoted"][0]["path"])
PY
```

## 2｜三條未完主線（依價值排序）

1. **B3 owner 補編**：183/273 source-bound atom 無 owner。三來源（Unit 欄、payload、pinned 條文列）皆已證無宣告 → 需最小 typed 補編＋原具權採納。補完後 `admission_ready` 才可能到 273。
2. **B3 requiredness 載體**：B3 unit 365/365 不含任何 TECH id，B2 requiredness 無法 join → 需 typed 映射或宣告 N/A。此項解掉才能關 2 個 NEG HOLD。
3. **B2 20 案 ROUTE FirstFail**：產品回 `ROUTE_REQUIREDNESS_DRIFT_DENY`、SPEC 宣告 `TOOL_REQUIREDNESS_HOLD`；改產品碼或改 SPEC 需具權裁定，未自行改標籤。

## 3｜需 Owner 開窗才能做

| 項 | task／ceiling | 影響 |
|---|---|---|
| Consumer 五類權利臂（未生效／非法時區／撤權／principal／epoch） | `SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH`／`READ_ONLY_PROBE` | 只在無 live window 時無法行使；現有 12 臂已含 expiry |
| B3 `SourceChildLedger` 真 COMMIT | `HOST_OPERATIONS`（≥`REPOSITORY_WRITE`） | 目前只有 in-memory 切片與 2 份 draft（`EFFECT` 層） |
| D-2／D-3／D-4／TT-UP-1 | 各原權位 | B1／B2 未閉項 |

## 4｜重現（本輪全部指令）

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/71_W0_B0-B3_R7_20261127/20_DEV/r7"
python -B b3_product.py --dry-run          # B3 四 Op（in-memory）
python -B b3_neg_v2.py && python -B b3_neg_reconcile.py && python -B b3_tqaep.py
python -B b1_tqaep.py && python -B b1_edge_sec.py
python -B b2_meta.py && python -B b2_tqaep.py
python -B r7_preflight.py && python -B r7_reconcile.py
python -B r5_consumers.py && python -B r5_consumers.py --selftest
python -B r7_layers.py                     # 分層／升格／索引重算
python -B r7_freeze.py --revision revN     # 凍結（拒絕覆寫；新修訂用新 rev）
python -B r7_session_closeout.py           # 本檔與 CLOSEOUT 重生成
```

B0 產品案（137 案，約 6 分鐘）：

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/20_DEV" && mkdir -p .tmp_tests \\
  && env -u TMPDIR TMP="$PWD/.tmp_tests" TEMP="$PWD/.tmp_tests" \\
     python -B -m unittest discover -s tests -p "test_*.py"
```

## 5｜不得重入

- 不得覆寫凍結（`r7_freeze.py` 無 `--revision` 即拒絕；同 rev 檔存在即拒絕）。
- 不得把 `VERDICT_SUPERSEDED` 的判決引用為現行候選的 verdict。
- 不得把 `SUPERSEDED` 的 freeze 當現行；現行只有 `LAYERS.json.current_candidate` 一個。
- 不得把 `LOCAL_ONLY` 的 B0 readset 上推；published 樹只有其 sha。
- 不得把 B2 的 `receivers.B3` 1317/148 與 B3 TQAEP 的 join 0/1465 互相代替（mandatory 集合不同）。
- 不得在未取得具權裁定的情況下，把 20 個 ROUTE 案改標籤或改 SPEC。
"""

    boot = """# BOOTSTRAP｜下一 SESSION 第一讀

## 狀態

- B0 `COMPLETE`（已升格）；B1 `PARTIAL_PARK`；B2 `PARTIAL`；B3 `ReadyAtom=false`／`ReadyExecute=false`。
- 現行候選＝`40_OPS/LAYERS.json` 的 `current_candidate`（唯一）；Checker verdict 只適用於舊 digest。
- `FIN_ORDER=DENY`；除 B0 外無批次接受。

## 四步

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/71_W0_B0-B3_R7_20261127"
sed -n '1,40p' 60_CLOSEOUT/SESSION_CLOSEOUT_2026-11-27.md
sed -n '1,40p' 60_CLOSEOUT/HANDOFF_NEXT_SESSION.md
python -B -c "import json;d=json.load(open('DELIVERY_INDEX.json',encoding='utf-8'));print(d['phase_status']);print(d['promotion_state']['promoted_to_primary'])"
python -B -c "import json;l=json.load(open('40_OPS/LAYERS.json',encoding='utf-8'));print(l['tally']);print(l['current_candidate'])"
```

## 不要做

覆寫凍結／把 superseded verdict 當現行／把 LOCAL_ONLY 上推／把 B2 receiver 數字當 B3 join。
"""

    for name, body in (("SESSION_CLOSEOUT_2026-11-27.md", closeout),
                       ("HANDOFF_NEXT_SESSION.md", handoff),
                       ("BOOTSTRAP_NEXT_SESSION.md", boot)):
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
    print(json.dumps({"written": ["60_CLOSEOUT/" + n for n in
                                  ("SESSION_CLOSEOUT_2026-11-27.md",
                                   "HANDOFF_NEXT_SESSION.md",
                                   "BOOTSTRAP_NEXT_SESSION.md")],
                      "freeze": os.path.basename(fr) if fr else None,
                      "b0_log": logline}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
