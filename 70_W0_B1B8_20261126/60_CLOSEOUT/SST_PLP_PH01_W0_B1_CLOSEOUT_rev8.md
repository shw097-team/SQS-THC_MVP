# SST_PLP_PH01_W0_B1_CLOSEOUT_rev8

> 取代 `_rev7`。rev 8 依 round 3（`40_OPS/b1_checker_round3_verdict.md`）修掉兩處**同一缺陷的復發**，並誠實保留未修項。
- 候選：`b1_run_20261126T130447.json`（`abec36c2…c41438`）＋ `b1_tqaep_20261126T130448.json`（`60762a74…aa16b`）
- **PASS 55／FAIL 0／HOLD_ORACLE_UNBOUND 5**

## 1｜round 3 揭出的兩處復發（已修）

| 缺陷 | 根因 | 修法 |
|---|---|---|
| `commit=HEAD` 仍出現在 9 筆 untracked 解析 | `repo_exact = bool(exact)`，而 `matched` 對 `DISK_FILE_UNTRACKED` 會回填 `declared_path`，於是「磁碟命中」被當成「HEAD 樹命中」 | 拆開兩個概念：`exact`＝宣告路徑有實體（任何面）；`tracked`＝`exact ∩ HEAD tree`。`commit`／`REPO_ROOT` 只由 `tracked` 決定 |
| `TRACKED_GLOB` 被 carrier 標籤覆寫 | carrier 升級未檢查 repo 是否已精確命中 | 升級條件加 `and not _repo_exact` |

副作用已驗：`missing=[]`、`fabricated commits=[]`、讀域 `REPO_ROOT 14 / DISK_AT_DECLARED_PATH 9 / EXTERNAL_CARRIER 12`——前兩者正是 round 3 逐一數出的 14 與 9。

## 2｜`B1.NEG.BASE-009` 已閉合（非硬轉綠）

round 3 判定：arm (b) 的 `upgraded` 來自 `data_plane/config/*.yaml` 這個**在 HEAD 就 tracked** 的 glob 被當成「被升級」。修法為逐目標只比較 baseline 非 TRACKED 者。修後該案 PASS，且仍保留 `mutation_a.first_fail=BASE_ROW_MISSING` 的實測。

## 3｜round 3 (a) 類仍未修（不宣稱已閉合）

1. 收據**未釘** `b1_locator_bindings.json`／`b1_source_allowlist.json` 的 sha（binding 信任只剩 binding-vs-file）。
2. BASE-017 bound 目標的 `measured` 為空，只有回抄 sha。
3. bound 目標的 `commit_reason` 仍用「no locator at the declared path」（該目標其實有 binding）。
4. `SEC.B1.CALLER_SUPPLIED_SURFACE_REJECTED` 對 exact path 無效（`resolve` 走真實 FS），斷言不可能失敗 → 應改判 `NOT_APPLICABLE` 或重寫。
5. `FDA_ARTEFACTS` 15 筆 vs allow-list 16 筆（`README.md` 未納碰撞清單）。
6. `NEG.FDA_broker_live_submit` detector 的 `submit` 為常數，arm 不具區辨力；變異與 §06 欄位不一致。

## 4｜(b) SPEC／Owner 權限阻斷（我不自行裁決）

1. 三筆 locator binding 為 `CANDIDATE_NOT_RATIFIED`；需 Owner 追認或修 SPEC 路徑（含新 sha）。
2. mirror carrier 仍餵 EOL 判定與 matrix vocabulary，但 allow-list 只有 primary → 需結構化授權或停用。
3. 七槽 slot→artefact 映射仍 `slot_reference_counts=0`（七個 FDA POS 標 `CARRIER_LEVEL_ONLY`）。
4. §06 KERNEL NEG 的「改一個受保護欄位」需 Domain Owner 語義 Oracle。

## 5｜狀態

`B1_TQAEP_EXECUTED` 成立；`B1_ACCEPTED` **不成立**——不是因為 FAIL（已 0），而是因為上述 (a) 6 項未修、(b) 4 項未授權、(c) 5 案無 Oracle。三者性質不同，不合併成單一 HOLD。
