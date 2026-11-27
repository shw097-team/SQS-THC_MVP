# -*- coding: utf-8 -*-
"""CLI for the R3 receiver.

    python -B -m b0_r3_receiver.cli receive --consumer B1 --envelope <file|-> --out <path>

There is deliberately no `--context`/`--root`/`--epoch`: the deployment descriptor is
authenticated from the pinned registry, so a caller cannot authorise itself.
`--out` writes one engineering receipt; the product SOURCE_READ write_set stays `[]`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import deployment
from .receiver import receive
from .wire import Reject

EXIT_OK, EXIT_REJECT, EXIT_USAGE, EXIT_TRUST = 0, 2, 64, 65


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    for bad in deployment.REFUSED_ARGUMENTS:
        if any(a == bad or a.startswith(bad + "=") for a in argv):
            print(json.dumps({"refused": "CALLER_SUPPLIED_TRUST_ROOT",
                              "argument": bad,
                              "detail": "the deployment descriptor is pinned; a caller path is "
                                        "not a trust root"}, ensure_ascii=False))
            return EXIT_USAGE

    ap = argparse.ArgumentParser(prog="b0_r3_receiver", add_help=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    rec = sub.add_parser("receive")
    rec.add_argument("--consumer", required=True, choices=["B1", "B2", "B3"])
    rec.add_argument("--envelope", required=True, help="path to the envelope bytes, or - for stdin")
    rec.add_argument("--deployment", default="prod", choices=["prod", "fixture"])
    rec.add_argument("--out", default=None, help="engineering recorder path")
    ap.add_argument("--version", action="version", version="b0-r3-receiver/1.0.0")
    args = ap.parse_args(argv)

    try:
        dep = deployment.load(args.deployment)
    except Reject as exc:
        print(json.dumps({"refused": exc.code, "detail": exc.detail}, ensure_ascii=False))
        return EXIT_TRUST

    if args.envelope == "-":
        payload = sys.stdin.buffer.read()
    else:
        payload = Path(args.envelope).read_bytes()

    receipt = receive(dep, args.consumer, payload, deployment_ref=dep.get("_deployment_ref"))
    text = json.dumps(receipt, ensure_ascii=False, indent=1)
    if args.out:
        p = Path(args.out)
        if p.exists():
            print(json.dumps({"refused": "PREIMAGE_NOT_ABSENT", "path": str(p)}))
            return EXIT_USAGE
        with open(p, "xb") as fh:
            fh.write(text.encode("utf-8") + b"\n")
        print(json.dumps({"written": str(p), "verdict": receipt["verdict"],
                          "consumer_id": receipt["consumer_id"]}, ensure_ascii=False))
    else:
        print(text)
    return EXIT_OK if receipt["verdict"] == "ACCEPTED" else EXIT_REJECT


if __name__ == "__main__":
    raise SystemExit(main())
