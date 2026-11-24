"""Read-only B0 command-line interface.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from .return_ import build_read_set


def _span(value: str) -> tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("span must be A:B")
    try:
        first, last = (int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("span bounds must be integers") from exc
    return first, last


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m b0_reader.cli")
    subparsers = parser.add_subparsers(dest="operation", required=True)
    read = subparsers.add_parser("read", help="read one source without writing")
    read.add_argument("--allowed-root", required=True)
    read.add_argument("--source", required=True)
    read.add_argument("--expected-sha")
    read.add_argument("--span", type=_span)
    read.add_argument(
        "--required-field",
        action="append",
        nargs="+",
        default=[],
        metavar="F",
    )
    read.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run a single read and print one JSON document to stdout."""

    args = _parser().parse_args(argv)
    required_fields: list[str] = []
    for group in args.required_field:
        required_fields.extend(group)
    result = build_read_set(
        "SST/SQS-THC/PH01/E00",
        None,
        "B0",
        [
            {
                "allowed_root": args.allowed_root,
                "source_ref": args.source,
                "expected_sha": args.expected_sha,
                "clause_span": args.span,
                "required_fields": required_fields,
                "observed": {},
                "verified_by_source": {},
            }
        ],
    )
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["entries"] and not result["errors"] else 2


if __name__ == "__main__":
    sys.exit(main())
