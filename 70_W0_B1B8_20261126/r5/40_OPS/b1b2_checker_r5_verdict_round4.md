# B1-B2 r5｜分離唯讀 Checker 裁決（Round 4）

- 裁決：**ACCEPT**
- mandatory findings：**0**
- 執行：分離唯讀 subagent `sa-0-e0c85a98`（deleg_00fb178c），23 次工具呼叫、346 秒
- 時間：2026-11-26T23:35:38+0800
- 範圍：reader pin delta、B0 真跑產物、B3 draft v2、B2 META、M-01 收據、受檢源碼樹非回歸

## 逐項（Checker 原文摘）

1. **C1 PASS** — `native_entry.py:32-39` 三常數（path / `2064685a…aacd` / 3582）與磁碟實檔重算全等；`icacls` 無 Everyone／Authenticated Users／BUILTIN\Users／Anonymous ACE，亦無任何 (F)/(M)/(W)；僅 CodexSandboxUsers RX、Administrators/SYSTEM/user F。
2. **C2 PASS** — `b0_r5_sourcereadset.json`（3,028 B）：wire／entries 1／errors 0／write_set []／fin_order DENY／preimage N/A 全符；locator 檔重算 457,294 B／`dd37a40b…`；物理行切片（含行終止符）1,306 B → `clause_sha 77132f06…` 相符；M=[]、R=[read]=observed keys、value 逐字在切片內、value_sha 相符。
3. **C3 PASS** — `draft.v2` 重算 315,375 B／`f08ec189…`；ready 1,369=len(children)、held 96=len(holds)、合計 1,465、零重複 atom、children/holds 不重疊；舊 draft（407,447 B／`c6819579…`／mtime 22:51）仍在且 bytes 不同。
4. **C4 PASS** — META 18 entries、18 個不重複 tool_id、counts 與實際分佈一致；兩條 COLLECTED 的 URL 重抓產生完全相同位元流（pydantic 2.14.4：147,543 B／`5d722dd4…`；jsonschema 4.26.0：9,468 B／`d0c9ccdf…`），`license_expression=MIT` 相符；7 條 UNBOUND 的 pin_text 均含 UNBOUND 且無可解析版本。
5. **C5 PASS** — M-01 收據的 16／16／7／7 與 `b1_r5_run_fda.json` 一致；獨立對 16 個 path 重新 hash 全為 RAW_SHA_MATCH；7 slot 全 CARRIER_LEVEL_ONLY、hit_count 0。
6. **C6 PASS** — SQS-THC 20,175 檔（排除 .git）今日 0 檔被改（最新 2026-10-27）；FHS/Fabric 10,222 檔今日 0 檔被改（最新 2026-11-14）。

## MINOR（不阻接受，但必須留痕）

- **[MINOR] 信任根 ACL 僅 broad-principal 封閉，非 identity 封閉**：`DESKTOP-57EO414\user`、`BUILTIN\Administrators`、`NT AUTHORITY\SYSTEM` 各持 `(I)(F)`，且繼承仍開啟。也就是說，B0 的 trust root 可被「驗證它的同一 principal」改寫。
  影響：本輪 C1 判準（broad principal 不得有寫權）**通過**；此為更嚴的 identity 封閉未達成。
  處置：不自行改 ACL（改信任根 ACL 屬權利配置變更，須 Owner 決定）；已列入 Owner 待決事項 `OWNER_DECISION_LIST_r5.md`。
