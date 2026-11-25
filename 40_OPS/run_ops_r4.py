"""Commander OPS harness for B0 v2 real runs (engineering recorder, NOT product code).

Runs `python -B -m b0_reader.cli read --request-json -` in W/20_DEV with a request on
stdin, and captures argv/cwd/exit/stdout/stderr/raw plus before/after no-write snapshots.

This recorder writes only under W/40_OPS. It performs no rights decision and never
mutates a source. AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

W = Path(r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace")
DEV = W / "20_DEV"
OPS = W / "40_OPS"
# The recorder's own outputs and the W-local test temp area are not product writes.
RECORDER_EXCLUDES = (
    "40_OPS/ops_run_",
    "40_OPS/ops_r4_",
    "40_OPS/lane_",
    "20_DEV/.tmp_tests/",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_snapshot(root: Path, exclude_prefixes: tuple[str, ...] = (), *, hash_contents: bool = False) -> dict:
    entries: dict[str, dict] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".git"}]
        for name in filenames:
            p = Path(dirpath) / name
            relative = str(p.relative_to(root)).replace("\\", "/")
            if any(relative.startswith(prefix) for prefix in exclude_prefixes):
                continue
            try:
                st = p.stat()
                rec = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
                if hash_contents and st.st_size <= 8 * 1024 * 1024:
                    rec["sha256"] = sha256_file(p)
                entries[relative] = rec
            except OSError as exc:  # transient sharing issues are recorded, not hidden
                entries[relative] = {"error": str(exc)}
    digest = hashlib.sha256(
        "".join(f"{k}\t{v.get('size')}\t{v.get('mtime_ns')}\n" for k, v in sorted(entries.items())).encode()
    ).hexdigest()
    return {"count": len(entries), "digest": digest, "entries": entries}


def diff_snapshots(before: dict, after: dict) -> dict:
    b, a = before["entries"], after["entries"]
    added = sorted(set(a) - set(b))
    removed = sorted(set(b) - set(a))
    changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    return {"added": added, "removed": removed, "changed": changed,
            "clean": not added and not removed and not changed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--label", default="")
    ap.add_argument("--extra-arg", action="append", default=[])
    args = ap.parse_args()

    request_bytes = args.request.read_bytes()
    outdir = args.out.parent
    outdir.mkdir(parents=True, exist_ok=True)
    rawdir = outdir / (args.out.stem + ".raw")
    rawdir.mkdir(exist_ok=True)

    watched = {
        "W_tree": tree_snapshot(W, RECORDER_EXCLUDES, hash_contents=True),
        "source_dir": tree_snapshot(Path(r"C:\Projects\Agent_Workspace\知識庫\SQS")),
    }
    source_stats = {}
    started = time.time()
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("TMPDIR", None)
    env["TEMP"] = str(DEV / ".tmp_tests")
    env["TMP"] = env["TEMP"]
    Path(env["TEMP"]).mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, "-B", "-m", "b0_reader.cli", "read", "--request-json", "-", *args.extra_arg]
    proc = subprocess.run(cmd, cwd=str(DEV), input=request_bytes, capture_output=True, env=env)
    elapsed = time.time() - started
    finished = time.time()

    stdout = proc.stdout
    stderr = proc.stderr
    so = rawdir / "stdout.txt"
    se = rawdir / "stderr.txt"
    so.write_bytes(stdout)
    se.write_bytes(stderr)

    after = {
        "W_tree": tree_snapshot(W, RECORDER_EXCLUDES, hash_contents=True),
        "source_dir": tree_snapshot(Path(r"C:\Projects\Agent_Workspace\知識庫\SQS")),
    }
    no_write = {name: diff_snapshots(watched[name], after[name]) for name in watched}

    record = {
        "schema": "SST-B0-OPS-RUN/1",
        "label": args.label,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "command": {
            "argv": cmd,
            "cwd": str(DEV),
            "python": sys.executable,
            "python_version": sys.version,
            "product_module_root": str(DEV / "b0_reader"),
        },
        "request": {
            "path": str(args.request),
            "bytes": len(request_bytes),
            "sha256": hashlib.sha256(request_bytes).hexdigest(),
        },
        "actual": {
            "exit": proc.returncode,
            "seconds": round(elapsed, 3),
            "stdout_bytes": len(stdout),
            "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
            "stderr_bytes": len(stderr),
            "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
            "stdout_raw": str(so),
            "stderr_raw": str(se),
            "stdout_truncated_for_report": stdout[:4000].decode("utf-8", "replace"),
            "stderr_text": stderr[:2000].decode("utf-8", "replace"),
        },
        "product_write_set": [],
        "no_write": {
            "before_digests": {k: v["digest"] for k, v in watched.items()},
            "after_digests": {k: v["digest"] for k, v in after.items()},
            "diff": no_write,
            "verdict": "NO_PRODUCT_WRITE_OBSERVED"
            if all(no_write[k]["clean"] for k in no_write)
            else "WRITE_OR_DRIFT_OBSERVED",
            "watch_note": "W tree compared by size+mtime_ns+raw sha256 (content); the K source root by size+mtime_ns; "
                          "this is a bounded observation, not a whole-disk guarantee.",
            "not_covered": [
                "OS-level write/process monitoring (ETW, ProcMon) not available to this recorder",
                "registry, network egress, bytecode in other interpreters, child processes",
                "TEMP/cache trees outside the two watched roots",
            ],
        },
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(finished)),
    }
    args.out.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: record[k] for k in ("label", "actual", "no_write")}, ensure_ascii=False)[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
