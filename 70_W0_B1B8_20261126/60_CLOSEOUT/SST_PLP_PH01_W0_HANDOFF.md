---
artifact: SST_PLP_PH01_W0_HANDOFF
wave: SST/SQS-THC/PH01/E00 (P1-W00M)
handoff_from: 2026-11-26 SESSION (HERMES native-first)
handoff_to: next SESSION (same Owner; fresh context)
read_order: [NEW_SESSION_BOOTSTRAP.md, this file, 60_CLOSEOUT/SST_PLP_PH01_W0_CLOSEOUT.md, DELIVERY_MANIFEST.json]
effect: read-only instructions; no Grant, no acceptance
---

# SST PH01 W0 B1–B8｜HANDOFF（可執行）

## 1｜座標

| 名稱 | 路徑 | 性質 |
|---|---|---|
| K（上游） | `C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04` | **唯讀** |
| W（唯一工程寫入根） | `C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace` | 可寫 |
| R（本 wave） | `W\70_W0_B1B8_20261126` | 可寫 |
| 發布通道 | `W\dist\SQS-THC_MVP`（clone of `shw097-team/SQS-THC_MVP`） | 只經 `50_PUBLISH\push_w0_b1b8.py` |
| 禁止寫入 | `C:\Projects\Agent_Workspace\SQS-THC`、`…\FHS`、K | — |

## 2｜現行指標（照抄即可用）

```
b1_run    40_OPS/b1_run_20261126T141840.json          127,559 B  591808fa…
b1_tqaep  40_OPS/b1_tqaep_20261126T141842.json         41,636 B  821f3e61…
b1_freeze 40_OPS/b1_candidate_freeze_20261126T141853.json  2,218 B  9666c7ed…
b2_parse  40_OPS/b2_parse_20261126T121931.json        274,689 B  14147dcb…
b2_trs    40_OPS/b2_toolreadset_20261126T160603.json  3,264,963 B
b2_tqaep  40_OPS/b2_tqaep_20261126T160627.json        3,005,4xx B
b2_freeze 40_OPS/b2_candidate_freeze_round6.json       candidate_digest 913a76c5…
b3_parse  40_OPS/b3_parse_20261126T142325.json          —        6dff324f…
```
權威來源是 `DELIVERY_MANIFEST.json` 的 `current_pointers`，不要用 mtime 猜。

## 3｜第一批動作（照順序）

1. `cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/70_W0_B1B8_20261126"`
2. 讀 `DELIVERY_MANIFEST.json` → `promotion_state`、`current_pointers`、`layer_counts`。**先確認 promoted_to_primary 仍為 `[]`**；若有人聲稱已升格，先找 acceptance receipt，找不到就是不成立。
3. 重算現行 freeze 完整性（不執行產品）：
   ```bash
   python -B - <<'PY'
   import json,hashlib
   f=json.load(open('40_OPS/b2_candidate_freeze_round6.json',encoding='utf-8'))
   print(all(hashlib.sha256(open(a['path'],'rb').read()).hexdigest()==a['raw_sha256'] for a in f['artefacts']))
   d=hashlib.sha256("".join(f"{a['raw_sha256']}  {a['path']}\n" for a in sorted(f['artefacts'],key=lambda x:x['path'])).rstrip("\n").encode()).hexdigest()
   print(d==f['candidate_digest'])
   PY
   ```
   兩行都要 `True`。
4. 讀最後一輪分離裁決：`40_OPS/b2_checker_round5_verdict.md`、`40_OPS/b1_checker_round5_verdict.md`。**它們是唯一有效的對外判讀**。

## 4｜不要做的事（會直接破壞證據鏈）

- 不要直接跑交接舊版的「全量重跑」；先判斷證據是否仍可重開。
- 不要改 `40_OPS/*_checker_*_verdict.md`（immutable）。
- 不要刪 `SUPERSEDED_RECEIPT`（含失敗版本，是「未挑選」的證據）。
- 不要把 `CANDIDATE_NOT_RATIFIED` 或 `CANDIDATE_EXTERNAL_UNRATIFIED` 當 primary：`00_PREFLIGHT/b1_locator_bindings.json`、`b1_source_allowlist.json`、`90_EXTERNAL_INPUTS/spec_delta_r5_…`。
- 不要用 `q_row.evidence_line` 定位（全體偏移 +664，TT-UP-2）。
- 不要為湊綠去拆 `SELECTED_OPTIONAL_DISABLED` 這類複合 token，也不要把 `EXCLUSIVE_PAIRS_MAKER_DECLARED` 放回 `state_gate`。
- SPEC 一律 **by raw sha** 定位（路徑會搬；B1 `13294cad…`、B2 `140de5bc…`）。

