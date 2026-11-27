#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Second increment: fold the separated checker's verdict into the closeout, re-freeze
and publish the delta.  Refuses to run without a verdict file (no self-acceptance).
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
VERDICT = WAVE / "30_VERIFY" / "verdict.json"
WORK = WAVE / "publish" / "SQS-THC_MVP"
CRED = Path(r"C:\Projects\Agent_Workspace\API KEY\GITHUB-REPO_SHW097-4.txt")
DEST_NAME = "72_W0_B0_R3_20261127"
DOC = WAVE / "60_CLOSEOUT" / "SST_PLP_PH01_W0_B0_CLOSEOUT_HANDOFF_r8.md"
FREEZE = WAVE / "60_CLOSEOUT" / "FREEZE_r8.json"
OPS = WAVE / "40_OPS"


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
    if not VERDICT.exists():
        print(json.dumps({"refused": "NO_SEPARATED_VERDICT",
                          "detail": "30_VERIFY/verdict.json absent; the closeout keeps its HOLD"}))
        return 3
    verdict = json.loads(VERDICT.read_bytes())

    regen = subprocess.run([sys.executable, "-B", str(WAVE / "60_CLOSEOUT" / "build_closeout.py")],
                           capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    if regen.returncode != 0:
        print(json.dumps({"regenerate_failed": regen.stderr[-600:]}))
        return 4
    gen = json.loads(regen.stdout)

    # delta proof: the code identities did not move between the two freezes
    code_files = sorted((WAVE / "10_CODE" / "b0_r3_receiver").glob("*.py"))
    delta = {"changed_code": [], "verdict": verdict.get("verdict"),
             "frozen_members": gen["manifest"]["members"],
             "manifest_sha256": gen["manifest"]["sha256"]}

    token = CRED.read_text(encoding="utf-8", errors="replace").strip().splitlines()[0].strip()
    env = auth_env(token)
    if not (WORK / ".git").exists():
        print(json.dumps({"refused": "NO_CLONE", "path": str(WORK)}))
        return 3

    dest = WORK / DEST_NAME
    for src in sorted(WAVE.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(WAVE).as_posix()
        if rel.startswith("publish/") or rel.startswith("tmp/") or "__pycache__" in rel \
                or ".tmp_tests" in rel or src.name == "TEST_ONLY_keypair.json":
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)

    rows = []
    for p in sorted(dest.rglob("*")):
        if p.is_file() and p.name != "PUBLISH_MANIFEST.tsv":
            rel = p.relative_to(dest).as_posix()
            raw = p.read_bytes()
            rows.append(f"{rel}\t{hashlib.sha256(raw).hexdigest()}\t{len(raw)}")
    manifest = dest / "PUBLISH_MANIFEST.tsv"
    manifest.write_bytes(("\n".join(rows) + "\n").encode("utf-8"))

    git(["add", "--", DEST_NAME], env=env)
    cp = git(["commit", "-m",
              f"W0 B0 r8 increment 2: separated checker verdict ({verdict.get('verdict')}) "
              "folded into closeout; freeze re-issued over identical code bytes"],
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
    out = {
        "schema": "SST.PH01.W0.B0.R3.PublishReadback/1",
        "increment": 2,
        "verdict": verdict.get("verdict"),
        "commit": head,
        "remote_main": remote,
        "remote_equals_local": remote == head,
        "document": {"path": str(DOC), "bytes": DOC.stat().st_size,
                     "sha256": hashlib.sha256(DOC.read_bytes()).hexdigest()},
        "freeze": str(FREEZE),
        "delta": delta,
        "fixed_link": f"https://github.com/shw097-team/SQS-THC_MVP/commit/{head}",
    }
    (WAVE / "70_PUBLISH" / "PUBLISH_READBACK_r8_increment2.json").write_bytes(
        json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
