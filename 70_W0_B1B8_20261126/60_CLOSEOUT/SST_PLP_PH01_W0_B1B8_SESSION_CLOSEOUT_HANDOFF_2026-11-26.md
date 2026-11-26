# SST_PLP_PH01 W0 B1–B8｜SESSION 結案與移交（2026-11-26）

> 用途：讓全新 SESSION 不必重讀整段對話即可續工。本檔自足。
> 讀者：下一位執行代理（Commander）。
> 撰寫原則：只寫實測事實；未達成者寫「未達成」，不缺省、不美化。

---

## 0｜本次 SESSION 的升格稽核（用戶直接提問）

| 稽核問題 | 實測答案 | 證據 |
|---|---|---|
| 過審項目是否已從候選升格為主用？ | **沒有。升格數 = 0** | `DELIVERY_MANIFEST.json` → `promotion_state.promoted_to_primary = []` |
| 是否已上推並併入主 MANIFEST？ | **沒有。無法上推** | `SQS-THC_MVP_Workspace` **不是 git repo**（無 `.git`、無 remote）；Master PROMPT 指定的 `SQS-THC_MVP` 本機不存在；本次未動用任何憑證 |
| 是否被錯誤放進可棄層／候選層？ | **是，已修正** | 修正前：75 件產物無索引，50 個 `40_OPS` 檔案中 41 份是舊輪收據，新 session 無從分辨權威與過時 → 事實上的候選層。已建 `DELIVERY_MANIFEST.json`（19,897 B，`e934db60…868134`）逐件分層並帶 raw sha |
| 為何沒升格？ | **沒有可升格之物** | B1 經三輪分離 Checker 全判 `B1_ACCEPTED = NO`；B2 的 TQAEP 剛執行完但**尚無分離驗收**. 無驗收即升格＝偽造，違反 Owner 規則 |

**分層現況**（`layers` 實測）：`CODE_AUTHORITATIVE 10`｜`CURRENT_RECEIPT 5`｜`SUPERSEDED_RECEIPT 41`｜`CHECKER_RECORD_IMMUTABLE 3`｜`CURRENT_CLOSEOUT 2`｜`SUPERSEDED_CLOSEOUT 8`｜`LASTGOOD_HISTORY 2`｜`CANDIDATE_NOT_RATIFIED 2`｜`AUTHORITATIVE_INPUT 1`｜`UNCLASSIFIED 1`（`40_OPS/b1_summary.json`，為衍生摘要，下輪應歸 `DERIVED_SUMMARY`）

**正確落在候選層的 2 件**（刻意，不可自行升格）：
- `00_PREFLIGHT/b1_locator_bindings.json`（2,502 B）— 三筆 `CANDIDATE_NOT_RATIFIED` binding
- `00_PREFLIGHT/b1_source_allowlist.json`（3,105 B）— 僅 primary carrier，mirror 未納

**誤落可棄層並已清除**：`/tmp/c*.txt`、`/tmp/cases_out.txt`、`/tmp/chk_b1*.md`（本 session 執行輸出，非權威，已刪）。`/tmp/e.txt,o.txt,tree.txt` 非本 session 產物，未動。

**外部唯讀狀態複驗**：brownfield `C:\Projects\Agent_Workspace\SQS-THC` HEAD 仍 `9a70501ad4bbf315c675894a7a58c0f98bf18f47`；知識庫 SPEC 目錄最新 mtime 10:45（本 session 首寫為 11:24）→ 未被本 session 修改。

---

## 1｜現行權威指標（current_pointers）

| 角色 | 檔案 | raw SHA256 |
|---|---|---|
| B1 run | `40_OPS/b1_run_20261126T130447.json` | `abec36c2…c41438` |
| B1 TQAEP | `40_OPS/b1_tqaep_20261126T130448.json` | `60762a74…aa16b` |
| B2 parse | `40_OPS/b2_parse_20261126T121931.json` | `14147dcb…`（274,689 B） |
| B2 ToolReadSet | `40_OPS/b2_toolreadset_20261126T122128.json` | `661ce45e…`（716,671 B） |
| B2 TQAEP（新） | `40_OPS/b2_tqaep_20261126T131157.json` | `74ee303d0480fdf3ab7653b3d5a033a81fada6d06d965de2fb1d610661917023`（963,326 B） |
| B1 CLOSEOUT | `60_CLOSEOUT/SST_PLP_PH01_W0_B1_CLOSEOUT_rev8.md` | 2,944 B |
| B1 HANDOFF | `60_CLOSEOUT/SST_PLP_PH01_W0_B1_HANDOFF_rev3.md` | 5,229 B |
| B2 CLOSEOUT | `60_CLOSEOUT/SST_PLP_PH01_W0_B2_CLOSEOUT_HANDOFF_rev1.md` | 4,153 B |
| 交付索引 | `DELIVERY_MANIFEST.json` | `e934db60e5c5a9ecf881d9e3da7c34f4e71d6c8225ef73e569a81ad63b868134` |

