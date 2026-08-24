"""
NID (National Identity Number) validation for the lab service.

Nepal's NIN is a 10-digit, non-intelligible numeric identifier (no checksum),
issued by the Department of National ID and Civil Registration (DoNIDCR) under
the National Identity Card and Registration Act, 2076. We validate strictly on
format: exactly 10 digits after stripping spaces and hyphens.

This module also hosts the shared Nepal mobile-number rule so every service in
the federation applies an identical phone format.
"""
import re

NID_RE = re.compile(r"^\d{10}$")

# Nepal mobile numbers: NTC (984/985/986, 974/975), Ncell (980/981/982, 970/971)
# and Smart Cell (961/962, 988) all fall under the 9[678]XXXXXXXX pattern.
# An optional +977 / 00977 / 0 trunk prefix is accepted on input and stripped on
# normalization, so storage is always the bare 10-digit subscriber number.
NEPAL_MOBILE_RE = re.compile(r"^(\+977|00977|0)?9[678]\d{8}$")


class NIDValidationError(ValueError):
    """Raised when an NID does not match the Nepal NIN format."""


class PhoneValidationError(ValueError):
    """Raised when a phone number does not match the Nepal mobile format."""


def normalize_nid(value: str) -> str:
    return re.sub(r"[\s-]", "", (value or "").strip())


def is_valid_nid(value: str) -> bool:
    return bool(NID_RE.match(normalize_nid(value)))


def validate_nid(value: str) -> str:
    """Return the normalized NID or raise NIDValidationError."""
    nid = normalize_nid(value)
    if not NID_RE.match(nid):
        raise NIDValidationError(
            "National ID must be exactly 10 digits (Nepal NIN)."
        )
    return nid


def normalize_phone(value: str) -> str:
    """Strip separators and any +977 / 00977 / 0 prefix -> bare 10 digits."""
    cleaned = re.sub(r"[\s\-()]", "", (value or "").strip())
    if not NEPAL_MOBILE_RE.match(cleaned):
        return cleaned
    for prefix in ("+977", "00977"):
        if cleaned.startswith(prefix):
            return cleaned[len(prefix):]
    # A single leading 0 is the domestic trunk prefix; a leading 9 is already bare.
    if cleaned.startswith("0"):
        return cleaned[1:]
    return cleaned


def is_valid_phone(value: str) -> bool:
    return bool(NEPAL_MOBILE_RE.match(re.sub(r"[\s\-()]", "", (value or "").strip())))


def validate_phone(value: str) -> str:
    """Return the normalized 10-digit mobile or raise PhoneValidationError."""
    if not is_valid_phone(value):
        raise PhoneValidationError(
            "Enter a valid Nepal mobile number, e.g. 9841234567 or +9779841234567."
        )
    return normalize_phone(value)

