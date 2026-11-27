#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v4 publisher: counts, notices and manifests are all derived from what git actually holds.

Defects this version closes (each found by a separated checker):
  * `.logs` directories are skipped by a predicate that actually matches their names;
  * the notice and the redaction list are built *after* `git add`, from tracked files only;
  * line-ending conventions of both manifests are declared;
  * the manifest is counted from `git ls-files`, so tree == rows + 1 is checkable.
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
REV = os.environ.get("B0_REV", "r12")
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
    residue = [ln.split(":", 2)[-1] for ln in grep.stdout.splitlines()
               if ln.strip() and not ln.split(":", 2)[-1].startswith(DEST_NAME)]

    withheld, skipped, redaction_src = [], [], {}
    for src in sorted(WAVE.rglob("*"),
                      key=lambda q: q.relative_to(WAVE).as_posix().encode("utf-8")):
        if not src.is_file():
            continue
        rel = src.relative_to(WAVE).as_posix()
        if rel.startswith("publish/") or rel.startswith("tmp/") or "__pycache__" in rel \
                or ".tmp_tests" in rel:
            continue
        if any(part.endswith(SKIP_SUFFIXES) for part in src.parts) or src.name.endswith(SKIP_SUFFIXES):
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
            redaction_src[rel] = {"original_sha256": sha(raw), "original_bytes": len(raw),
                                  "occurrences": raw.count(LOCAL_ONLY)}
        else:
            target.write_bytes(raw)

    leftover = [p for p in dest.rglob("*") if p.is_file() and LOCAL_ONLY in p.read_bytes()]
    if leftover:
        print(json.dumps({"refused": "UNREDACTED_FILE_REMAINS",
                          "files": [str(p.relative_to(dest)) for p in leftover]}))
        return 4

    # ---- what git actually received -------------------------------------------------
    git(["add", "-A", "--", DEST_NAME], env=env)
    tracked = [ln for ln in git(["ls-files", "--", DEST_NAME], env=env).stdout.splitlines() if ln]
    tracked_rel = [t[len(DEST_NAME) + 1:] for t in tracked]
    redacted = []
    for rel, meta in sorted(redaction_src.items(), key=lambda kv: kv[0].encode("utf-8")):
        if rel in tracked_rel:                       # only files the commit really carries
            disk = dest / rel
            redacted.append({"path": rel, "published_bytes": disk.stat().st_size,
                             "published_sha256": sha(disk.read_bytes()), **meta})

    notice = [
        "# REDACTION NOTICE — LOCAL_ONLY clause text",
        "",
        "This directory publishes the " + REV + " candidate of SST PH01 W0 B0 R3 (work root",
        "`SST_PH01_W0_B0_R3_20261127`).",
        "",
        "## 1. What was redacted in this wave (" + str(len(redacted)) + " files actually in the commit)",
        "",
        "The clause value carried by the B0 envelope is LOCAL_ONLY for its declared consumers.",
        "Every published copy replaces exactly that sentence with `" + REDACTED.decode() + "`.",
        "",
        "| path | original sha256 | published sha256 | occurrences |",
        "|---|---|---|---|",
    ]
    for r in redacted:
        notice.append('| `' + r["path"] + '` | `' + r["original_sha256"] + '` | `'
                      + r["published_sha256"] + '` | ' + str(r["occurrences"]) + ' |')
    notice += [
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
        notice.append("- `" + p + "`")
    if len(residue) > 80:
        notice.append("- … and " + str(len(residue) - 80)
                           + " more (`git grep -l -F` on the parent commit)")
    notice += [
        "",
        "## 4. Conventions and consequences",
        "",
        "1. `PUBLISH_MANIFEST.tsv` uses LF line endings and lists every tracked file under this",
        "   directory except itself; `git ls-tree -r` count == rows + 1 by construction.",
        "2. A redacted `observed.value` / `expected_value` no longer re-derives from the source, so the",
        "   published envelope and receipts are a *projection*. Verify them against the local originals.",
        "3. `20_TESTS/fixture/TEST_ONLY_keypair.json` is withheld (test private key). Its public half and",
        "   the receipt it signed are published, so fixture verification still works.",
        "4. Engine receipts git ignores (`*.logs/`, `*.ndjson`) are neither copied nor counted.",
    ]
    (dest / "REDACTION_NOTICE.md").write_text("\n".join(notice) + "\n", encoding="utf-8")
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
    git(["add", "-A", "--", DEST_NAME], env=env)

    tracked = [ln for ln in git(["ls-files", "--", DEST_NAME], env=env).stdout.splitlines()
               if ln and not ln.endswith("PUBLISH_MANIFEST.tsv")]
    rows = []
    for rel in sorted(tracked, key=lambda r: r.encode("utf-8")):
        raw = (WORK / rel).read_bytes()
        rows.append(rel[len(DEST_NAME) + 1:] + "\t" + sha(raw) + "\t" + str(len(raw)))
    (dest / "PUBLISH_MANIFEST.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    git(["add", "--", DEST_NAME + "/PUBLISH_MANIFEST.tsv"], env=env)

    cp = git(["commit", "-m",
              "W0 B0 " + REV + ": self-description matched to artefacts (freeze predicate, verdict "
              "roster, notice built from tracked files)"], env=env, check=False)
    if cp.returncode != 0 and "nothing to commit" not in (cp.stdout + cp.stderr):
        print(json.dumps({"commit_failed": cp.stderr[-600:]}))
        return 4
    push = git(["push", "origin", "HEAD:main"], env=env, check=False)
    if push.returncode != 0:
        print(json.dumps({"push_failed": push.stderr[-600:]}))
        return 5
    head = git(["rev-parse", "HEAD"], env=env).stdout.strip()
    remote = git(["ls-remote", "origin", "refs/heads/main"], env=env).stdout.split()[0]
    tree = git(["ls-tree", "-r", "--name-only", head, "--", DEST_NAME], env=env).stdout.splitlines()
    logs = [t for t in tree if ".logs" in t]
    out = {
        "schema": "SST.PH01.W0.B0.R3.PublishReadback/1",
        "increment": 4,
        "revision": REV,
        "commit": head,
        "remote_main": remote,
        "remote_equals_local": remote == head,
        "tree_files_at_commit": len(tree),
        "logs_in_commit": len(logs),
        "manifest_rows": len(rows),
        "manifest_matches_tree": len(tree) == len(rows) + 1,
        "redacted_files_in_commit": len(redacted),
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
