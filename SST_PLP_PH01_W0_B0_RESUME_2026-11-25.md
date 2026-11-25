# SST_PLP_PH01_W0_B0｜RESUME / 交接（2026-11-25 16:00 +08:00，因關機暫停）

> 用途：關機後重開，任何接手者（或本 Commander 新 session）照本檔即可續跑，不需重做考古。
> 本檔是**現況快照**，不是驗收；一切判定仍以 CLOSEOUT／HANDOFF／實測 raw 為準。

## 0｜一句話現況

工程與真產品執行都已成立（`B0_ENGINEERING_CANDIDATE` ＋ `B0_PRODUCT_EXECUTED`，132 tests OK、真來源 POS exit 0、四個單變異 NEG 正確拒絕、無產品寫入），**但第二輪獨立 Checker 在跑完前被關機指令中止**，因此 `B0_CORE_ACCEPTED` 仍不成立；GitHub 增量上推**尚未 commit／push**。

## 1｜可回查身份（全部實測）

| 項 | 值 |
|---|---|
| 規格正文 | `SST_PLP_PH01_W0_B0_執行控制小包_實質正文_2026-11-25_r4_Native-first_定案.md`，99,791 B，`582a54048d8b63e37be3d803c829a12ffe164be72963f026cea1a1b6183345d9` |
| 候選 freeze | `1257f5ee18fbd52c86ef71ae406b33919104bf1452801794af73551b04c0ca1b`（**25 檔**，`40_OPS/candidate_freeze.json`；產品 envelope 內同值） |
| 部署 descriptor | `00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json`，3,612 B，`b8759ca7f5c213024c4046db07494cabb355d39d051b0082ff043845e9fb45e0`；`native_entry.EXPECTED_DESCRIPTOR_SHA` 已固定此值 |
| Owner 授權 | 視窗 `WIN-2ffca679906c`，`2026-11-25T12:11:29 → 20:11:29 +08:00`，收據 `e750066a430da8a7c479efa9687d5aa2377964dbab51fdd20e144c6303edd28a` |
| 測試 | **132 tests OK**（0 fail／0 error／0 skip，約 290 s） |
| 真產品 OPS | `40_OPS/ops_r4_g_{pos,neg_pin,neg_span,neg_effect,neg_scope}.json` ＋ `.raw/`；POS exit 0、5,429 B、`NO_PRODUCT_WRITE_OBSERVED` |
| 獨立複核 | `30_VERIFY/commander_recheck_2026-11-25.json`（Commander 由原件重算 sha／clause_sha／value_sha，`all_match=true`） |
| Checker 第一輪 | `30_VERIFY/findings_r4.json`（18 條：8 PASS／3 FAIL／5 NOT_VERIFIED／2 HOLD）＋ `verify_r4_receipt.json` |
| Checkpoint | `30_VERIFY/b0_checkpoint_2026-11-25.json`（含 lane、rights、狀態、恢復命令） |

## 2｜被中斷的事（必須先處理）

1. **Checker 第二輪（freeze `1257f5ee…`）被 kill**（15:59，跑約 23 分；dispatch `proc_97b8976394a7` 已終止，無 ok 收據、無 §5.2 內容）。→ 重開後需重跑，見 §3-①。
2. **GitHub 增量上推未完成**：`W/dist/SQS-THC_MVP` 工作樹已有 **73 項變更（未 commit）**，remote `origin/main` 仍在 `c502db00e16a`。→ 見 §3-⑤。
3. `CLOSEOUT.md` §5.2 仍寫「待第二輪回覆後補入」——這是**如實狀態**，不可當成完成。

## 3｜重開後的執行順序（照做即可）

**① 起 relay（車道依賴，必要）**
```bash
cd C:/Projects/Agent_Workspace/FHS_NEXT/HG-KSEOS
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/start-hgk-hermes.ps1 -Action StartOpenCodex   # 背景執行；完成後 curl 127.0.0.1:10101/healthz = 200
```
**② 確認 Owner 視窗是否仍有效**
```bash
C:/Projects/Agent_Workspace/FHS/HG-KSEOS/.venv/Scripts/python.exe C:/Projects/Agent_Workspace/FHS_NEXT/owner_envelope/code/owner_window.py status
```
- 若 `usable=false`（20:11 後必然到期）：由 **Owner 本人**在原 tkinter 視窗重開（口令不經代理）：
```bash
C:/Projects/Agent_Workspace/FHS/HG-KSEOS/.venv/Scripts/python.exe C:/Projects/Agent_Workspace/FHS_NEXT/owner_envelope/code/owner_window.py open --task SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH --ttl-hours 8 --max-ops 12 --scope b0_source_read_authority,sqs_thc_ph01_e00 --effect-ceiling READ_ONLY_PROBE --workspace "C:\Projects\Agent_Workspace\FHS_NEXT_Workspace\FHS_vNEXT_W0W1_CLOSEOUT_W2_ENTRY_20261115\owner_ws"
```
- 新收據 → 只改 descriptor 的 `authorization_sha` / `valid_from` / `expires_at`（＋兩來源的 `usage_evidence_sha`）→ **重算 descriptor pin 並同步 `native_entry.EXPECTED_DESCRIPTOR_SHA`／`_BYTES`** → 重 freeze → 重跑 §3-③④。**(descriptor 換版就必須重 freeze，否則 digest 會對不上。)**

