# HANDOFF rev2 → B3 准入（2026-11-27_r7）

- 產生：`2026-11-27T16:09:24+0800`
- 一句話：r7 真產品重跑完成，經 Checker REJECT 一輪更正；B3 `ReadyAtom=false`、`ReadyExecute=HOLD`；四批未接受。

## 1｜立即可做（不需新權限）

1. **B3 owner 綁定**：365 個 Unit 的 `owner` 皆為字面 `#`；改由原條文取得 owner，`admission_ready` 才可能非零。
2. **B3 NEG-design 結構化**：把 NEG design 做成 typed 欄，實作 `AUTHOR:TRACE_ORPHAN`／`AUTHOR:NEG_MISSING`／`AUTHOR:CHILD_RULE_HOLD:<key>` 三個原 FirstFail（**不得**把 `DIRECT_CLAUSE_SHA_MISMATCH` 改名成原碼）。
3. **B2 requiredness 限定詞契約**：40 案現為 `AUTHOR_QUALIFIER_UNRATIFIED` HOLD，需具權採納才可放行。

## 2｜需 Owner

| 項 | 範圍 | 影響 | 建議 |
|---|---|---|---|
| B0 descriptor 續期 | `00_PREFLIGHT/B0_READ_CONTEXT_2026-11-26.json`＋`native_entry.py` `EXPECTED_DESCRIPTOR_SHA/BYTES`＋每源 `usage_evidence_sha` | B0 現時權利、B3 `ReadyExecute`、三端 currency | 與 D-2／D-3 同窗 |
| D-2／D-3／D-4／TT-UP-1 | FDA 四測試讀權／七槽 M:N／五 Kernel 語義／inner→outer 映射 | B1／B2 未閉項 | 各原權位 |

## 3｜不得重入

- 不得覆寫凍結：`r7_freeze.py` 無 `--revision` 會拒絕；新修訂一律新檔並記 `supersedes`。
- 不得把 `REFUSAL_EXECUTED` 當 PASS；判定權在 `b3_r7_neg_reconcile.json`。
- 不得以 `receivers.B3` 的 1317 代替 B3 join 的 `with_mandatory` 0／1465（mandatory 集合不同）。
- 不得把歷史 B0 envelope 當 current；不得用路徑／檔名找 SPEC（用 raw sha）。

## 4｜重現（本輪指令）

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/71_W0_B0-B3_R7_20261127/20_DEV/r7"
python -B r7_preflight.py
python -B b1_cli.py --op ALL --out ../../40_OPS/b1_r7_run_all.json
python -B b1_tqaep.py && python -B b1_edge_sec.py
python -B b2_meta.py && python -B b2_tqaep.py
python -B b3_product.py --dry-run
python -B b3_neg.py && python -B b3_neg_reconcile.py && python -B b3_tqaep.py
python -B r5_consumers.py && python -B r5_consumers.py --selftest
python -B r7_freeze.py --revision rev3     # 凍結不含 docs；新修訂必用新檔名
python -B r7_closeout_gen_rev2.py
```

## 5｜坑

1. `b2_tqaep.py` 必須在 `b2_meta.py` 之後（否則 B5 接收為 0）。
2. B2 載體目錄是 `PHASE 01-04`（連字號），非 `PHASE 01~04`。
3. B3 ledger 正文不得含 wall clock，否則 digest 不可重算。
4. owner window 同時只能一個，`WINDOW_ALREADY_OPEN` 不彈視窗。
5. `b3_product.op_commit` 以 window 狀態判權：window 關閉時回 `OWNER_WINDOW_CLOSED`（正確的 fail-closed）。
