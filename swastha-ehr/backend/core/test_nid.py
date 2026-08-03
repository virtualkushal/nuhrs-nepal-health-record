"""
Tests for the standardized Nepal NIN (National Identity Number) rule.

The whole platform now agrees on a single format: exactly 11 numeric digits.
These tests pin that behaviour at the SwasthyaEHR serializer boundary, which is
where patient intake is validated before anything is persisted or shared.
"""
from datetime import date

from django.test import TestCase

from core.serializers import PatientSerializer


def _payload(**overrides):
    data = {
        "national_id": "12345678901",
        "first_name": "Ram",
        "last_name": "Bahadur",
        "phone_number": "+977-9841000001",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "blood_group": "O+",
    }
    data.update(overrides)
    return data


class NIDValidationTests(TestCase):
    def test_accepts_exactly_11_digits(self):
        s = PatientSerializer(data=_payload())
        self.assertTrue(s.is_valid(), s.errors)

    def test_normalizes_spaces_and_hyphens(self):
        s = PatientSerializer(data=_payload(national_id="12345-678 901"))
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["national_id"], "12345678901")

    def test_rejects_10_digits(self):
        s = PatientSerializer(data=_payload(national_id="1234567890"))
        self.assertFalse(s.is_valid())
        self.assertIn("national_id", s.errors)

    def test_rejects_12_digits(self):
        s = PatientSerializer(data=_payload(national_id="123456789012"))
        self.assertFalse(s.is_valid())
        self.assertIn("national_id", s.errors)

    def test_rejects_non_numeric(self):
        s = PatientSerializer(data=_payload(national_id="ABC45678901"))
        self.assertFalse(s.is_valid())
        self.assertIn("national_id", s.errors)
