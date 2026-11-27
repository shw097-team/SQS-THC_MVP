#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish this round's increment to SQS-THC_MVP and read the commit back.

Auth is one-shot: the credential is read into memory and passed through
GIT_CONFIG_COUNT/KEY/VALUE env vars, so it never reaches argv, a config file, a URL,
a log line or a commit.  Nothing sensitive is printed on failure.
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

WAVE = Path(r"C:\Projects\Agent_Workspace\FHS-5_Workspace\SST_PH01_W0_B0_R3_20261127")
WORK = WAVE / "publish" / "SQS-THC_MVP"
CRED = Path(r"C:\Projects\Agent_Workspace\API KEY\GITHUB-REPO_SHW097-4.txt")
REMOTE = "https://github.com/shw097-team/SQS-THC_MVP"
DEST_NAME = "72_W0_B0_R3_20261127"
CLUSTER = "0" * 64


def scrub(text: str, secret: str) -> str:
    return text.replace(secret, "<redacted>")


def git(args: list[str], *, env: dict, cwd: Path | None = None,
        check: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(["git", *args], cwd=str(cwd or WORK), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env)
    if check and p.returncode != 0:
        raise SystemExit(json.dumps({"git_failed": args[:3], "stderr": p.stderr[-800:]}))
    return p


def auth_env(token: str) -> dict:
    b64 = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    env = dict(os.environ)
    env.update({
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
        "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {b64}",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return env


def main() -> int:
    token = CRED.read_text(encoding="utf-8", errors="replace").strip().splitlines()[0].strip()
    env = auth_env(token)

    if not (WORK / ".git").exists():
        WORK.parent.mkdir(parents=True, exist_ok=True)
        p = subprocess.run(["git", "clone", "--depth", "1", REMOTE, str(WORK)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=env)
        if p.returncode != 0:
            print(json.dumps({"clone_failed": scrub(p.stderr[-600:], token)}))
            return 3
    head = git(["rev-parse", "HEAD"], env=env).stdout.strip()
    remote_head = git(["ls-remote", "origin", "refs/heads/main"], env=env).stdout.split()[0]

    dest = WORK / DEST_NAME
    skip_dirs = {"publish", "tmp", "__pycache__", ".tmp_tests", "fixture"}
    published, withheld = [], []
    for src in sorted(WAVE.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(WAVE).as_posix()
        if rel.startswith("publish/") or rel.startswith("tmp/") or "__pycache__" in rel \
                or ".tmp_tests" in rel:
            continue
        # the fixture's test private key never leaves the work root
        if src.name == "TEST_ONLY_keypair.json":
            withheld.append({"path": rel, "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
                             "reason": "test private key stays in the work root; the fixture "
                                       "public key and its receipt are published"})
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        published.append(rel)

    # a publish manifest so a reader can verify what actually travelled
    rows = []
    for rel in sorted(published):
        p = dest / rel
        raw = p.read_bytes()
        rows.append(f"{rel}\t{hashlib.sha256(raw).hexdigest()}\t{len(raw)}")
    ex = dest / "LOCAL_ONLY_EXCLUSIONS.json"
    ex.write_bytes(json.dumps({
        "schema": "SST.PH01.W0.B0.R3.PublishExclusions/1",
        "remote": REMOTE,
        "withheld": withheld,
        "force_pushed": False,
    }, ensure_ascii=False, indent=1).encode("utf-8"))
    rows.append("LOCAL_ONLY_EXCLUSIONS.json\t" + hashlib.sha256(ex.read_bytes()).hexdigest()
                + f"\t{ex.stat().st_size}")
    body = ("\n".join(rows) + "\n").encode("utf-8")
    (dest / "PUBLISH_MANIFEST.tsv").write_bytes(body)

    git(["add", "--", DEST_NAME], env=env)
    staged = git(["diff", "--cached", "--name-only"], env=env).stdout.splitlines()
    message = ("W0 B0 r8: R3 receiver repair (strict wire/tuple/rights/per-source accounting), "
               "three-consumer real receive against the owner-authorised B0 envelope, "
               "relocated product tree with renewed descriptor pin, closeout/handoff")
    cp = git(["commit", "-m", message], env=env, check=False)
    if cp.returncode != 0 and "nothing to commit" not in (cp.stdout + cp.stderr):
        print(json.dumps({"commit_failed": scrub(cp.stderr[-600:], token)}))
        return 4

    push = git(["push", "origin", "HEAD:main"], env=env, check=False)
    out = {"staged_files": len(staged), "commit_rc": cp.returncode,
           "push_rc": push.returncode,
           "push_stdout": scrub(push.stdout[-400:], token),
           "push_stderr": scrub(push.stderr[-600:], token)}
    if push.returncode != 0:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 5

    local_head = git(["rev-parse", "HEAD"], env=env).stdout.strip()
    fetched = subprocess.run(["git", "fetch", "origin", "main"], cwd=str(WORK),
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace", env=env)
    remote_after = git(["ls-remote", "origin", "refs/heads/main"], env=env).stdout.split()[0]
    tree = git(["rev-parse", "HEAD^{tree}"], env=env).stdout.strip()
    # read one published blob back through the API-independent path: remote ref -> local object
    blob = git(["cat-file", "-p", f"HEAD:{DEST_NAME}/PUBLISH_MANIFEST.tsv"], env=env).stdout
    readback = {
        "schema": "SST.PH01.W0.B0.R3.PublishReadback/1",
        "commit": local_head,
        "tree": tree,
        "parent": git(["rev-parse", "HEAD^"], env=env).stdout.strip(),
        "remote_main_before": remote_head,
        "remote_main_after": remote_after,
        "remote_equals_local": remote_after == local_head,
        "publish_manifest_bytes": len(blob.encode("utf-8")),
        "publish_manifest_lines": len([l for l in blob.splitlines() if l.strip()]),
        "files_published": len(published) + 2,
        "withheld": withheld,
        "fixed_link": f"https://github.com/shw097-team/SQS-THC_MVP/commit/{local_head}",
    }
    (WAVE / "70_PUBLISH").mkdir(exist_ok=True)
    (WAVE / "70_PUBLISH" / "PUBLISH_READBACK_r8.json").write_bytes(
        json.dumps(readback, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps(readback, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
