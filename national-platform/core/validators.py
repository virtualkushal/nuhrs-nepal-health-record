"""
Shared NID (National Identity Number) validation.

Nepal's National Identity Number (NIN), issued by the Department of National ID
and Civil Registration under the National Identity Card and Registration Act,
2076, is an 11-digit, non-intelligible numeric identifier (no meaning is encoded
in the digits, and there is no public checksum). We therefore validate strictly
on format: exactly 11 digits after stripping spaces and hyphens.
"""
import re

from rest_framework import serializers

NID_RE = re.compile(r"^\d{11}$")


def normalize_nid(value: str) -> str:
    """Strip spaces/hyphens so '12345 678 901' and '12345-678-901' are accepted."""
    return re.sub(r"[\s-]", "", (value or "").strip())


def is_valid_nid(value: str) -> bool:
    return bool(NID_RE.match(normalize_nid(value)))


def validate_nid(value: str) -> str:
    """Return the normalized NID or raise a DRF ValidationError."""
    nid = normalize_nid(value)
    if not NID_RE.match(nid):
        raise serializers.ValidationError(
            "National ID must be exactly 11 digits (Nepal NIN)."
        )
    return nid
