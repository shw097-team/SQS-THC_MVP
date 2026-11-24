"""B0 source-reader author candidate.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED

This package implements the isolated PH01/E00 W0-B0 development surface. It is
not a product-admitted reader and does not declare ReadyExecute or ReadyAccept.
"""

from .bytes_ import read_bytes
from .errors import ERROR_CODES, build_envelope, build_error
from .fields import split_fields
from .return_ import build_read_set, to_envelope
from .root import check_root

__all__ = [
    "ERROR_CODES",
    "build_envelope",
    "build_error",
    "build_read_set",
    "check_root",
    "read_bytes",
    "split_fields",
    "to_envelope",
]
