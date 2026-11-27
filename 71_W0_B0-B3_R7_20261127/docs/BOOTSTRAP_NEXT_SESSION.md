# BOOTSTRAP｜下一 SESSION 第一讀

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
