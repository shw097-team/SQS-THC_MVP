"""OPS evidence collector for SST_PLP_PH01_W0_B0 (engineering evidence, not product Raw).

Runs the frozen candidate's test suite and records: file tree hashes, interpreter identity,
command, exit code, stdout/stderr, timestamps. Writes only inside 40_OPS/.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

W = Path(__file__).resolve().parents[1]
DEV = W / "20_DEV"
OPS = W / "40_OPS"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hashes(root: Path) -> dict:
    out = {}
    skip_dirs = {".logs", "__pycache__"}
    for p in sorted(root.rglob("*")):
        if p.is_file() and not (skip_dirs & set(p.parts)) and not p.name.endswith((".pyc",)):
            rel = str(p.relative_to(root)).replace("\\", "/")
            if rel.startswith("exec_") and "receipt" in rel:
                continue
            if ".attempts.ndjson" in rel:
                continue
            out[rel] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    joined = "\n".join(f"{v['sha256']}  {k}" for k, v in sorted(out.items()))
    return {"files": out, "file_count": len(out),
            "tree_sha256": hashlib.sha256(joined.encode()).hexdigest()}


def run(cmd, cwd, timeout=900):
    t0 = time.time()
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, timeout=timeout)
    return {
        "cmd": cmd,
        "cwd": str(cwd),
        "exit": p.returncode,
        "seconds": round(time.time() - t0, 2),
        "stdout": p.stdout.decode("utf-8", "replace"),
        "stderr": p.stderr.decode("utf-8", "replace"),
    }


def main() -> int:
    OPS.mkdir(exist_ok=True)
    before = tree_hashes(DEV)
    suite = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], DEV)
    after = tree_hashes(DEV)
    receipt = {
        "schema": "B0.OPS.ENGINEERING_EVIDENCE/1",
        "claim_ceiling": "ENGINEERING_EVIDENCE_NOT_PRODUCT_RAW",
        "subject": "SST/SQS-THC/PH01/E00",
        "batch_id": "B0",
        "effect_intent": "SOURCE_READ",
        "product_write_set": [],
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "environment": {
            "python": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            "cwd": os.getcwd(),
        },
        "candidate_before": before,
        "candidate_after": after,
        "candidate_unchanged_by_run": before["tree_sha256"] == after["tree_sha256"],
        "suite": suite,
    }
    (OPS / "ops_run.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding="utf-8")
    (OPS / "ops_stdout.txt").write_text(suite["stdout"] + suite["stderr"], encoding="utf-8")
    print(json.dumps({"exit": suite["exit"], "tree_sha256": before["tree_sha256"],
                      "unchanged": receipt["candidate_unchanged_by_run"],
                      "files": before["file_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
