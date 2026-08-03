"""Tests for the canonical LOINC terminology resolver (SwasthyaEHR side)."""
from django.test import SimpleTestCase

from core import terminology


class TerminologyResolutionTests(SimpleTestCase):
    def test_synonyms_resolve_to_same_code(self):
        self.assertEqual(
            terminology.observable_coding("Fasting Blood Glucose")["code"],
            terminology.observable_coding("FBS")["code"],
        )
        self.assertEqual(
            terminology.observable_coding("Fasting Blood Sugar")["code"], "1558-6"
        )
        self.assertEqual(
            terminology.observable_coding("Serum Creatinine")["code"], "2160-0"
        )
        self.assertEqual(terminology.observable_coding("HbA1c")["code"], "4548-4")
        self.assertEqual(terminology.observable_coding("LDL Cholesterol")["code"], "2089-1")

    def test_panels_resolve(self):
        self.assertEqual(terminology.panel_coding("Complete Blood Count")["code"], "58410-2")
        self.assertEqual(terminology.panel_coding("Lipid Profile")["code"], "57698-3")

    def test_unmapped_returns_none(self):
        self.assertIsNone(terminology.observable_coding("Mystery Analyte X"))
        self.assertIsNone(terminology.panel_coding("Cardiac Markers"))

    def test_normalize(self):
        self.assertEqual(terminology.normalize("  FBS  "), "fbs")
        self.assertEqual(terminology.normalize("Hb A1c"), "hba1c")

    def test_integrity(self):
        self.assertEqual(terminology.check_integrity(), [])