## 5｜DAG 現狀與下一批

```
B0 ✅(前 SESSION, 歷史 ACCEPTED)
B1 ⚠️ 候選完成、B1_ACCEPTED=NO      ← D-1..D-4
B2 ⚠️ 候選完成、B2_ACCEPTED=NO      ← H-1/H-2/D-5/TT-UP-1
B3 🟡 只到 PARSE@1                   ← 下一步
B4–B8 ⬜ 未開工
```
- `B3`：先出 `B3.SEMANTIC@1`（365 Unit 的 POS 謂詞＋分類 NEG）。B3 的 `SourceChildLedger.draft.md` 需**原 Writer 授權的 COMMIT**，本次未寫；只可先做記憶體階段。
- `B4`←B1+B3、`B5`←B2+B3、`B6`←B4+B5、`B7`←B3+B4+B5+B6、`B8`←B7。B1/B3→B6 只 observes。
- B1 的 HOLD 不阻 B3/B5 未受影工作；但 B5 讀 B2 的 `pin_state` 時**只能用逐列值**，不可用歷史純量 72/54（那是「無可用 pin 文字」，不是「無工具」）。

## 6｜Owner 裁決包（一次送，不要逐項等）

D-1（locator bindings 追認）｜D-2（allow-list 與 mirror 地位）｜D-3（七槽映射來源）｜D-4（五 Kernel oracle）｜D-5（parent/carrier by-sha 重綁）｜H-1（9 列 HARD §06 mutation 的 oracle 或修 §06）｜H-2（6 列 E00 互斥關係）｜TT-UP-1/2（上游 SPEC 修正）｜EXT-1（r5 候選是否採納）。

裁決後的最小動作：更新 `00_PREFLIGHT` 對應檔或新增 Owner 裁決書 → 受影 batch 重跑 → 新 freeze → **新的分離 Checker 一輪** → 只有 PASS 才可談升格。

## 7｜執行慣例（本 SESSION 驗證有效）

- 產物一律 `write_file` 落地再跑；`python -B` 避免 `__pycache__`。
- 長跑（checker／大 JSON）用背景＋`notify`，並設心跳；同一候選被取代就 **kill 舊 run**，不要讓兩個 verdict 指向不同 bytes。
- freeze 的 `claim_ceiling` 只能有**一個來源**（本 wave 由 TQAEP 複製）。
- 每次 freeze 後重建 manifest 並驗 `UNCLASSIFIED == 0`。
- 每次推送上推後，用匿名 raw 回讀比對 byte。

## 8｜已知落差（不要重複踩）

1. 上游 SPEC 路徑會被搬 → by-sha。
2. `direct_clause_sha` 用 `direct_parent_ref`＋含第 b 行 LF，不是 `original_source_ref`。
3. 歷史 72/54 可由未修改的 `b2_ops_qrows.py`（`pin:=sp[5]`）重現。
4. Q 列 requiredness 是 `VERBATIM_ONLY`，不是獨立檢查。
5. licence 只看真正授權詞（`Apache Arrow` 是產品名）。
6. Q 列沒有 tool pin 可評估 → `NOT_EVALUATED_Q_ROW`。
7. `state_gate` 執行路徑只准 NATURAL 互斥，且以 token 相等比對（子字串會誤判）。
8. namespace join 必須以 full key 命中；丟／偽 namespace 以 `endswith` 判 DENY，unknown 回 `[]`。

## 9｜完成判準（不可自封）

- 每批：`DEV → 真 OPS → 原 TQAEP 自檢 → freeze → 分離 Checker → 受影修補 → 再 freeze`，且 **Checker 對同一 digest 給 PASS**。
- 全波：四 Outcome ＋ B5 Wheel 引用 ＋ B7 交付 ＋ B8 回歸 ＋ W0 Accepted ＋ W1 技術准入，皆具名收據。
- 在此之前，對外只能說「候選」，不能說「已接受／已升格／已交付」。
