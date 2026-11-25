"""Compute the B0 candidate freeze per正文 §06.4 over a spec-derived file set.

Included (spec §06.4: 程式／測試／規則檔；排除報告／暫存／manifest 自身):
  20_DEV/b0_reader/*.py      product program
  20_DEV/tests/*.py          tests
  00_PREFLIGHT/*.json        trusted descriptor + RequiredSetSpec rules
  20_DEV/RUN_TESTS.cmd       test entry

Manifest line = <relative POSIX path>\t<raw sha256>\t<byte length>\n, sorted by the
UTF-8 bytes of the relative path; candidate_digest = sha256(manifest bytes).

No globbing beyond the four explicit sets, no symlink following, no git blob hashes.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED (engineering tool, not product code)
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

W = Path(r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace")

SETS = (
    ("20_DEV/b0_reader", ".py"),
    ("20_DEV/tests", ".py"),
)
EXTRA = (
    "20_DEV/RUN_TESTS.cmd",
    "00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json",
    "00_PREFLIGHT/required_set_req12_read_all_2026-11-25.json",
    "00_PREFLIGHT/required_set_req12_read_w0m_2026-11-25.json",
)


def collect() -> list[str]:
    out: list[str] = []
    for rel_dir, suffix in SETS:
        base = W / rel_dir.replace("/", "\\")
        for name in sorted(p.name for p in base.iterdir() if p.is_file()):
            if not name.endswith(suffix):
                continue
            path = base / name
            if path.is_symlink():
                raise SystemExit(f"refusing symlinked candidate file: {path}")
            out.append(f"{rel_dir}/{name}")
    for rel in EXTRA:
        path = W / rel.replace("/", "\\")
        if not path.is_file():
            raise SystemExit(f"missing required file: {path}")
        out.append(rel)
    return sorted(set(out), key=lambda s: s.encode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(W / "40_OPS" / "candidate_freeze.json"))
    args = ap.parse_args()

    lines: list[bytes] = []
    files: dict[str, dict] = {}
    for rel in collect():
        payload = (W / rel.replace("/", "\\")).read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        files[rel] = {"sha256": digest, "bytes": len(payload)}
        lines.append(f"{rel}\t{digest}\t{len(payload)}\n".encode("utf-8"))
    manifest = b"".join(lines)
    digest = hashlib.sha256(manifest).hexdigest()

    record = {
        "schema": "SST-B0-CANDIDATE-FREEZE/1",
        "algorithm": "§06.4: sorted-by-utf8-posix-path; line=path<TAB>sha256<TAB>bytes<LF>; digest=sha256(manifest)",
        "root": str(W),
        "included_sets": [{"dir": d, "suffix": s} for d, s in SETS] + [{"file": f} for f in EXTRA],
        "candidate_digest": digest,
        "manifest_bytes": len(manifest),
        "file_count": len(files),
        "files": files,
        "excluded": "reports (30_VERIFY, 40_OPS evidence, CLOSEOUT/HANDOFF), __pycache__, .tmp_tests, non-.py/.json siblings, symlinks",
    }
    Path(args.out).write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"candidate_digest": digest, "file_count": len(files), "manifest_bytes": len(manifest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
