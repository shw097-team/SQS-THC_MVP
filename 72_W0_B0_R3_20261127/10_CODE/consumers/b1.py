# -*- coding: utf-8 -*-
"""B1's inbound entry for the B0 SourceReadSet/2 (thin wiring only).

B1's own product (RepoRoot/BASE/FDA/ROOTS) is out of scope.  What is here is the entry
B1 would call, carrying B1's independent expectation and its own readback.
"""
from __future__ import annotations

from .common import cli, run_entry

CONSUMER_ID = "B1"
ENTRY = "consumers.b1.receive_envelope"

# B1's own declaration, fixed before the envelope is read; the entry refuses if the
# pinned deployment disagrees with it.
EXPECTED = {
    "consumer_use": "B1 REPO/BASE/FDA/ROOTS inbound consumption of the B0 SourceReadSet",
    "sources": {
        "SST.ALL.W0.BLUEPRINT": {
            "required_fields": ["read"],
            "expected_raw_sha256": "dd37a40b112bf5aac379adb44285ec01409519f7af64418298375833859d01a1",
            "requirement_span": [572, 579],
        },
        "SST.W0M.MAIN": {
            "required_fields": ["read"],
            "expected_raw_sha256": "5670990d8f0faa571e21460919b4afd8c681396340583b47ed36a8a3b787da96",
            "requirement_span": [295, 307],
        },
    },
}


def receive_envelope(payload: bytes, *, now=None) -> dict:
    return run_entry(CONSUMER_ID, EXPECTED, payload,
                     entry=ENTRY, now=now)


if __name__ == "__main__":
    raise SystemExit(cli(CONSUMER_ID, EXPECTED, ENTRY))
