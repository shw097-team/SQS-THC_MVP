# B0 reader pin delta（可重現說明，不含私有 descriptor）

## 事實
- `20_DEV/b0_reader/native_entry.py` 的 `EXPECTED_DESCRIPTOR_PATH/SHA/BYTES` 由舊值
  （`00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json`／`c57518c4…`／3,846 B）
  改為新值（`00_PREFLIGHT/B0_READ_CONTEXT_2026-11-26.json`／`2064685a…`／3,582 B）。
- 新 descriptor 由 Owner 於本回合以 tkinter 口令視窗簽發（`WIN-4e2dff74d227`，
  ceiling `READ_ONLY_PROBE`，scope `b0_source_read_authority,sqs_thc_ph01_e00`，max_ops 40）。

## 為何改
原 descriptor 的權利區間在 2026-11-26T02:26:58+08:00 到期，B0 以 `RIGHTS_EXPIRED` 拒絕（exit 64）。
換 pin 後 B0 產出真 `SST.B0.SourceReadSet/2`（exit 0、errors 0、write_set []、fin_order DENY）。

## 三個判準（任何要重現的人都要滿足）
1. **scope 順序**：reader 比對 `("b0_source_read_authority","sqs_thc_ph01_e00")` 這個精確 tuple，反序會被拒。
2. **descriptor 位置**：必須在 broad principal 無寫權的位置；本輪置於 `W/00_PREFLIGHT/` 並複製原檔的
   `CodexSandboxUsers:(R)` 明確 ACE。
3. **每來源 `usage_evidence_sha`**：必須等於「當次視窗收據」的 SHA；換窗後須同步，否則回 `RIGHTS_UNVERIFIED`。

## 未公開
descriptor 本體（含 `authorization_ref`／收據 SHA）不進 Repo；本文件只描述結構與三個判準。
