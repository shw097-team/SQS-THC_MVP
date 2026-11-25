"""B0 source-reader author candidate.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED

This package exposes the v2 source-read implementation without declaring
product admission, ReadyExecute, or ReadyAccept.
"""

from .bytes_ import read_bytes
from .errors import ERROR_CODES, SourceError, build_error, make_error
from .fields import extract_fields, split_fields
from .native_entry import (
    TrustContextError,
    TrustedContext,
    TrustedSource,
    revalidate_trusted_context,
    resolve_context_for_current_principal,
)
from .requiredset import (
    RequiredSetError,
    RequiredSetSpec,
    RuleSpec,
    load_required_set,
)
from .return_ import (
    InvocationError,
    candidate_digest,
    parse_request,
    read_sources,
)
from .root import check_root, validate_path_security

__all__ = [
    "ERROR_CODES",
    "InvocationError",
    "RequiredSetError",
    "RequiredSetSpec",
    "RuleSpec",
    "SourceError",
    "TrustContextError",
    "TrustedContext",
    "TrustedSource",
    "build_error",
    "candidate_digest",
    "check_root",
    "extract_fields",
    "load_required_set",
    "make_error",
    "parse_request",
    "read_bytes",
    "read_sources",
    "resolve_context_for_current_principal",
    "revalidate_trusted_context",
    "split_fields",
    "validate_path_security",
]