`rev1` CLOSEOUT／`HANDOFF.md` 標記 `LASTGOOD_HISTORY`，**只作歷史**，不得當現行依據。

---

## 2｜B1 真實狀態

- `b1_run` 分佈：`OBSERVED_TRACKED_AT_HEAD 11`、`OBSERVED_IN_WORKING_TREE_UNTRACKED 4`、`OBSERVED_MIXED_SURFACES 1`、`OBSERVED_IN_FDA_CARRIER_CONTENT_IDENTICAL 7`；`missing = []`；`fabricated commits = []`
- 讀域分帳：`REPO_ROOT 14`、`DISK_AT_DECLARED_PATH 9`、`EXTERNAL_CARRIER 12`
- 60 案：**PASS 55／HOLD_ORACLE_UNBOUND 5／FAIL 0**
- `B1_ACCEPTED`：**不成立**。理由不是 FAIL，而是：(a) 6 項我可修未修、(b) 4 項待授權、(c) 5 案無 Oracle

### B1 六項未修（皆為 Maker 可修）
1. 收據未釘 `b1_locator_bindings.json`／`b1_source_allowlist.json` 的 sha
2. BASE-017 bound 目標 `measured` 為空（只有回抄 sha）
3. bound 目標 `commit_reason` 仍寫「no locator at the declared path」
4. `SEC.B1.CALLER_SUPPLIED_SURFACE_REJECTED` 對 exact path 恆真（真空轉）
5. `FDA_ARTEFACTS` 15 vs allow-list 16（`README.md` 未納碰撞清單）
6. `NEG.FDA_broker_live_submit` 的 detector `submit` 為常數，arm 無區辨力

**累計修補額度警示**：偽造 `commit=HEAD` 同根因已修 **2 次**（round 2 一次、round 3 一次）。第三次不得再以同一方式重開；若再現，判 `ROOT_CAUSE_UNRESOLVED` 並 PARK。

## 3｜B2 真實狀態

- 已真跑：`b2_ops_tqaep.py` → 1,465 unit／**2,930 case**（POS 1,465／NEG 1,465），**PASS 2,930**
- POS：由 `source_payload` 重算 compact JSON SHA，1,465/1,465 與宣告相符
- NEG：單欄位變異（`__b2_neg_probe__`）必須被同一 oracle 偵測，1,465/1,465 偵測
- `claim_ceiling = PAYLOAD_INTEGRITY_ONLY`；**不宣** Q 列語義 requiredness、工具可用性、licence／lock、B5 選型
- **兩項自曝缺口**：
  1. 該收據 `quadrants = {'None': 1465}`——象限歸屬在 `b2_ops_qrows.py`（440／513／378／54）不在這份 TQAEP，不可混用
  2. `rows_without_bound_pin = 54`，而 T122128 版報 72，**未對帳**
- `B2_ACCEPTED`：**不成立**（無分離驗收）

## 4｜待 Owner 裁決（最小清單，D-1～D-4）

| # | 事項 | 差額 | 建議 | 受影 |
|---|---|---|---|---|
| D-1 | 三筆 locator binding `CANDIDATE_NOT_RATIFIED` | declared 少 `data_plane/`、`governance/` | 追認 binding 或修 SPEC 路徑（含新 sha） | B1 BASE-009／017 |
| D-2 | mirror carrier 未納 allow-list 卻仍餵 EOL 判定 | 同內容≠同權利 | 授權為 `MIRROR_CARRIER` 或停用其 matrix／EOL 引用 | BASE-013~018 |
| D-3 | 七槽 slot→artefact 映射 `slot_reference_counts=0` | 五 action class 不能冒七槽 | 提供 slot 級來源或維持 `CARRIER_LEVEL_ONLY` | 7 個 FDA POS |
| D-4 | §06 KERNEL NEG 需「改一個受保護欄位」Oracle | 五 Kernel 細規未 ratified | 交原 Domain Owner 或維持 `HOLD_ORACLE_UNBOUND` | 5 案 |

