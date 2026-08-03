"""
NID (National Identity Number) validation for the hospital service.

Nepal's NIN is an 11-digit, non-intelligible numeric identifier (no checksum),
issued under the National Identity Card and Registration Act, 2076. We validate
strictly on format: exactly 11 digits after stripping spaces and hyphens.
"""
import re

NID_RE = re.compile(r"^\d{11}$")


class NIDValidationError(ValueError):
    """Raised when an NID does not match the Nepal NIN format."""


def normalize_nid(value: str) -> str:
    return re.sub(r"[\s-]", "", (value or "").strip())


def is_valid_nid(value: str) -> bool:
    return bool(NID_RE.match(normalize_nid(value)))


def validate_nid(value: str) -> str:
    """Return the normalized NID or raise NIDValidationError."""
    nid = normalize_nid(value)
    if not NID_RE.match(nid):
        raise NIDValidationError(
            "National ID must be exactly 11 digits (Nepal NIN)."
        )
    return nid
