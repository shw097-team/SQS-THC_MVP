# NEW SESSION BOOTSTRAP｜SST PH01 W0 B1–B8

> 這頁是第一讀。讀完只要照 §B 四步就能接上；細節在 `60_CLOSEOUT/SST_PLP_PH01_W0_HANDOFF.md`。

## A｜一句話狀態

B1、B2 都做完了**候選**並各經 5 輪分離 Checker，**兩者 `ACCEPTED = NO`**；B3 只到 parse；**B4–B8 未開工**；**沒有任何項目升格**；已發布到 `shw097-team/SQS-THC_MVP` @ `0489ac8`。

## B｜四步接上

```bash
cd "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/70_W0_B1B8_20261126"
# 1) 現況
python -c "import json;m=json.load(open('DELIVERY_MANIFEST.json',encoding='utf-8'));print(m['promotion_state']['promoted_to_primary']);print(m['current_pointers'])"
# 2) 凍結完整性（兩行都要 True）
python -B - <<'PY'
import json,hashlib
f=json.load(open('40_OPS/b2_candidate_freeze_round6.json',encoding='utf-8'))
print(all(hashlib.sha256(open(a['path'],'rb').read()).hexdigest()==a['raw_sha256'] for a in f['artefacts']))
d=hashlib.sha256("".join(f"{a['raw_sha256']}  {a['path']}\n" for a in sorted(f['artefacts'],key=lambda x:x['path'])).rstrip("\n").encode()).hexdigest()
print(d==f['candidate_digest'])
PY
# 3) 最後判讀（唯一有效）
sed -n '1,40p' 40_OPS/b2_checker_round5_verdict.md
sed -n '1,25p' 40_OPS/b1_checker_round5_verdict.md
# 4) 重建一次 manifest 確認 0 UNCLASSIFIED
python -B 20_DEV/build_delivery_manifest2.py | tail -2
```

## C｜立刻可做的三件事

1. **B3 語意**：沿用 `20_DEV/w0_spec.py` 的 by-sha 取件，把 `b3_parse` 的 365 Unit 做成 POS 謂詞＋分類 NEG（**不要**套 B2 的通用 oracle）。`SourceChildLedger.draft.md` 需原 Writer 授權才可 COMMIT。
2. **Owner 裁決包**：D-1…D-5、H-1、H-2、TT-UP-1/2、EXT-1（清單在 HANDOFF §6）。裁決前不要動受影 batch 的 expected。
3. **B4 parse**：不依賴 B1 接受，可先出 `B4.PARSE@1`（census＋pin＋case join）。

## D｜不要做

- 不要把 `CANDIDATE_*` 當 primary；不要刪 `SUPERSEDED_RECEIPT`；不要改 verdict；不要用 `q_row.evidence_line`；不要用路徑（用 raw sha）找 SPEC；不要自封接受。

## E｜檔案地圖

| 想看 | 去哪裡 |
|---|---|
| 全 wave 實測＋升格審計＋衛生紀錄 | `60_CLOSEOUT/SST_PLP_PH01_W0_CLOSEOUT.md` |
| 怎麼續作、指令、DAG、落差 | `60_CLOSEOUT/SST_PLP_PH01_W0_HANDOFF.md` |
| 分層／指標／每檔 sha | `DELIVERY_MANIFEST.json` |
| 程式 | `20_DEV/**`（`b1_reader/`、`b2_reader/`、`w0_spec.py`、`build_delivery_manifest2.py`、`make_b2_freeze.py`） |
| 收據／裁決 | `40_OPS/**`（`CURRENT_RECEIPT` 6、`CHECKER_RECORD_IMMUTABLE` 10） |
| 外部 r5 候選（未採納） | `90_EXTERNAL_INPUTS/spec_delta_r5_2026-11-26_r5_CANDIDATE/STATUS.md` |
