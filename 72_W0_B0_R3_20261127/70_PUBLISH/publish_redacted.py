#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Increment 2: publish the {REV} candidate with LOCAL_ONLY clause text redacted.

The whole published directory is rebuilt from the work root so no earlier unredacted
copy stays in the tree; history is never rewritten, and REDACTION_NOTICE.md names what
the earlier commits already exposed.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

WAVE = Path(__file__).resolve().parents[1]
REV = os.environ.get("B0_REV", "r10")
WORK = WAVE / "publish" / "SQS-THC_MVP"
CRED = Path(r"C:\Projects\Agent_Workspace\API KEY\GITHUB-REPO_SHW097-4.txt")
DEST_NAME = "72_W0_B0_R3_20261127"
LOCAL_ONLY = "<LOCAL_ONLY_REDACTED>".encode("utf-8")
REDACTED = b"<LOCAL_ONLY_REDACTED>"
SKIP_NAMES = {"TEST_ONLY_keypair.json"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def auth_env(token: str) -> dict:
    b64 = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    env = dict(os.environ)
    env.update({"GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
                "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {b64}",
                "GIT_TERMINAL_PROMPT": "0"})
    return env


def git(args, env, check=True):
    p = subprocess.run(["git", *args], cwd=str(WORK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    if check and p.returncode != 0:
        raise SystemExit(json.dumps({"git_failed": args[:3], "stderr": p.stderr[-600:]}))
    return p


def main() -> int:
    if not (WORK / ".git").exists():
        print(json.dumps({"refused": "NO_CLONE"}))
        return 3
    token = CRED.read_text(encoding="utf-8", errors="replace").strip().splitlines()[0].strip()
    env = auth_env(token)
    dest = WORK / DEST_NAME
    if dest.exists():
        shutil.rmtree(dest)

    published, withheld, redacted = [], [], []
    for src in sorted(WAVE.rglob("*"),
                      key=lambda q: q.relative_to(WAVE).as_posix().encode("utf-8")):
        if not src.is_file():
            continue
        rel = src.relative_to(WAVE).as_posix()
        if (rel.startswith("publish/") or rel.startswith("tmp/") or "__pycache__" in rel
                or ".tmp_tests" in rel):
            continue
        if src.name in SKIP_NAMES:
            withheld.append({"path": rel, "sha256": sha(src.read_bytes()),
                             "reason": "test private key stays in the work root"})
            continue
        raw = src.read_bytes()
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if LOCAL_ONLY in raw:
            new = raw.replace(LOCAL_ONLY, REDACTED)
            target.write_bytes(new)
            redacted.append({"path": rel, "original_sha256": sha(raw), "original_bytes": len(raw),
                             "published_sha256": sha(new), "published_bytes": len(new),
                             "occurrences": raw.count(LOCAL_ONLY)})
        else:
            target.write_bytes(raw)
        published.append(rel)

    notice = [
        "# REDACTION NOTICE — LOCAL_ONLY clause text",
        "",
        f"This directory publishes the {REV} candidate of SST PH01 W0 B0 R3.",
        "",
        "The clause value carried by the B0 envelope is LOCAL_ONLY for its declared consumers.",
        "Every published copy therefore replaces that one clause sentence with",
        f"`{REDACTED.decode()}`; the pinned originals remain in the work root with the digests below.",
        "",
        "| path | original sha256 | published sha256 | occurrences |",
        "|---|---|---|---|",
    ]
    for r in redacted:
        notice.append(f'| `{r["path"]}` | `{r["original_sha256"]}` | `{r["published_sha256"]}` | {r["occurrences"]} |')
    notice += [
        "",
        "Consequences a reader must know:",
        "",
        "1. A redacted `observed.value` / `expected_value` no longer re-derives from the source, so the",
        "   published envelope and receipts are a *projection*; verify them against the local originals.",
        "2. The earlier commit `b144f63` in this repository published the unredacted r8 copies. History is",
        "   not rewritten; this notice is the record that those bytes disclosed one clause sentence.",
        "3. `20_TESTS/fixture/TEST_ONLY_keypair.json` is withheld (test private key); its public half and the",
        "   receipt it signed are published, so fixture verification still works.",
    ]
    (dest / "REDACTION_NOTICE.md").write_text("\n".join(notice) + "\n", encoding="utf-8")
    (dest / "LOCAL_ONLY_EXCLUSIONS.json").write_text(json.dumps({
        "schema": "SST.PH01.W0.B0.R3.PublishExclusions/1",
        "revision": REV,
        "withheld": withheld,
        "redacted": redacted,
        "force_pushed": False,
        "history_rewritten": False,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    rows = []
    for p in sorted(dest.rglob("*"), key=lambda q: q.relative_to(dest).as_posix().encode("utf-8")):
        if p.is_file() and p.name != "PUBLISH_MANIFEST.tsv":
            rel = p.relative_to(dest).as_posix()
            raw = p.read_bytes()
            rows.append(f"{rel}\t{sha(raw)}\t{len(raw)}")
    (dest / "PUBLISH_MANIFEST.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    leftover = [p for p in dest.rglob("*") if p.is_file() and LOCAL_ONLY in p.read_bytes()]
    if leftover:
        print(json.dumps({"refused": "UNREDACTED_FILE_REMAINS",
                          "files": [str(p.relative_to(dest)) for p in leftover]}))
        return 4

    git(["add", "-A", "--", DEST_NAME], env=env)
    cp = git(["commit", "-m",
              f"W0 B0 {REV}: redirect LOCAL_ONLY clause text out of the published copies; "
              "separated-checker round-2 repairs (manifest/epoch binding, doc figures, freeze order)"],
             env=env, check=False)
    if cp.returncode != 0 and "nothing to commit" not in (cp.stdout + cp.stderr):
        print(json.dumps({"commit_failed": cp.stderr[-600:]}))
        return 4
    push = git(["push", "origin", "HEAD:main"], env=env, check=False)
    if push.returncode != 0:
        print(json.dumps({"push_failed": push.stderr[-600:]}))
        return 5
    head = git(["rev-parse", "HEAD"], env=env).stdout.strip()
    remote = git(["ls-remote", "origin", "refs/heads/main"], env=env).stdout.split()[0]
    blob = git(["cat-file", "-p", f"HEAD:{DEST_NAME}/REDACTION_NOTICE.md"], env=env).stdout
    out = {
        "schema": "SST.PH01.W0.B0.R3.PublishReadback/1",
        "increment": 2,
        "revision": REV,
        "commit": head,
        "remote_main": remote,
        "remote_equals_local": remote == head,
        "files_published": len(published) + 2,
        "redacted_files": len(redacted),
        "withheld": withheld,
        "notice_readback_bytes": len(blob.encode("utf-8")),
        "notice_readback_has_redaction": "<LOCAL_ONLY_REDACTED>" in blob,
        "fixed_link": f"https://github.com/shw097-team/SQS-THC_MVP/commit/{head}",
    }
    (WAVE / "70_PUBLISH" / f"PUBLISH_READBACK_{REV}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
