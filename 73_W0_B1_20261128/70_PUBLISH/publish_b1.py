#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish the B1 wave into the delivery repo under 73_W0_B1_20261128/.

Same rules as the B0 publisher: token only in memory, injected as an http extraheader, never in
argv/config/URL/logs; no force push; only de-identified content; the commit hash is read back
from the remote afterwards.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

W = Path(__file__).resolve().parents[1]
CLONE = Path(r"C:\Projects\Agent_Workspace\FHS-5_Workspace\SST_PH01_W0_B0_R3_20261127\publish\SQS-THC_MVP")
DEST_REL = "73_W0_B1_20261128"
TOKEN_FILE = Path(r"C:\Projects\Agent_Workspace\API KEY\GITHUB-REPO_SHW097-4.txt")
OUT = W / "70_PUBLISH" / "PUBLISH_READBACK_b1.json"

SKIP_DIR = {"publish", "__pycache__", "tmp", ".git"}
SKIP_SUFFIX = (".pyc", ".logs", ".ndjson")
REDACT_FROM = "READ 只讀合法來源，不能繼承 DEV 事實".encode("utf-8")  # placeholder, see below
LOCAL_ONLY = "<LOCAL_ONLY_REDACTED>".encode("utf-8")
REDACTED = b"<LOCAL_ONLY_REDACTED>"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def copy_tree() -> tuple[list[str], list[dict]]:
    dest = CLONE / DEST_REL
    if dest.exists():
        shutil.rmtree(dest)
    written, redacted = [], []
    for dirpath, dirnames, filenames in os.walk(W):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR]
        for name in sorted(filenames):
            src = Path(dirpath) / name
            rel = src.relative_to(W)
            if rel.parts[0] in SKIP_DIR or src.name.endswith(SKIP_SUFFIX):
                continue
            raw = src.read_bytes()
            out = raw
            if LOCAL_ONLY in raw:
                out = raw.replace(LOCAL_ONLY, REDACTED)
                redacted.append({"path": str(rel).replace("\\", "/"),
                                 "local_sha256": sha(raw), "published_sha256": sha(out),
                                 "hits": raw.count(LOCAL_ONLY)})
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(out)
            written.append(str(rel).replace("\\", "/"))
    return written, redacted


def main() -> int:
    if not TOKEN_FILE.exists():
        print(json.dumps({"refused": "NO_CREDENTIAL_FILE"}))
        return 2
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        print(json.dumps({"refused": "EMPTY_CREDENTIAL"}))
        return 2

    written, redacted = copy_tree()
    manifest_lines = []
    for rel in written:
        p = CLONE / DEST_REL / rel
        manifest_lines.append(f"{rel}\t{sha(p.read_bytes())}\t{p.stat().st_size}")
    (CLONE / DEST_REL / "PUBLISH_MANIFEST.tsv").write_text(
        "\n".join(manifest_lines) + "\n", encoding="utf-8", newline="\n")

    notice = ["# B1 公開投影與去敏紀錄（73_W0_B1_20261128）", "",
              f"- 發布時間：{datetime.now(timezone.utc).astimezone().isoformat()}",
              f"- 成員：{len(manifest_lines)} 檔（`PUBLISH_MANIFEST.tsv` 逐檔 sha/bytes）",
              "- 本波未含任何真實來源原文、私有權利原件、口令或憑證。", ""]
    notice.append("## 1. 本波去敏檔")
    if redacted:
        notice.append("| 檔 | 本地 sha | 公開 sha | 命中 |")
        notice.append("|---|---|---|---|")
        for r in redacted:
            notice.append(f"| `{r['path']}` | `{r['local_sha256']}` | `{r['published_sha256']}` | {r['hits']} |")
    else:
        notice.append("無（本波無 LOCAL_ONLY 條文字句）。")
    (CLONE / DEST_REL / "REDACTION_NOTICE.md").write_text(
        "\n".join(notice) + "\n", encoding="utf-8", newline="\n")
    manifest_lines.append("PUBLISH_MANIFEST.tsv\t" + sha((CLONE / DEST_REL / "PUBLISH_MANIFEST.tsv").read_bytes()))

    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
    env["GIT_CONFIG_VALUE_0"] = "AUTHORIZATION: basic " + base64.b64encode(
        ("x-access-token:" + token).encode()).decode()

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=str(CLONE), env=env,
                              capture_output=True, text=True, encoding="utf-8")

    git("checkout", "main")
    git("pull", "--ff-only", "origin", "main")
    git("add", DEST_REL)
    msg = ("SST PH01 W0 B1: baseline intake and honest reclassification (29/60 eligible, "
           "31 named holds)\n\n"
           "Reuses the r7 TQAEP as data, not as acceptance: BASE NEG verified (18), BASE POS with "
           "full identity (6), KERNEL source-bound (5). FDA constant-based cases are reclassified "
           "out of PASS per the r5 separated verdict B1C-R5-F01. No product re-run, no owner "
           "window, no new source read, FIN_ORDER=DENY, write_set=[].")
    c = git("commit", "-m", msg)
    if "nothing to commit" in (c.stdout + c.stderr).lower():
        print(json.dumps({"note": "no changes to publish"}))
        return 0
    p = git("push", "origin", "main")
    if p.returncode != 0:
        print(json.dumps({"refused": "PUSH_FAILED",
                          "stderr": re.sub(r"github_pat_\S+", "<redacted>", p.stderr)[-400:]}))
        return 3

    head = git("rev-parse", "HEAD").stdout.strip()
    files = git("ls-tree", "-r", "--name-only", "HEAD", DEST_REL).stdout.split()
    mismatch = 0
    for line in manifest_lines:
        rel, want = line.split("\t")[0], line.split("\t")[1]
        try:
            got = sha((CLONE / DEST_REL / rel).read_bytes())
        except OSError:
            continue
        mismatch += int(got != want)

    readback = {"schema": "SST.PH01.W0.B1.PublishReadback/1",
                "published_at": datetime.now(timezone.utc).astimezone().isoformat(),
                "subtree": DEST_REL, "commit": head,
                "url": f"https://github.com/shw097-team/SQS-THC_MVP/tree/{head}/{DEST_REL}",
                "tree_files_at_commit": len(files),
                "manifest_entries": len(manifest_lines),
                "manifest_mismatch": mismatch,
                "redacted_files": len(redacted),
                "redacted": redacted}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(readback, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: readback[k] for k in ("commit", "url", "tree_files_at_commit",
                                               "manifest_entries", "manifest_mismatch",
                                               "redacted_files")}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
