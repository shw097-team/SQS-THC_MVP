#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the receiver suite and record the counts as a receipt (cited by the closeout)."""
from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

WAVE = Path(__file__).resolve().parents[1]
OUT = WAVE / "30_VERIFY" / "receiver_test_run_r19.json"
sys.path.insert(0, str(WAVE / "10_CODE"))
sys.path.insert(0, str(WAVE / "20_TESTS"))


def main() -> int:
    loader = unittest.TestLoader()
    suite = loader.discover(str(WAVE / "20_TESTS"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    total = result.testsRun
    bad = len(result.failures) + len(result.errors)
    receipt = {
        "schema": "SST.PH01.W0.B0.R3.TestRun/1",
        "ran_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "suite": "20_TESTS/test_receiver.py",
        "tests_run": total,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "ok": bad == 0,
        "failed_ids": [str(t) for t, _ in result.failures + result.errors],
    }
    OUT.write_bytes(json.dumps(receipt, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps(receipt, ensure_ascii=False, indent=1))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
