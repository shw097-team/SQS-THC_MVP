#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seal the trust-anchor directories so no broad principal can write them.

Measured before sealing, this work tree inherits `Authenticated Users:(Modify)` from
C:\\Projects, which makes every descriptor inside it caller-writable and therefore not a
trust root.  Sealing removes inheritance and grants only the interactive owner, SYSTEM
and Administrators, then re-applies inheritance to the children so the descriptors carry
the sealed ACEs themselves.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "10_CODE"))
from b0_r3_receiver.rights import broad_write_holders  # noqa: E402

OWNER_SID = "S-1-5-21-2687334950-3868438633-1592137926-1000"      # DESKTOP-57EO414\user
SANDBOX_SID = "S-1-5-21-2687334950-3868438633-1592137926-1003"    # local group CodexSandboxUsers
TARGETS = [
    Path(r"C:\Projects\Agent_Workspace\FHS-5_Workspace\SST_PH01_W0_B0_R3_20261127\00_PREFLIGHT"),
    Path(r"C:\Projects\Agent_Workspace\FHS-5_Workspace\SST_PH01_W0_B0_R3_20261127\20_TESTS\fixture"),
]


def run(*args: str) -> tuple[int, str]:
    p = subprocess.run(["icacls", *args], capture_output=True)
    text = (p.stdout or b"").decode("mbcs", "replace") + (p.stderr or b"").decode("mbcs", "replace")
    return p.returncode, text.strip()


def main() -> int:
    report = []
    for d in TARGETS:
        d.mkdir(parents=True, exist_ok=True)
        before = broad_write_holders(d)
        rc1, out1 = run(str(d), "/inheritance:r",
                        "/grant:r", f"*{OWNER_SID}:(OI)(CI)F",
                        "/grant:r", "*S-1-5-18:(OI)(CI)F",
                        "/grant:r", "*S-1-5-32-544:(OI)(CI)F",
                        "/grant:r", f"*{SANDBOX_SID}:(OI)(CI)RX")
        rc2, out2 = run(str(d / "*"), "/reset")
        after_dir = broad_write_holders(d)
        files = sorted(p for p in d.rglob("*") if p.is_file())
        per_file = {str(p.name): broad_write_holders(p) for p in files}
        report.append({
            "dir": str(d),
            "broad_write_before": before,
            "icacls_dir_rc": rc1, "icacls_reset_rc": rc2,
            "broad_write_after_dir": after_dir,
            "broad_write_after_files": {k: v for k, v in per_file.items() if v},
            "files_checked": len(files),
            "ok": not after_dir and not any(per_file.values()),
        })
        if not report[-1]["ok"]:
            print(out1[:400]); print(out2[:400])
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if all(r["ok"] for r in report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
