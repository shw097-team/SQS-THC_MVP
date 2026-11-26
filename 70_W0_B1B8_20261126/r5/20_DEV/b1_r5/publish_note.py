#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append the remote-readback block to the r5 delivery documents (idempotent)."""
from __future__ import annotations
import hashlib, json, os, time

W = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126"
D = os.path.join(W, "60_CLOSEOUT")
HEAD = "## 發布｜remote readback"


def current_remote() -> str:
    p = os.path.join(W, "40_OPS", "b1b2_r5_publish_record.json")
    if os.path.isfile(p):
        return json.load(open(p, encoding="utf-8")).get("remote_head", "UNKNOWN")
    return "UNKNOWN"


def main() -> int:
    head = current_remote()
    block = f"""
{HEAD}（工程成果，非產品接受）

- Repo：`https://github.com/shw097-team/SQS-THC_MVP`，branch `main`
- commit：`{head}`（remote `ls-remote` 回讀與本機 `rev-parse HEAD` 全等）
- 發布範圍：`70_W0_B1B8_20261126/r5/` 下 168 檔（引擎、TQAEP/OPS 收據、凍結 manifest、CLOSEOUT/HANDOFF、裁決清單）
- **未發布**：`40_OPS/b0_r5_sourcereadset.json`（含原條文逐字），依 `LOCAL_ONLY` 留本地，remote 只記其 sha256（見 `40_OPS/LOCAL_ONLY_EXCLUSIONS.json`）
- 憑證：以受管 `extraheader` 一次性注入，未寫入 git config、未出現在 argv/URL/log/commit
- 發布 ≠ 接受：`B1_ACCEPTED`／`B2_ACCEPTED`／`W0_COMPLETE`／`W1 ReadyExecute` 仍未成立，`FIN_ORDER=DENY`
- 更新時間：{time.strftime('%Y-%m-%dT%H:%M:%S%z')}
"""
    n = 0
    for name in sorted(os.listdir(D)):
        if not (name.endswith("_r5.md") or "OWNER_DECISION_LIST" in name):
            continue
        p = os.path.join(D, name)
        s = open(p, encoding="utf-8").read()
        if HEAD in s:
            s = s.split(HEAD)[0].rstrip() + "\n"
        open(p, "w", encoding="utf-8", newline="\n").write(s.rstrip() + "\n" + block)
        n += 1
    print(json.dumps({"publish_note_appended": n, "remote_head": head}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
