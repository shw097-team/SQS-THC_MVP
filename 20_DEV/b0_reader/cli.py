"""Read-only B0 v2 command-line interface.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import BinaryIO

from .native_entry import TrustContextError, resolve_context_for_current_principal
from .return_ import InvocationError, parse_request, read_sources


class _CliArgumentError(Exception):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _CliArgumentError()


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog="python -B -m b0_reader.cli",
        description="Read explicitly authorized B0 sources without writing.",
    )
    subparsers = parser.add_subparsers(dest="operation", required=True)
    read = subparsers.add_parser(
        "read",
        help="read a B0ReadRequest/2 from standard input",
    )
    read.add_argument(
        "--request-json",
        required=True,
        choices=("-",),
        metavar="-",
        help="read one UTF-8 JSON object from standard input",
    )
    return parser


def _emit(code: str) -> None:
    sys.stderr.write(code)


def _emit_json(rendered: str) -> None:
    stream = getattr(sys.stdout, "buffer", None)
    if stream is None:
        sys.stdout.write(rendered)
        return
    stream.write(rendered.encode("utf-8"))
    stream.flush()


def _stdin_stream(stdin: BinaryIO | None) -> BinaryIO:
    if stdin is not None:
        return stdin
    stream = getattr(sys.stdin, "buffer", None)
    if stream is None:
        raise InvocationError()
    return stream


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: BinaryIO | None = None,
) -> int:
    """Resolve trust before stdin, then emit one v2 JSON object or a fixed code."""

    try:
        args = _parser().parse_args(argv)
    except _CliArgumentError:
        _emit("INVOCATION_INVALID")
        return 64

    if args.operation != "read" or args.request_json != "-":
        _emit("INVOCATION_INVALID")
        return 64

    try:
        context = resolve_context_for_current_principal()
    except TrustContextError:
        _emit("TRUST_CONTEXT_UNBOUND")
        return 64
    except Exception:
        _emit("TRUST_CONTEXT_UNBOUND")
        return 70

    try:
        payload = _stdin_stream(stdin).read()
        if not isinstance(payload, bytes):
            raise InvocationError()
        request = parse_request(payload)
    except InvocationError as exc:
        _emit(exc.code)
        return 64
    except Exception:
        _emit("UNKNOWN_RECONCILE_REQUIRED")
        return 70

    try:
        envelope, exit_code = read_sources(
            request,
            trusted_context=context,
        )
    except Exception:
        _emit("UNKNOWN_RECONCILE_REQUIRED")
        return 70
    if exit_code not in (0, 2):
        code = getattr(envelope, "code", "UNKNOWN_RECONCILE_REQUIRED")
        if code not in (
            "INVOCATION_INVALID",
            "TRUST_CONTEXT_UNBOUND",
            "SUBJECT_MISMATCH",
            "SCOPE_MISMATCH",
            "EFFECT_DENIED",
            "UNKNOWN_RECONCILE_REQUIRED",
        ):
            code = "UNKNOWN_RECONCILE_REQUIRED"
        _emit(code)
        return exit_code if exit_code in (64, 70) else 70
    if not envelope:
        _emit("UNKNOWN_RECONCILE_REQUIRED")
        return 70
    try:
        rendered = json.dumps(
            envelope,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError):
        _emit("UNKNOWN_RECONCILE_REQUIRED")
        return 70
    if exit_code == 2 and envelope["errors"]:
        _emit(envelope["errors"][0]["code"])
    _emit_json(rendered)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
