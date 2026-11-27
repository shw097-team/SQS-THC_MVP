# NEW SESSION BOOTSTRAP｜W0 B0–B3 r7（rev4）

## 狀態

r7 真產品重跑＋一輪 Checker 更正；B3 `ReadyAtom=false`／`ReadyExecute=HOLD`；四批未接受；`FIN_ORDER=DENY`。

## 四步

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/71_W0_B0-B3_R7_20261127"
python -B - <<'PY'
import json,hashlib
import glob as _g
f=json.load(open(sorted(_g.glob("40_OPS/r7_candidate_freeze.rev*.json"),key=os.path.getmtime)[-1],encoding="utf-8"))
ok=all(hashlib.sha256(open(a["path"],"rb").read()).hexdigest()==a["raw_sha256"] for a in f["artefacts"])
body="\n".join(f'{a["raw_sha256"]}  {a["path"]}' for a in sorted(f["artefacts"],key=lambda x:x["path"])).rstrip("\n")
print(ok, hashlib.sha256(body.encode()).hexdigest()==f["candidate_digest"])
PY
sed -n '1,40p' 60_CLOSEOUT/SST_PLP_PH01_W0_B0-B2_CLOSEOUT_rev4.md
python -c "import json;d=json.load(open('40_OPS/r7_b3_admission.json',encoding='utf-8'));print(d['four_ready'])"
```

## 立刻可做

B3 owner 綁定、B3 NEG-design 結構化、B2 requiredness 限定詞契約。

## 不要做

覆寫凍結／把 `REFUSAL_EXECUTED` 當 PASS／用 `receivers.B3` 數字代替 B3 join／用歷史 B0 envelope 當 current。
