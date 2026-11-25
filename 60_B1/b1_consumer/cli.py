"""CLI: accept a B0 v2 envelope the way B1 would.

python -B -m b1_consumer.cli receive --envelope <file|-> --context <ctx.json> --out <receipt.json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .receiver import Reject, load_context, receive


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -B -m b1_consumer.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("receive")
    r.add_argument("--envelope", required=True)
    r.add_argument("--context", required=True)
    r.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        context = load_context(a.context)
        payload = sys.stdin.buffer.read() if a.envelope == "-" else Path(a.envelope).read_bytes()
        receipt = receive(payload, context)
    except Reject as exc:
        sys.stderr.write(f"{exc.first_fail}: {exc.detail}\n")
        return 2
    except Exception as exc:  # noqa: BLE001 - typed surface only
        sys.stderr.write(f"CONSUMER_ERROR: {type(exc).__name__}\n")
        return 70
    Path(a.out).write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"verdict": receipt["verdict"], "accepted": len(receipt["accepted"]),
                      "rejected": len(receipt["rejected"]), "errors": len(receipt["errors"]),
                      "first_fail": receipt["first_fail"], "out": a.out}, ensure_ascii=False))
    return 0 if receipt["verdict"] == "ACCEPTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
