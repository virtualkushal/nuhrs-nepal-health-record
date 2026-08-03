"""Tests for the canonical LOINC terminology resolver in the lab service."""
from django.test import SimpleTestCase

from lab import terminology


class TerminologyResolutionTests(SimpleTestCase):
    def test_analytes_resolve(self):
        self.assertEqual(terminology.observable_coding("Hemoglobin")["code"], "718-7")
        self.assertEqual(terminology.observable_coding("WBC")["code"], "6690-2")
        self.assertEqual(terminology.observable_coding("Troponin I")["code"], "10839-9")
        self.assertEqual(terminology.observable_coding("Urea")["code"], "3094-0")

    def test_panels_resolve(self):
        self.assertEqual(terminology.panel_coding("Complete Blood Count")["code"], "58410-2")
        self.assertEqual(terminology.panel_coding("Lipid Profile")["code"], "57698-3")

    def test_unmapped_returns_none(self):
        self.assertIsNone(terminology.observable_coding("Mystery Analyte X"))
        self.assertIsNone(terminology.panel_coding("Cardiac Markers"))

    def test_integrity(self):
        self.assertEqual(terminology.check_integrity(), [])