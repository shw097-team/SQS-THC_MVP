# CHECKER WORK ORDER｜SST_PLP_PH01_W0_B0 獨立驗收（VERIFY_SECURITY 車道）

- 角色：分離 checker（不同 session、不得改 Maker 候選、不得共用 Maker 的測試當 oracle）。
- 候選（唯讀）：`C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\20_DEV\`
- 你的寫入範圍（唯一）：`C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\30_VERIFY\`
- 契約來源（唯讀）：`20_DEV/WORKORDER_B0_DEV.md`、`00_PREFLIGHT/PRECHECK_B0_2026-11-24.md`
- `FIN_ORDER=DENY`；不得讀憑證/口令；不得連網；不得安裝套件；不得 git 操作。

## 1｜凍結候選
1. 對 `20_DEV/**` 每個檔案（排除 `exec_build_receipt.json*`、`__pycache__`）算 sha256 與 bytes，寫 `30_VERIFY/candidate_freeze.json`（含 `frozen_at`、`file_count`、`tree_sha256`＝把所有 `sha256  path` 排序後串接再 hash）。
2. 之後**不得**再讀到不同內容卻沿用同一 freeze；若檔案變動，記 `STALE_CANDIDATE` 並停。

## 2｜獨立 oracle（不用 Maker 的測試）
在 `30_VERIFY/checker_tests/` 自行撰寫 `unittest`，覆蓋下列 22 點，每點一個測試，斷言以契約為準：
1. `check_root` 對正常檔回 ok，且 `acl_raw` 非空。
2. `../` 逃出 allowed_root → `PATH_ESCAPE`。
3. 同層前綴（`...\b0_ok_evil` vs root `...\b0_ok`）不得被判為包含。
4. junction/symlink 祖先 → `REPARSE_POINT`（無法建立則 `skipTest` 並記錄）。
5. ADS 形路徑（`file.txt:stream`）→ `ADS_PATH`。
6. 目錄不存在 → `ROOT_NOT_FOUND`。
7. `read_bytes` 對 UTF-8 失敗位元組 → `ENCODING_INVALID`，且不得回 text。
8. `expected_sha` 不符 → `SHA_MISMATCH`。
9. CRLF 檔的 `clause_sha` 必須包含 `\r`（不得正規化）。
10. span 越界 → `SPAN_OUT_OF_RANGE`。
11. `split_fields`：R={x,y}、只核實 y → M=[x]，且 `R` 不變。
12. `split_fields` 刪 R 的元素 → `REQUIREDNESS_HOLD` / `AUTHOR:TOOL_REQUIREDNESS_HOLD`。
13. `split_fields` 對不在 R 的 observed key → `SCHEMA_INVALID`。
14. `build_read_set` 全部合法 → `write_set==[]`、`errors==[]`。
15. 一個 ref 缺欄不得使其他 ref 失效（分帳）。
16. 以 `mock.patch("builtins.open")` 監看 `build_read_set` 不得以寫模式開檔。
17. 控制面：`subject` 被改 → `AUTHOR:SCOPE_MISMATCH`。
18. `write_set` 非空 → `AUTHOR:READ_WRITE_SCOPE_HOLD`。
19. `ready_execute` 被升為 true → `AUTHOR:FOUR_READY_HOLD`。
20. `claim_ceiling` 被升格 → `AUTHOR:CLAIM_CEILING_DENY`。
21. `effect_intent != SOURCE_READ` → `AUTHOR:EFFECT_UNBOUND`。
22. `unknown_policy` 改成盲 retry → `AUTHOR:UNKNOWN_UNDO_HOLD`。

## 3｜執行與證據
1. 跑 Maker 的 `python -m unittest discover -s tests -v`（cwd `20_DEV`），保存完整 stdout/stderr 與 exit code 到 `30_VERIFY/maker_suite_raw.txt`。
2. 跑自己的 checker 測試，保存到 `30_VERIFY/checker_suite_raw.txt`。
3. 逐 Case 寫 `30_VERIFY/findings.json`：
```json
{"schema":"B0.CHECKER.FINDINGS/1","candidate_tree_sha256":str,"checker":"VERIFY_SECURITY lane (separate session)",
 "results":[{"case":str,"verdict":"PASS|FAIL|NOT_EXECUTED","expected_first_fail":str,
   "observed":str,"evidence":"file:line or raw locator","note":str}],
 "summary":{"pass":int,"fail":int,"not_executed":int},
 "claim_ceiling":"independent-of-maker review of an AUTHOR candidate; NOT an OriginalReader verdict, NOT ReadyAccept"}
```

## 4｜判準
- 只依契約與你自寫的 oracle 判；不得因 Maker 測試綠燈而給 PASS。
- 發現缺陷只記錄，**不得代改**任何 `20_DEV` 檔。
- 若候選缺檔或無法 import，記 `NOT_EXECUTED` 並列缺因，不得補寫。
- 最終訊息最後一行輸出 token：`HGK_CODEX_PROVIDER_LANE_NONCE_OK`。
