# HANDOFF｜下一 SESSION 接續（SST PH01 W0 B0–B3）

- 產生：2026-11-27T19:52:36+0800
- 一句話：B0 已閉合並升格；B1 PARK、B2 PARTIAL、B3 准入仍 HOLD；現行候選 `40_OPS/r7_candidate_freeze.rev12.json`（`8fe2b08d56670234…`）未經 Checker。

## 1｜第一步（照抄即可）

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/71_W0_B0-B3_R7_20261127"
python -B - <<'PY'
import json,hashlib,os
lay=json.load(open("40_OPS/LAYERS.json",encoding="utf-8"))
f=json.load(open(lay["current_candidate"]["path"],encoding="utf-8"))
ok=all(hashlib.sha256(open(a["path"],"rb").read()).hexdigest()==a["raw_sha256"] for a in f["artefacts"])
body="\n".join(f'{a["raw_sha256"]}  {a["path"]}' for a in sorted(f["artefacts"],key=lambda x:x["path"])).rstrip("\n")
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
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/20_DEV" && mkdir -p .tmp_tests \
  && env -u TMPDIR TMP="$PWD/.tmp_tests" TEMP="$PWD/.tmp_tests" \
     python -B -m unittest discover -s tests -p "test_*.py"
```

## 5｜不得重入

- 不得覆寫凍結（`r7_freeze.py` 無 `--revision` 即拒絕；同 rev 檔存在即拒絕）。
- 不得把 `VERDICT_SUPERSEDED` 的判決引用為現行候選的 verdict。
- 不得把 `SUPERSEDED` 的 freeze 當現行；現行只有 `LAYERS.json.current_candidate` 一個。
- 不得把 `LOCAL_ONLY` 的 B0 readset 上推；published 樹只有其 sha。
- 不得把 B2 的 `receivers.B3` 1317/148 與 B3 TQAEP 的 join 0/1465 互相代替（mandatory 集合不同）。
- 不得在未取得具權裁定的情況下，把 20 個 ROUTE 案改標籤或改 SPEC。
