#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3 publisher: redacted copies, a manifest counted from git, an honest notice.

Rules enforced here (each one is a defect a separated checker found):
  * nothing git will ignore is copied, so the manifest cannot claim more files than the commit;
  * the publish manifest is built from `git ls-files`, not from the copy loop;
  * every copied file is re-read and the run refuses if one still carries the LOCAL_ONLY clause;
  * the notice names the clause residue that already exists elsewhere in the repository,
    measured with `git grep` on the parent commit, instead of implying the tree is clean.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

WAVE = Path(__file__).resolve().parents[1]
REV = os.environ.get("B0_REV", "r11")
WORK = WAVE / "publish" / "SQS-THC_MVP"
CRED = Path(r"C:\Projects\Agent_Workspace\API KEY\GITHUB-REPO_SHW097-4.txt")
DEST_NAME = "72_W0_B0_R3_20261127"
LOCAL_ONLY = "<LOCAL_ONLY_REDACTED>".encode("utf-8")
REDACTED = b"<LOCAL_ONLY_REDACTED>"
SKIP_SUFFIXES = (".logs", ".ndjson")
SKIP_NAMES = {"TEST_ONLY_keypair.json"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def auth_env(token: str) -> dict:
    b64 = base64.b64encode(("x-access-token:" + token).encode()).decode()
    env = dict(os.environ)
    env.update({"GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
                "GIT_CONFIG_VALUE_0": "AUTHORIZATION: basic " + b64,
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

    parent = git(["rev-parse", "HEAD"], env=env).stdout.strip()
    grep = git(["grep", "-l", "-F", LOCAL_ONLY.decode(), parent, "--", "."], env=env, check=False)
    residue_all = [ln.split(":", 2)[-1] for ln in grep.stdout.splitlines() if ln.strip()]
    residue = [p for p in residue_all if not p.startswith(DEST_NAME)]

    published, withheld, redacted, skipped = [], [], [], []
    for src in sorted(WAVE.rglob("*"),
                      key=lambda q: q.relative_to(WAVE).as_posix().encode("utf-8")):
        if not src.is_file():
            continue
        rel = src.relative_to(WAVE).as_posix()
        if rel.startswith("publish/") or rel.startswith("tmp/") or "__pycache__" in rel \
                or ".tmp_tests" in rel:
            continue
        if src.name.endswith(SKIP_SUFFIXES) or ".logs" in src.parts:
            skipped.append(rel)
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

    head_notice = [
        "# REDACTION NOTICE — LOCAL_ONLY clause text",
        "",
        "This directory publishes the " + REV + " candidate of SST PH01 W0 B0 R3 (work root",
        "`SST_PH01_W0_B0_R3_20261127`).",
        "",
        "## 1. What was redacted in this wave",
        "",
        "The clause value carried by the B0 envelope is LOCAL_ONLY for its declared consumers.",
        "Every published copy replaces exactly that sentence with `" + REDACTED.decode() + "`.",
        "",
        "| path | original sha256 | published sha256 | occurrences |",
        "|---|---|---|---|",
    ]
    for r in redacted:
        head_notice.append('| `' + r["path"] + '` | `' + r["original_sha256"] + '` | `'
                           + r["published_sha256"] + '` | ' + str(r["occurrences"]) + ' |')
    head_notice += [
        "",
        "## 2. What this publication cannot retract",
        "",
        "Commit `b144f63` in this repository published the unredacted r8 copies. History is not",
        "rewritten. This notice is the record that those bytes disclosed one clause sentence.",
        "",
        "## 3. Pre-existing residue elsewhere in this repository (" + str(len(residue))
        + " files at `" + parent[:12] + "`)",
        "",
        "The same sentence also sits in files this wave did not author. They are listed so the",
        "disclosure is complete; redacting them would rewrite other rounds' delivered bytes and is",
        "left to the rights holder.",
        "",
    ]
    for p in residue[:80]:
        head_notice.append("- `" + p + "`")
    if len(residue) > 80:
        head_notice.append("- … and " + str(len(residue) - 80)
                           + " more (`git grep -l -F` on the parent commit)")
    head_notice += [
        "",
        "## 4. Consequences a reader must know",
        "",
        "1. A redacted `observed.value` / `expected_value` no longer re-derives from the source, so the",
        "   published envelope and receipts are a *projection*. Verify them against the local originals",
        "   whose digests are in this table.",
        "2. `20_TESTS/fixture/TEST_ONLY_keypair.json` is withheld (test private key). Its public half and",
        "   the receipt it signed are published, so fixture verification still works.",
        "3. Engine receipts git ignores (`*.logs`, `*.attempts.ndjson`) are not published and not counted.",
    ]
    (dest / "REDACTION_NOTICE.md").write_text("\n".join(head_notice) + "\n", encoding="utf-8")
    (dest / "LOCAL_ONLY_EXCLUSIONS.json").write_text(json.dumps({
        "schema": "SST.PH01.W0.B0.R3.PublishExclusions/1",
        "revision": REV,
        "withheld": withheld,
        "redacted": redacted,
        "skipped_git_ignored": skipped,
        "preexisting_residue": {"parent": parent, "count": len(residue), "paths": residue},
        "force_pushed": False,
        "history_rewritten": False,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    leftover = [p for p in dest.rglob("*") if p.is_file() and LOCAL_ONLY in p.read_bytes()]
    if leftover:
        print(json.dumps({"refused": "UNREDACTED_FILE_REMAINS",
                          "files": [str(p.relative_to(dest)) for p in leftover]}))
        return 4

    git(["add", "-A", "--", DEST_NAME], env=env)
    tracked = [ln for ln in git(["ls-files", "--", DEST_NAME], env=env).stdout.splitlines()
               if ln and not ln.endswith("PUBLISH_MANIFEST.tsv")]
    rows = []
    for rel in sorted(tracked, key=lambda r: r.encode("utf-8")):
        raw = (WORK / rel).read_bytes()
        rows.append(rel[len(DEST_NAME) + 1:] + "\t" + sha(raw) + "\t" + str(len(raw)))
    (dest / "PUBLISH_MANIFEST.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    git(["add", "--", DEST_NAME + "/PUBLISH_MANIFEST.tsv"], env=env)
    tracked_final = [ln for ln in git(["ls-files", "--", DEST_NAME], env=env).stdout.splitlines() if ln]

    cp = git(["commit", "-m",
              "W0 B0 " + REV + ": freeze predicate enforced, publish counted from git, verdict "
              "rounds and LOCAL_ONLY residue disclosed"], env=env, check=False)
    if cp.returncode != 0 and "nothing to commit" not in (cp.stdout + cp.stderr):
        print(json.dumps({"commit_failed": cp.stderr[-600:]}))
        return 4
    push = git(["push", "origin", "HEAD:main"], env=env, check=False)
    if push.returncode != 0:
        print(json.dumps({"push_failed": push.stderr[-600:]}))
        return 5
    head = git(["rev-parse", "HEAD"], env=env).stdout.strip()
    remote = git(["ls-remote", "origin", "refs/heads/main"], env=env).stdout.split()[0]
    tree_count = len(git(["ls-tree", "-r", "--name-only", head, "--", DEST_NAME],
                         env=env).stdout.splitlines())
    out = {
        "schema": "SST.PH01.W0.B0.R3.PublishReadback/1",
        "increment": 3,
        "revision": REV,
        "commit": head,
        "remote_main": remote,
        "remote_equals_local": remote == head,
        "tree_files_at_commit": tree_count,
        "tracked_files": len(tracked_final),
        "manifest_rows": len(rows),
        "manifest_matches_tree": tree_count == len(rows) + 1,
        "redacted_files": len(redacted),
        "skipped_git_ignored": len(skipped),
        "withheld": withheld,
        "preexisting_residue_files": len(residue),
        "fixed_link": "https://github.com/shw097-team/SQS-THC_MVP/commit/" + head,
    }
    (WAVE / "70_PUBLISH" / ("PUBLISH_READBACK_" + REV + ".json")).write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