**③ 重跑測試（必要，290 s）**
```bash
cd C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/20_DEV
unset TMPDIR; export PYTHONDONTWRITEBYTECODE=1
export TEMP='C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\20_DEV\.tmp_tests'; export TMP="$TEMP"
python -B -m unittest discover -s tests        # 期望 Ran 132 OK
```

**④ 重跑真 OPS（若 descriptor 未換版，可直接重用現有 raw）**
```bash
cd C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace
unset TMPDIR; python -B 40_OPS/freeze_candidate.py      # 期望 1257f5ee…（25 檔）
for r in pos:b0_read_request_2026-11-25.json neg_pin:b0_read_neg_pin_2026-11-25.json \
         neg_span:b0_read_neg_span_single_2026-11-25.json neg_effect:b0_read_neg_effect_2026-11-25.json \
         neg_scope:b0_read_neg_scope_2026-11-25.json; do
  l=${r%%:*}; f=${r##*:}; python -B 40_OPS/run_ops_r4.py --label "B0-R4-R-$l" --request "40_OPS/$f" --out "40_OPS/ops_r4_r_$l.json"
done
```
期望：`pos` exit 0／5,429 B；`neg_pin` exit 2 `SOURCE_PIN_MISMATCH`；`neg_span` exit 2 `SPAN_INVALID`；`neg_effect` exit 64 `EFFECT_DENIED`；`neg_scope` exit 64 `SCOPE_MISMATCH`；全部 `NO_PRODUCT_WRITE_OBSERVED`。

**⑤ 第二輪獨立 Checker（重跑，這是 `B0_CORE_ACCEPTED` 的唯一缺口之一）**
用 VERIFY_SECURITY 車道，prompt 與 2026-11-25 15:36 那次相同（freeze `1257f5ee…`、逐條重判第一輪 18 條、核 POS 與四個 NEG、核三項已修 FAIL、給 CORE_ACCEPTED 五條件），**並要求最後一行只印 NONCE**；收據落 `30_VERIFY/verify_r4_round2_receipt.json`。回覆後把逐條判定寫入 `SST_PLP_PH01_W0_B0_CLOSEOUT.md` §5.2。

**⑥ 發布（增量上推，憑證檔 `C:\Projects\Agent_Workspace\API KEY\GITHUB-REPO_SHW097-4.txt`，只以受權客戶端注入、不落 argv/log）**
- `W/dist/SQS-THC_MVP` 已有 73 項 staged 變更；先 `git -C <dist> status` 核對再 `git add -A && git commit -m "..."`，以 `http.extraheader` 方式 push 到 `origin main`（不得 force、不得改 visibility）。
- 已排除不公開項：lane 派工 receipt／logs、`30_VERIFY/b0_checkpoint*`、FHS 車道配置、口令信封、raw 權利證據。
- push 後讀回 remote branch／commit／tree 與兩份公開 MD，把實際 commit URL 寫回 CLOSEOUT 發布段。

## 4｜不要重做的事（已定案，重做只會浪費時間）

- 不要重讀 r4 六件配套（SHA 已核）。
- 不要再改 `require_sealed` 的範圍（只套 descriptor＋直屬父目錄）、不要把 mint 放回 `b0_reader`、不要把撤權判定放寬成「非 CLOSED 就放行」。
- 不要再改 `00_PREFLIGHT` 的 ACL（已收緊為 user/SYSTEM/Administrators）；K 與他人 ACL 一律不動。
- 不要用 `TMPDIR` 跑測試（Hermes 預設會設；測試要求 `TEMP/TMP=.tmp_tests`）。
- 不要用 PowerShell／pwsh 派工（本機被 policy 阻擋，上一輪因此 50 分逾時）；用 python／icacls 直接呼叫。
- 不要以歷史 59／22 或作者 fixture 當現行 PASS。
- 不要為求全綠放寬 §04.D 的 FirstFail 碼。

## 5｜仍未閉合的 HOLD（與 CLOSEOUT §6 同）

H1 Native OFF 的 network／transitive tracing（`NOT_VERIFIED`，卡 `B0_CORE_ACCEPTED`）｜H2 無真 B1/B2/B3 Consumer（卡 `B0_COMPLETE`）｜H3 無 provider-versioned epoch｜H4 SourceManifest 原件未取得（`UNVERIFIED`）｜H5 P0-W00M 當期來源／權利成果未定位｜H6 Owner 視窗到期（20:11 +08:00）｜H7 車道 credential posture gate 檔缺（每次派工 WARN）｜H8 三車道同模型（owner order，served 已證、ADMITTED 未獨立證明）。

## 6｜狀態標的（重開後請照此續寫，不得提前升級）

```
B0_SPEC_READY                 = 成立
B0_ENGINEERING_CANDIDATE      = 成立（freeze 1257f5ee…, 132 tests OK）
B0_PRODUCT_EXECUTED           = 成立（真來源 POS + 4 單變異 NEG + 無寫）
B0_CORE_ACCEPTED              = 不成立（等第二輪 checker；Native OFF 仍 NOT_VERIFIED）
B0_COMPLETE                   = 不成立（無真 Consumer 接收）
B1_CONTRACT_COMPATIBLE        = 成立（僅 probe）
B1_INPUT_READY / B1_READY_EXECUTE = 不成立
```
