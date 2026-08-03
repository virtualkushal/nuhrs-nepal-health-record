"""Tests for the canonical LOINC terminology resolver in the hospital service."""
from django.test import SimpleTestCase

from clinical import terminology


class TerminologyResolutionTests(SimpleTestCase):
    def test_synonyms_resolve_to_same_code(self):
        self.assertEqual(
            terminology.observable_coding("Fasting Blood Glucose")["code"],
            terminology.observable_coding("FBS")["code"],
        )
        self.assertEqual(terminology.observable_coding("Fasting Blood Sugar")["code"], "1558-6")
        self.assertEqual(
            terminology.observable_coding("HbA1c")["code"],
            terminology.observable_coding("Glycated Hemoglobin")["code"],
        )
        self.assertEqual(terminology.observable_coding("Serum Creatinine")["code"], "2160-0")

    def test_unmapped_returns_none(self):
        self.assertIsNone(terminology.observable_coding("Mystery Analyte X"))

    def test_integrity(self):
        self.assertEqual(terminology.check_integrity(), [])