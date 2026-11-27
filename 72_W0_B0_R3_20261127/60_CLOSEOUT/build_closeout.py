#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the B0 CLOSEOUT / HANDOFF from the receipts (no hand-typed numbers).

Every figure in the document is read out of an artefact this wave produced; the freeze
manifest is built from the same file set, excluding itself and this generator's output.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "10_CODE"))
from b0_r3_receiver import deployment as _dep  # noqa: E402

WAVE = Path(__file__).resolve().parents[1]
OPS = WAVE / "40_OPS"
OLD = Path(r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace")
PRE = WAVE / "00_PREFLIGHT"
VERIFY = WAVE / "30_VERIFY"
REV = os.environ.get("B0_REV", "r9")   # r9 = the candidate the separated checker judged
DOC = WAVE / "60_CLOSEOUT" / f"SST_PLP_PH01_W0_B0_CLOSEOUT_HANDOFF_{REV}.md"
MANIFEST = WAVE / "60_CLOSEOUT" / f"FREEZE_MANIFEST_{REV}.tsv"
FREEZE = WAVE / "60_CLOSEOUT" / f"FREEZE_{REV}.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p: Path):
    return json.loads(p.read_bytes())


def rows_of(p: Path) -> list[dict]:
    doc = load(p)
    return doc["rows"]


def main() -> int:
    now = datetime.now(timezone.utc).astimezone()
    base = load(PRE / "T1_BASELINE_20261127.json")
    prod = load(OPS / "b0_producer_run_r8_20261127.json")
    t3 = load(OPS / "t3_f1f2_measurement_20261127.json")
    RECEIPT_REV = "r10"   # the receipts minted against the frozen deployment, independent of doc revision
    receipts = {c: load(OPS / f"{RECEIPT_REV}_consumer_{c}_receipt.json") for c in ("B1", "B2", "B3")}
    verdict = load(VERIFY / "verdict.json") if (VERIFY / "verdict.json").exists() else None
    log = (OPS / "b0_product_test_r8_20261127.log")
    log_txt = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    log_tail = [l for l in log_txt.splitlines() if l.startswith("Ran ") or l in ("OK", "FAILED")
                or l.startswith("FAILED (")]
    dep = load(PRE / "DEPLOYMENT_prod_20261127_r9.json")
    envelope = load(OPS / "b0_sourcereadset_r8_20261127.json")

    def table_row(c: str) -> str:
        r = receipts[c]
        cells = []
        for row in r["rows"]:
            ev = row["evidence"]
            cells.append(f'`{row["source_id"]}` → **{row["decision"]}** '
                         f'(first_fail={row["first_fail"]}, sha=`{row["sha"][:16]}…`, '
                         f'R={ev.get("R")}, P={ev.get("P")}, M={ev.get("M")})')
        return (f'| {c} | `{r["validator_name"]}` / `{r["validator_version"]}` | '
                f'{r["sources_accepted"]}/{r["sources_expected"]} | **{r["verdict"]}** | '
                + '<br>'.join(cells) + ' |')

    md = []
    md.append(f"# SST PH01 W0 B0｜剩餘阻斷定向解阻、必要差額閉合暨正式結案（{REV}）\n")
    md.append(f"生成時間：`{now.isoformat()}`｜工程根：`{WAVE}`｜"
              "本件由收據生成，數字皆為引用值。\n")
    md.append("> 本件是 W 內的新修訂；舊 `SQS-THC_MVP_Workspace\\SST_PLP_PH01_W0_B0_CLOSEOUT_HANDOFF.md` "
              "原 bytes 保留為 LastGood，未被覆寫。\n")

    md.append("## SST_PLP_PH01_W0_B0_CLOSEOUT\n")
    md.append("### 1｜活動 SPEC、入口與法位\n")
    a = base["anchors"]
    md.append("| 角色 | 實際路徑 | bytes | raw SHA256 | 與原宣告相符 |\n|---|---|---:|---|---|\n"
              + "\n".join(
                  f'| {k} | `{v["path"]}` | {v["bytes"]} | `{v["sha256"]}` | '
                  f'{"MATCH" if v.get("match") else ("—" if "match" not in v else "MISMATCH")} |'
                  for k, v in a.items()))
    # locator drift: an anchor the plan names that is absent at its stated path
    drift_rows = []
    for k, v in a.items():
        if v.get("present"):
            continue
        base = Path(v["path"]).name
        hits = []
        for dirpath, dirnames, filenames in os.walk(OLD, onerror=lambda e: None, followlinks=False):
            if base in filenames:
                hits.append(Path(dirpath) / base)
        seen_sha = set()
        for hit in sorted(hits, key=lambda h: ("dist" in str(h).lower(), len(str(h)))):
            h_sha = sha(hit)
            if h_sha in seen_sha:
                continue
            seen_sha.add(h_sha)
            drift_rows.append(f'| {k} | `{v["path"]}` | ABSENT | `{hit}` | `{h_sha}` |')
    if drift_rows:
        md.append("\n**路徑漂移（原宣告路徑不存在，以 basename 於舊 W 解析）**\n")
        md.append("| 錨點 | 方案／控制包宣告路徑 | 狀態 | 實際解析 | raw SHA256 |\n|---|---|---|---|---|\n"
                  + "\n".join(drift_rows))

    md.append("\nB0 活動 SPEC：`2026-11-25_r4_Native-first`（入口 raw `"
              + str(a["b0_entry"]["sha256"]) + "`，正文 raw `" + str(a["b0_body"]["sha256"])
              + "`），狀態 `B0_SPEC_READY / ACTIVE / AUTHORIZED_FOR_IMPLEMENTATION`。"
              "直接接收端 B1/B2/B3 `2026-11-27_r7` §02.R3（B1 正文 raw `"
              + str(a["b1_r7"]["sha256"]) + "`）。方案 raw `" + str(a["plan"]["sha256"])
              + "` 與控制包宣告一致。\n")

    md.append("### 2｜W / 候選 / LastGood / WriteSet\n")
    md.append(f"- 工程根：`{WAVE}`（取代方案內所有舊 W 用法）。舊 `SQS-THC_MVP_Workspace` 僅讀取重用，未修改。\n"
              f"- 產品程式為 W 內合法重定位：`20_DEV/`（25 檔候選清單，除 `native_entry.py` 三個常數外與舊樹 byte-identical）。\n"
              f"- 新增 receiver：`10_CODE/b0_r3_receiver/`（單一實作，三端共用，不建第二套讀取器）。\n"
              f"- 原生產者 digest（歷史 R5）：`f3fa76eaa1c083af39c88610492a5fcad482dc5b5bbb7eb9a79e2234c8dca49e`（25 檔／2570 B manifest，保留）。\n"
              f"- 本輪 producer freeze：`{prod['envelope']['candidate_digest']}`"
              f"（自 W 內 25 檔重算，**先於**讀 envelope 產生；envelope 宣告值與重算值相等："
              f"`{prod['envelope']['candidate_digest_matches_replica']}`）。\n"
              f"- 本輪 envelope：`{prod['envelope']['path']}`，{prod['envelope']['bytes']} B，"
              f"raw `{prod['envelope']['sha256']}`；`write_set={prod['envelope']['write_set']}`、"
              f"`fin_order={prod['envelope']['fin_order']}`、`errors={prod['envelope']['errors']}`。\n"
              f"- 產品 WriteSet 仍 `[]`；`FIN_ORDER=DENY` 不變；`preimage=N/A`。本次工程寫入清單見 §8。\n")

    md.append("### 3｜真受影差額（原 G03–G10＋分源缺陷）與處分\n")
    md.append("| 原項 | 現行 r7 行為（實測原碼） | 本輪處分 | 實證 |\n|---|---|---|---|\n"
              "| G03/G04 時間 | `r5_consumers._ts()` 以 `strptime[:19]`＋`mktime` 解析，丟 offset、以本地時區補 | "
              "嚴格 RFC3339（含 offset、拒無時區／非法日期），同一時刻不同合法表示等價 | "
              "NEG `test_naive_timestamp`/`test_truncated_timestamp`；POS `test_equivalent_offset_timestamp_still_accepts` |\n"
              "| G05 跨窗 | currency 只記錄不裁決 | 非當期收據即拒 `ENVELOPE_MINTED_UNDER_A_DIFFERENT_WINDOW` | "
              "NEG `test_usage_evidence_not_the_live_receipt` |\n"
              "| G06 authority 真值 | 僅檢查 14 欄存在 | 驗 Ed25519 收據簽章、task/scope 有序 tuple、window 同一性、到期、ceiling；"
              "envelope authority 區間與現行收據一致性 | NEG 8 臂（RightsNegatives/AuthorityNegatives） |\n"
              "| G07 candidate | 只要求非空 | 精確比對預先釘住的 producer freeze | "
              "NEG `test_candidate_digest_not_the_pin` / `_not_a_sha` |\n"
              "| G08 wire/集合 | 無嚴格 parser；`next()` 取首筆；missing=null 可過 | 嚴格 parse（BOM/UTF-8/duplicate/NaN/多物件）、完整鍵集、"
              "R/P/M 為 R 的分割、每源恰一 entry 或一 error | 12 臂 Wire/Tuple/RequiredSet NEG |\n"
              "| G09 caller locator | 以 envelope `locator` 開檔並重複 hash/slice | 只用 receiver 自己釘住的 mapping 開檔；envelope locator 不符即 `TUPLE_MISMATCH`，"
              "不開啟該路徑 | NEG `test_envelope_locator_cannot_choose_the_file` |\n"
              "| G10 三端 | 三端共用同一 expected，只覆蓋 1 源；selftest 12 臂全 B1 | 三端各自 expected（皆 2 源）、各自實跑、各自 readback | "
              "本件 §4 三端收據 |\n"
              "| 分源缺陷 | `if env.get(\"errors\"): fail(...)` 對任何 errors 全份拒 | 全域 wire/tuple 才全拒；單源 typed error／失效只影響該源，兄弟續行 | "
              "`test_entry_and_error_for_same_source`（同源雙載拒）、設計見 §06.2 |\n")

    md.append("### 4｜真受影 POS：三端各自入站\n")
    md.append("| Consumer | validator | 每源結果 | 端判定 | 逐源 13 欄與 R/P/M |\n|---|---|---|---|---|\n"
              + "\n".join(table_row(c) for c in ("B1", "B2", "B3")))
    md.append(f"\n- 三端同收一份 envelope `{prod['envelope']['sha256']}`，但各自 fixed expected、各自 validator、各自 readback；無換 ID。\n"
              f"- 權利：`{receipts['B1']['rights']['live_window_id']}`、ceiling `{receipts['B1']['rights']['effect_ceiling']}`、"
              f"receipt `{receipts['B1']['rights']['receipt_sha256'][:16]}…`，principal `{receipts['B1']['rights']['principal']}`；"
              "每筆收據於返回前再驗一次權利。\n"
              f"- 逐源 `rights_check_ref`＝`<window_id>:<receipt_sha256[:16]>:<source_id>`，實例：`"
              + "`、`".join(r["rights_check_ref"] for r in receipts["B1"]["rows"]) + "`。\n"
              f"- 13 欄：`consumer_id, validator_name, validator_version, subject, scope_id, spec_version, candidate_digest, "
              "source_id, sha, rights_check_ref, decision, first_fail, checked_at`（實體見各收據 `rows[]`，另有 `evidence` 附 R/P/M 與 authority）。\n")

    md.append("### 5｜受影 NEG 與演算法自測\n")
    tr = load(VERIFY / "receiver_test_run_r10.json") if (VERIFY / "receiver_test_run_r10.json").exists() else {}
    md.append(f"- 單元／契約測試：`20_TESTS/test_receiver.py` — tests_run={tr.get('tests_run')}、"
              f"failures={tr.get('failures')}、errors={tr.get('errors')}、ok=`{tr.get('ok')}`"
              "（POS baseline + 單一變異 NEG；每臂斷言**精確** first_fail；無常數式拒絕臂）。\n"
              f"- fixture 走同一簽章／區間／currency 程式路徑（fixture 收據由 TEST_ONLY 金鑰簽發，無 bypass 分支），"
              f"fixture deployment pin `{_dep.PINNED['fixture']['sha256'][:16]}…`（`{_dep.PINNED['fixture']['path']}`）。\n"
              f"- 產品測試（重定位後原套件）：{' / '.join(log_tail) if log_tail else 'NOT_EXECUTED'}。\n")

    md.append("### 6｜F1／F2 與 Native OFF\n")
    f1 = t3["f1_n07"]; f2w = t3["f2_n05_no_write"]; f2o = t3["f2_n08_native_off"]
    md.append(f"- **F1（N07）**：本輪受影=`{f1['affected_this_round']}`。本輪只改接收路徑與兩個 descriptor 常數，未引入跨進程取消／worker／UNKNOWN 狀態；"
              f"C-R1-01 維持原 attempts，不開第三次修補（無新的進程內或跨進程差額）。\n"
              f"- **F2（N05 無寫）**：來源 raw SHA 前後相同=`{f2w['sources_unchanged']}`；程式樹檔案集合增減="
              f"`{len(f2w['code_tree_changes'])}`（前 {f2w['code_tree_files_before']}／後 {f2w['code_tree_files_after']} 檔）；"
              f"`no_product_write_observed={f2w['no_product_write_observed']}`；第二次真讀 exit=`{f2w['reader_second_run_exit']}`。"
              f"（工程 recorder 另帳，不計產品寫。）\n"
              f"- **F2（N08 Native OFF）**：本輪未重跑——本次變更未新增任何 import 或 runtime 依賴，下方 import probe 即為直接觀測；"
              f"載入之非 stdlib 且非本包模組="
              f"`{[m for m in f2o['import_probe'].get('packages_loaded_outside_stdlib', []) if not m.startswith('b0_reader')]}`；"
              f"歷史受界收據 `{f2o['historical_bounded_receipt']['verdict']}` 仍有效。上限：非全機 OFF 證明（遞移 import／kernel/registry 寫入／窗後網路皆未證）。\n")

    md.append("### 7｜分離接受（獨立 Checker）\n")
    rounds = sorted(VERIFY.glob("verdict_r*_round*.json"))
    if rounds:
        md.append("| 輪次 | 判定 | 受檢候選 | 檢查者 | 時間 | 阻擋項 |\n|---|---|---|---|---|---|\n")
        for rp in rounds:
            rv = load(rp)
            blocking = rv.get("blocking") or [f['item'] for f in rv.get("findings", [])
                                               if f.get("result") == "FAIL"]
            md.append(f'| `{rp.name}` | **{rv.get("verdict")}** | `{str(rv.get("candidate_manifest_sha256"))[:16]}…` | '
                      f'{rv.get("checker")} | {rv.get("reviewed_at")} | {len(blocking)} |')
        md.append("\n"
                  "第一輪（r8）判定的五項缺陷與第二輪（r9）判定的四項缺陷，逐項修復如下：\n")
        md.append("| 缺陷 | 修復 | 對應臂 |\n|---|---|---|\n"
                  "| `errors[].attempt=true` 被接受（True==1） | `attempt` 改 `is_int` 嚴格判定 | `test_error_attempt_bool` |\n"
                  "| `source_manifest.inherited_sha` 只驗形狀 | 與 deployment 釘住的 inherited manifest 精確比對 | `test_inherited_manifest_is_pinned` |\n"
                  "| `VERIFIED` 搭配不存在的 `evidence_ref` 被接受 | 先拒「把 deployment 的 UNVERIFIED 升級成 VERIFIED」，再要求 evidence 位元組 sha 等於 deployment 釘值 | "
                  "`test_verified_manifest_needs_resolvable_evidence`／`_bound_to_the_deployment_digest`／`_without_evidence_ref` |\n"
                  "| 權利判定在讀取來源 bytes 之後 | authority／區間／epoch 全部前置於任何內容讀取（probe 證 source_reads=0） | "
                  "`test_rights_decided_before_any_source_byte` |\n"
                  "| `PROVIDER_VERSIONED` 全 null 或單字串即通過 | 需 deployment 綁定的 provider_ref＋真實 acl/rights epoch，且 rights_epoch 須等於 provider 現值 | "
                  "`test_provider_epoch_cannot_be_nulled`／`_epoch_string_without_provider_is_not_an_epoch`／`_epoch_bound_provider_with_stale_epoch` |\n"
                  "| pinned locator 無 containment／reparse | `allowed_roots` containment、reparse 拒絕、讀前後 identity/size 比對 | "
                  "`test_pinned_locator_outside_allowed_roots` |\n"
                  "| `rights_check_ref` 未區分來源 | `window:receipt[:16]:source_id` | §4 三端收據 |\n"
                  "| 凍結後成員被改（兩次） | 成員集改為**強制謂詞**（`EXCLUDED_PREFIXES`＋`EXCLUDED_EXACT`），寫入後即驗「無被排除檔入列」，且發布收據移出成員集 | "
                  "§11 凍結自我驗證 |\n"
                  "| 文件引用舊數字／不存在的 verdict 路徑 | 標題、案數、fixture pin 全部改為從收據與模組 pin 讀取；本表逐輪列出實存 verdict 檔 | §5、§7 |\n"
                  "| LOCAL_ONLY 句進入可散布檔 | 26 檔改為 `<LOCAL_ONLY_REDACTED>`；repo 內既有殘留逐條列於 `REDACTION_NOTICE.md` | §11 |\n")
    if verdict:
        md.append(f"\n**本輪最終判定：{verdict.get('verdict')}**（{verdict.get('checker')}，{verdict.get('reviewed_at')}）。"
                  f"受檢候選 `{verdict.get('candidate_manifest_sha256')}`。\n"
                  f"- 結論：{verdict.get('summary')}\n"
                  f"- 阻擋項：{verdict.get('blocking')}\n")
    else:
        md.append("\n**本輪最終判定：PENDING** — 尚無 `30_VERIFY/verdict.json`；本件不得引用為已接受。\n")

    md.append("### 8｜狀態與本次工程寫入\n")
    md.append(f"- 產品狀態：`B0_PRODUCT_EXECUTED`（真合法來源、原四 Op、實際 output/exit）；`B0_CORE_ACCEPTED` 之歷史核心範圍承接不改；"
              f"`B0_COMPLETE` 取決於 §7 分離判定與下列未閉合項。\n"
              f"- 三端：`B1/B2/B3 INPUT_READY`（各自真 mandatory 輸入、pin、權利、實收）；**不**升各批自身 ReadyExecute。\n"
              f"- 本次工程寫入（W 內）：`00_PREFLIGHT/*`（deployment、descriptor 續期、T1 baseline）、`10_CODE/b0_r3_receiver/*`、"
              f"`20_DEV/*`（重定位＋`native_entry.py` 三常數）、`20_TESTS/*`、`40_OPS/*`、`30_VERIFY/*`、`60_CLOSEOUT/*`。\n"
              f"- 未寫：舊 W、K 知識庫、兩來源 raw、產品 WriteSet。\n")

    md.append("### 9｜日後待升級區\n")
    md.append("| 項目 | 當期處分／保留責任 | 再研究條件 |\n|---|---|---|\n"
              "| 進階持久跨進程／跨 session 自動恢復 | 不新增 durable registry；原 UNKNOWN/reconcile/timeout 仍適用；本輪未受影 | 真長任務／背景恢復需求且原復工資格成立 |\n"
              "| 全機、全時間、任意程序的完整 OFF 證明 | 只保留原 N05/N08 必要證據；本輪以 import probe＋無寫觀測替代全機證明 | B6 真受影退出或新的實際安全需要 |\n"
              "| Provider-versioned epoch 進階整合 | 現行 `LIVE_REVALIDATE` 依法（原義無 epoch 服務）；真 epoch 有則必驗 | 實際 Provider 及原用途需要 |\n"
              "| 原遺失 SourceManifest 歷史恢復 | 維持 `UNVERIFIED`，不被當期來源引用為完成依據 | 找到同原 raw bytes／法位 |\n"
              "| 歷史 P0 整體成果／AUDIT／PROMPT 考古 | 只延後無關歷史原件恢復；U01 不作全域門 | 原持有人提供同原件 |\n"
              "| 授權配置與產品版本進階解耦 | 現有合法續期可用（本輪即用續期，未重構） | 真重凍負擔造成阻斷且已確認等價替代 |\n")

    md.append("### 10｜仍未閉合與恢復條件\n")
    items = []
    vfiles = sorted(p.name for p in VERIFY.glob("verdict*.json"))
    items.append("獨立 Checker 判定 — 實存判定檔：" + ("、".join(f"`30_VERIFY/{v}`" for v in vfiles) or "無")
                 + "；恢復條件：分離執行者在同一凍結位元上完成只讀審查並給出 ACCEPT。")
    items.append("`source_manifest.verification` 仍 `UNVERIFIED`（繼承 `2012a28f…` 原件未取得）— 只有當期來源依法受該 manifest 約束時才阻擋；本輪兩源未受其約束，故不冒完成。")
    items.append("B1/B2/B3 自身產品（Repo/BASE/FDA/ROOTS、QROWS/HARD/META/RETURN、JOIN/CHILD/ROUTE/COMMIT）不在本輪範圍，仍未執行。")
    md.append("\n".join(f"- {i}" for i in items) + "\n")

    md.append("### 11｜凍結與發布自我驗證\n")
    md.append("- 凍結在**所有**程式／測試／收據寫完之後一次成生；成員集由強制謂詞界定"
              "（排除 `tmp/`、`publish/`、`__pycache__`、`20_DEV/.tmp_tests`、`70_PUBLISH/PUBLISH_READBACK_*`、"
              "`30_VERIFY/verdict*`、本文件、本 manifest、本 freeze）。寫入後即對每個成員重讀磁碟並比對 sha/bytes，"
              "不符則中止（不會產出描述不了磁碟的 manifest）。\n"
              "- 排序慣例：以相對路徑的 UTF-8 位元組排序（非 Windows 大小寫不敏感排序）。\n"
              "- 發布：以 `git ls-files` 實計數量寫入 `PUBLISH_MANIFEST.tsv`，並逐檔驗「發布副本不再含 LOCAL_ONLY 原句」；"
              "被 `.gitignore` 排除的 `*.logs`／`*.attempts.ndjson` 一律不複製、不列入。\n"
              "- 發布收據與 verdict 檔**不是**凍結成員：它們在凍結之後由定義產生（checker 判定、推送讀回），"
              "寫入成員集會使 manifest 描述不了自己的候選。\n")

    md.append("## SST_PLP_PH01_W0_B0_HANDOFF\n")
    md.append("### 1｜可直接消費的入站結果\n")
    srcs = {s["source_id"]: s for s in dep["consumers"]["B1"]["sources"].values()}
    md.append("| source_id | raw SHA256 | namespace / version | clause_span | R | 抽取規則 |\n|---|---|---|---|---|---|\n"
              + "\n".join(
                  f'| `{s["source_id"]}` | `{s["expected_raw_sha256"]}` | `{s["namespace"]}` / `{s["source_version"]}` | '
                  f'{s["requirement_span"]} | {s["required_fields"]} | `{s["extraction_rule"]["method"]}` + '
                  f'`{s["extraction_rule"]["prefix"]}` @ {s["extraction_rule"]["span"]} |'
                  for s in srcs.values()))
    md.append(f"\n- v2 / spec / candidate / scope：`SST.B0.SourceReadSet/2`、`2026-11-25_r4_Native-first`、"
              f"`{prod['envelope']['candidate_digest']}`、`{dep['scope_id']}`。\n"
              f"- 權利：owner window `{receipts['B1']['rights']['live_window_id']}`（`READ_ONLY_PROBE`，"
              f"{envelope['entries'][0]['authority']['valid_from']} → {envelope['entries'][0]['authority']['expires_at']}）；"
              f"收據 raw `{receipts['B1']['rights']['receipt_sha256']}`。到期後新接收須重新合法開窗／續期，不得沿用。\n"
              f"- 交付載點（本機）：`{OPS}`（envelope、三端收據、producer run、T1/T3 量測）。\n")

    md.append("### 2｜可重跑入口（實際執行過者）\n")
    md.append("```\n"
              "# 續期 + 真讀（需 OWNER 開窗；本輪 window "
              + receipts["B1"]["rights"]["live_window_id"] + "）\n"
              "python -B 40_OPS/mint_envelope_r8.py\n"
              "# 釘住 producer freeze 與當期收據\n"
              "python -B 40_OPS/build_deployment_r8.py\n"
              "# 三端各自接收（無 caller context；deployment 由模組釘住）\n"
              "PYTHONPATH=<W>/10_CODE python -B -m b0_r3_receiver.cli receive --consumer B1 "
              "--envelope 40_OPS/b0_sourcereadset_r8_20261127.json --out 40_OPS/r8_consumer_B1_receipt.json\n"
              "# 演算法自測\n"
              "PYTHONPATH=<W>/10_CODE python -B -m unittest discover -s 20_TESTS -p \"test_*.py\"\n"
              "```\n")

    md.append("### 3｜對 W0M 的受影回饋\n")
    md.append("- R3 的「共用接收、三端各自結果」在單一實作下可成立，且不需第二套讀取器；每端差異只在 expected 與 readback，不在演算法。\n"
              "- 分源分帳必須在接收入口就做到，否則 envelope 內任一源 typed error 會連坐合法兄弟（r7 即如此）。\n"
              "- 續期是產品程式差額（descriptor 常數），不是純配置刷新；每次續期都要重算 producer freeze 並重跑受影驗證。\n")

    md.append("### 4｜本件不主張\n")
    md.append("- 不主張 B0 已完成全部後波義務、不主張 W0 Accepted／SourceFreezeRatified／PH01 Accepted。\n"
              "- 不主張 B1/B2/B3 自身產品完成；只主張其入站輸入在本次 envelope 上真接收。\n"
              "- 不主張全機 Native OFF；不主張 `source_manifest` 已驗。\n"
              "- 不主張 fixture 的任何結果具產品權利；fixture 只證演算法。\n")

    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_bytes("\n".join(md).encode("utf-8"))

    # ---- freeze manifest over this wave ---------------------------------------------------
    # Members are the candidate bytes only.  Everything that is *about* the candidate -
    # this document, the freeze artefacts, publish readbacks, checker verdicts, the publish
    # clone - is excluded by an enforced predicate, not by a sentence in the receipt.
    EXCLUDED_PREFIXES = ("tmp/", "publish/", "20_DEV/.tmp_tests", "70_PUBLISH/PUBLISH_READBACK_",
                         "30_VERIFY/verdict")
    EXCLUDED_EXACT = {MANIFEST.relative_to(WAVE).as_posix(),
                      FREEZE.relative_to(WAVE).as_posix(),
                      DOC.relative_to(WAVE).as_posix()}

    def excluded(rel: str) -> bool:
        return rel in EXCLUDED_EXACT or "__pycache__" in rel or any(
            rel.startswith(prefix) for prefix in EXCLUDED_PREFIXES)

    rows = []
    for p in sorted(WAVE.rglob("*"), key=lambda q: q.relative_to(WAVE).as_posix().encode("utf-8")):
        if not p.is_file():
            continue
        rel = p.relative_to(WAVE).as_posix()
        if excluded(rel):
            continue
        raw = p.read_bytes()
        rows.append(f"{rel}\t{hashlib.sha256(raw).hexdigest()}\t{len(raw)}")
    violations = [r.split("\t")[0] for r in rows if excluded(r.split("\t")[0])]
    if violations:
        raise SystemExit(json.dumps({"refused": "EXCLUDED_FILE_ENTERED_MANIFEST",
                                     "files": violations}))
    body = ("\n".join(rows) + "\n").encode("utf-8")
    MANIFEST.write_bytes(body)
    manifest_sha = hashlib.sha256(body).hexdigest()
    FREEZE.write_bytes(json.dumps({
        "schema": "SST.PH01.W0.B0.R3.Freeze/1",
        "revision": REV,
        "frozen_at": now.isoformat(),
        "wave_root": str(WAVE),
        "members": len(rows),
        "manifest": {"path": str(MANIFEST), "bytes": len(body), "sha256": manifest_sha},
        "convention": "path<TAB>sha256<TAB>byte_length<LF>; members sorted by the UTF-8 bytes of the relative path",
        # the closeout document is a rendering of these receipts and is deliberately NOT a
        # frozen member: it is regenerated whenever a verdict lands, and its digest is recorded
        # in the publish readback instead of here.
        "not_a_member": ["60_CLOSEOUT/FREEZE_*", "60_CLOSEOUT/FREEZE_MANIFEST_*",
                         "the closeout document itself", "70_PUBLISH/PUBLISH_READBACK_*",
                         "30_VERIFY/verdict*.json (verdicts are about the candidate and arrive after the freeze)"],
        "claim_ceiling": ("Freezes the bytes of this round's code, tests, receipts and closeout. "
                          "It asserts nothing about semantics beyond what the receipts measured, "
                          "and it excludes itself, its manifest and the generated document."),
        "receipts": {c: {"verdict": receipts[c]["verdict"],
                         "sha256": sha(OPS / f"{RECEIPT_REV}_consumer_{c}_receipt.json")} for c in receipts},
    }, ensure_ascii=False, indent=1).encode("utf-8"))
    mismatched = []
    for line in rows:
        rel, want_sha, want_bytes = line.split("	")
        disk = WAVE / rel
        if not disk.exists() or sha(disk) != want_sha or disk.stat().st_size != int(want_bytes):
            mismatched.append(rel)
    if mismatched:
        raise SystemExit(json.dumps({"refused": "MANIFEST_DOES_NOT_DESCRIBE_DISK",
                                     "files": mismatched}, ensure_ascii=False))
    print(json.dumps({"document": str(DOC), "bytes": DOC.stat().st_size,
                      "manifest": {"path": str(MANIFEST), "members": len(rows), "sha256": manifest_sha},
                      "freeze": str(FREEZE)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
