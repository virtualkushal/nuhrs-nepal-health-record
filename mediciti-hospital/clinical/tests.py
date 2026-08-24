"""
Tests for the shared NUHRS validation rules at this hospital edge service.

Pins the 10-digit Nepal NIN (DoNIDCR) and the shared Nepal mobile rule, so a
drift in either regex fails loudly here rather than silently breaking the
federation's NID-keyed FHIR lookups.
"""
from django.test import SimpleTestCase

from clinical.validators import (
    NIDValidationError,
    PhoneValidationError,
    is_valid_nid,
    is_valid_phone,
    normalize_nid,
    normalize_phone,
    validate_nid,
    validate_phone,
)


class NIDValidationTests(SimpleTestCase):
    def test_accepts_exactly_10_digits(self):
        self.assertTrue(is_valid_nid("2345678901"))
        self.assertEqual(validate_nid("2345678901"), "2345678901")

    def test_normalizes_spaces_and_hyphens(self):
        self.assertEqual(normalize_nid("2345-678 901"), "2345678901")
        self.assertEqual(validate_nid("2345-678 901"), "2345678901")

    def test_rejects_9_digits(self):
        self.assertFalse(is_valid_nid("234567890"))
        with self.assertRaises(NIDValidationError):
            validate_nid("234567890")

    def test_rejects_11_digits(self):
        self.assertFalse(is_valid_nid("12345678901"))
        with self.assertRaises(NIDValidationError):
            validate_nid("12345678901")

    def test_rejects_non_numeric(self):
        self.assertFalse(is_valid_nid("ABC4567890"))
        with self.assertRaises(NIDValidationError):
            validate_nid("ABC4567890")

    def test_error_message_states_10_digits(self):
        with self.assertRaises(NIDValidationError) as ctx:
            validate_nid("1")
        self.assertIn("exactly 10 digits", str(ctx.exception))


class PhoneValidationTests(SimpleTestCase):
    def test_accepts_bare_mobile(self):
        self.assertEqual(validate_phone("9841234567"), "9841234567")

    def test_strips_plus977(self):
        self.assertEqual(validate_phone("+9779841234567"), "9841234567")

    def test_strips_00977(self):
        self.assertEqual(validate_phone("009779841234567"), "9841234567")

    def test_strips_leading_zero(self):
        self.assertEqual(validate_phone("09841234567"), "9841234567")

    def test_ignores_separators(self):
        self.assertEqual(validate_phone("+977-984 123 4567"), "9841234567")

    def test_accepts_all_operator_prefixes(self):
        for number in ("9841234567", "9741234567", "9801234567", "9611234567", "9881234567"):
            self.assertTrue(is_valid_phone(number), number)

    def test_rejects_landline(self):
        self.assertFalse(is_valid_phone("014445555"))
        with self.assertRaises(PhoneValidationError):
            validate_phone("014445555")

    def test_rejects_unknown_operator_prefix(self):
        self.assertFalse(is_valid_phone("9512345678"))

    def test_rejects_too_short(self):
        self.assertFalse(is_valid_phone("984123456"))

    def test_normalize_leaves_invalid_input_untouched(self):
        self.assertEqual(normalize_phone("014445555"), "014445555")