---

## 5｜新 SESSION 起手步驟（照做即可）

```
cd "C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126"
# 1) 先讀三個檔：本檔、DELIVERY_MANIFEST.json、40_OPS/b1_checker_round3_verdict.md
# 2) 復現 B1（約 2 分鐘）
python -B 20_DEV/b1_reader/run_b1.py && python -B 20_DEV/b1_reader/b1_cases.py
# 3) 復現 B2（約 1 分鐘，會產生新收據）
python -B 20_DEV/b2_reader/b2_ops_tqaep.py
# 4) 重建交付索引（每次產生新收據後必跑）
python -B 20_DEV/build_delivery_manifest.py
```

**Owner 視窗**：`WIN-4e4b8cdc56c7`，opened 2026-11-26T11:25:31，`expires_at = 1795692331`（19:25:31 +08:00），`max_ops = 40`，上次量測 `ops_used = 0`。新 session 起手先跑 `python C:\Projects\Agent_Workspace\FHS_NEXT\owner_envelope\code\owner_window.py status`。**代理不得解鎖私鑰、不得代輸口令、不得自行開窗或延期**；過期即停受影效果並回報。

**分離 Checker 正確呼叫式**（前兩輪失敗過）：
```
codex exec --skip-git-repo-check -s read-only \
  -C "C:/Projects/Agent_Workspace/SQS-THC_MVP_Workspace/70_W0_B1B8_20261126" \
  -o ".../40_OPS/b1_checker_round4_verdict.md" "$(cat prompt.md)" < /dev/null
```
必須 `C:/` 原生路徑（MSYS `/c/` 會 `os error 2`）、必須 `--skip-git-repo-check`、必須 `< /dev/null`。

## 6｜本 session 已踩過並記下的坑

1. **heredoc 吃反斜線**：`<<'PY'` 內的 `'\\'` 會 SyntaxError → 腳本一律 `write_file` 落地再執行。
2. **路徑深度算錯**：`20_DEV/x.py` 往上一層才是 wave root；多算一層會把 manifest 寫到工作區根。
3. **bash `git -C /c/...` 間歇失敗**：改 `git -C "C:/..."` 或先 `cd`。
4. **`repo_exact` 混淆面**：`matched` 對 untracked 會回填 `declared_path`，「磁碟命中」被誤當「HEAD 命中」→ 偽造 commit。必須 `tracked = exact ∩ tree` 分開判定。此坑犯過兩次。
5. **carrier 升級覆寫**：須加 `and not _repo_exact`，否則 `TRACKED_GLOB` 被改寫成 carrier 標籤。
6. **NEG 恆真**：mutation 不能與 baseline 相同（`submit=true` 對 `submit=true`）；`narrowed_ok` 不得對 PARTIAL 強制 true。
7. **B2 象限**：取 unit 標題 `#### B2.Uxxxx｜` 之後 500 字；不可由總數反推。
8. `write_file` 對既有 CLOSEOUT 有覆寫保護 → 一律新增 `_revN`，不覆寫。

## 7｜不可跨越的線（違反即失效）

- 不讀／不輸入口令、私鑰、DPAPI；不自建 issuer／registry／compiler
- 不改知識庫原件、不改 `SQS-THC`、不改 `FHS/Fabric`；`write_set = []`
- 不 checkout／fetch／import／執行 repo 內程式碼；`FIN_ORDER = DENY`；不啟金融 GUI、不裝工具
- 不為求綠修改 expected、不改 Oracle、不把 `HOLD` 藏成 `PASS`、不把 Maker 自測當驗收
- 全部新產物只寫 `C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace`

## 8｜下一步優先序（下個 session 直接執行）

1. 修 B1 六項（§2），特別先修真空轉的 SEC 案與 detector 常數——那兩項是假證據
2. 新 freeze → 派 round 4，只核同根因復發與六項，不全量重盤
3. B2：把象限歸屬與 54/72 對帳併入同一收據，再交分離驗收
4. D-1～D-4 待裁決項目並行送 Owner，不阻塞上述 1–3
5. B3 准入只依 B0＋B2 真 requires，不等 `B1_ACCEPTED`

**本 session 結束狀態：無背景程序殘留；owner broker 隨視窗存活；未上推、未升格、未改外部原件。**
