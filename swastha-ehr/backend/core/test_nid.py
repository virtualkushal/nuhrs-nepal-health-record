"""
Tests for the standardized Nepal NIN (National Identification Number) rule, the
shared Nepal mobile-number rule, and the shared password policy.

The whole platform agrees on a single NIN format: exactly 10 numeric digits (per
DoNIDCR). These tests pin that behaviour at the SwasthyaEHR serializer boundary,
which is where patient intake is validated before anything is persisted or
shared.
"""
from datetime import date

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase

from core.serializers import PatientSerializer


def _payload(**overrides):
    data = {
        "national_id": "2345678901",
        "first_name": "Ram",
        "last_name": "Bahadur",
        "phone_number": "9841000001",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "blood_group": "O+",
    }
    data.update(overrides)
    return data


class NIDValidationTests(TestCase):
    def test_accepts_exactly_10_digits(self):
        s = PatientSerializer(data=_payload())
        self.assertTrue(s.is_valid(), s.errors)

    def test_normalizes_spaces_and_hyphens(self):
        s = PatientSerializer(data=_payload(national_id="2345-678 901"))
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["national_id"], "2345678901")

    def test_rejects_9_digits(self):
        s = PatientSerializer(data=_payload(national_id="234567890"))
        self.assertFalse(s.is_valid())
        self.assertIn("national_id", s.errors)

    def test_rejects_11_digits(self):
        s = PatientSerializer(data=_payload(national_id="12345678901"))
        self.assertFalse(s.is_valid())
        self.assertIn("national_id", s.errors)

    def test_rejects_non_numeric(self):
        s = PatientSerializer(data=_payload(national_id="ABC4567890"))
        self.assertFalse(s.is_valid())
        self.assertIn("national_id", s.errors)


class PhoneValidationTests(TestCase):
    """The shared Nepal mobile rule: optional +977/00977/0, stored bare 10 digits."""

    def test_accepts_bare_mobile(self):
        s = PatientSerializer(data=_payload(phone_number="9841000001"))
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["phone_number"], "9841000001")

    def test_normalizes_plus977_prefix(self):
        s = PatientSerializer(data=_payload(phone_number="+977-9841000001"))
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["phone_number"], "9841000001")

    def test_normalizes_00977_prefix(self):
        s = PatientSerializer(data=_payload(phone_number="009779841000001"))
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["phone_number"], "9841000001")

    def test_normalizes_leading_zero_prefix(self):
        s = PatientSerializer(data=_payload(phone_number="09841000001"))
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["phone_number"], "9841000001")

    def test_accepts_smart_cell_96_prefix(self):
        s = PatientSerializer(data=_payload(phone_number="9612345678"))
        self.assertTrue(s.is_valid(), s.errors)

    def test_rejects_landline(self):
        s = PatientSerializer(data=_payload(phone_number="014445555"))
        self.assertFalse(s.is_valid())
        self.assertIn("phone_number", s.errors)

    def test_rejects_wrong_operator_prefix(self):
        s = PatientSerializer(data=_payload(phone_number="9512345678"))
        self.assertFalse(s.is_valid())
        self.assertIn("phone_number", s.errors)

    def test_rejects_too_short(self):
        s = PatientSerializer(data=_payload(phone_number="984100000"))
        self.assertFalse(s.is_valid())
        self.assertIn("phone_number", s.errors)


class PasswordPolicyTests(TestCase):
    """>=8 chars with upper + lower + digit + special, enforced Django-natively."""

    def test_accepts_compliant_password(self):
        validate_password("Str0ng#Pass")

    def test_rejects_too_short(self):
        with self.assertRaises(DjangoValidationError):
            validate_password("Ab1#efg")

    def test_rejects_missing_uppercase(self):
        with self.assertRaises(DjangoValidationError):
            validate_password("str0ng#pass")

    def test_rejects_missing_lowercase(self):
        with self.assertRaises(DjangoValidationError):
            validate_password("STR0NG#PASS")

    def test_rejects_missing_digit(self):
        with self.assertRaises(DjangoValidationError):
            validate_password("Strong#Pass")

    def test_rejects_missing_special(self):
        with self.assertRaises(DjangoValidationError):
            validate_password("Str0ngPass")

