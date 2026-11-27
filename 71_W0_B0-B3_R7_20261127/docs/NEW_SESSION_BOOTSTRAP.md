# NEW SESSION BOOTSTRAP｜W0 B0–B3 r7

## 一句話狀態

以 `2026-11-27_r7_Native-first_CODEX_FINAL` 重跑 B1／B2／B3 真產品並凍結候選；B3 `ReadyExecute=HOLD`（B0 descriptor 續期＋原 Reader）；**四批皆未接受**，`FIN_ORDER=DENY`。

## 四步接上

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/71_W0_B0-B3_R7_20261127"
# 1) 凍結完整性（兩行都要 True）
python -B - <<'PY'
import json,hashlib,os
f=json.load(open("40_OPS/r7_candidate_freeze.json",encoding="utf-8"))
ok=all(hashlib.sha256(open(a["path"],"rb").read()).hexdigest()==a["raw_sha256"] for a in f["artefacts"])
body="
".join(f'{a["raw_sha256"]}  {a["path"]}' for a in sorted(f["artefacts"],key=lambda x:x["path"])).rstrip("
")
print(ok, hashlib.sha256(body.encode()).hexdigest()==f["candidate_digest"])
PY
# 2) 重算（同 digest 表示無人改過受檢 bytes；此步會重寫 freeze 檔，勿在 Checker 讀取期間執行）
# 3) 最後判讀
sed -n '1,40p' 60_CLOSEOUT/SST_PLP_PH01_W0_B0-B2_CLOSEOUT.md
# 4) 准入
python -c "import json;d=json.load(open('40_OPS/r7_b3_admission.json',encoding='utf-8'));print(d['four_ready']);print([b['item'] for b in d['readyexecute_blockers']])"
```

## 立刻可做

1. B3 NEG-design 結構化（44 案唯一成因）。
2. B2 18 HARD `source_row`（由 B5 驅動）。
3. DOC_BRIDGE heading 10 案內容版本確認。

## 不要做

`CANDIDATE_*` 當 primary／刪收據／改 verdict／用路徑找 SPEC／用歷史 B0 envelope 當 current rights。
