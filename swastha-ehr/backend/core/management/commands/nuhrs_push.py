"""
Push this SwasthyaEHR instance's clinical record metadata to the National
Platform index so a patient's records here become discoverable federation-wide.

Only lightweight pointers leave the building (NID + patient demographics +
resource type + local UUID + a one-line summary). The actual clinical data is
fetched back on demand through core.nuhrs_adapter (the NID-keyed FHIR endpoints).

Usage:
    python manage.py nuhrs_push          # push all patients' records
    python manage.py nuhrs_push --nid 1234500001

Idempotent enough for a demo: the platform creates a RecordIndex row per call,
so run once after seeding.
"""

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import Diagnosis, LabResult, Prescription, Patient


class Command(BaseCommand):
    help = "Index this hospital's clinical records on the National Platform."

    def add_arguments(self, parser):
        parser.add_argument("--nid", help="Only push records for this national ID.")

    def handle(self, *args, **options):
        if not settings.NUHRS_ENABLED:
            self.stdout.write(self.style.WARNING("NUHRS_ENABLED is False — nothing pushed."))
            return

        patients = Patient.objects.all()
        if options.get("nid"):
            patients = patients.filter(national_id=options["nid"])
        if not patients:
            self.stdout.write(self.style.WARNING("No patients to index."))
            return

        for patient in patients:
            if not patient.national_id:
                self.stdout.write(self.style.WARNING(f"  = {patient} has no NID — skipped"))
                continue
            meta = self._patient_meta(patient)
            self._push_conditions(patient, meta)
            self._push_observations(patient, meta)
            self._push_medications(patient, meta)

        self.stdout.write(self.style.SUCCESS(f"Indexed {settings.NUHRS_ORG_CODE} records on the platform."))

    # -- metadata builders --------------------------------------------------
    def _patient_meta(self, patient):
        return {
            "nid": patient.national_id,
            "full_name": f"{patient.first_name} {patient.last_name}".strip(),
            "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
            "gender": (patient.gender or "OTHER").upper(),
            "phone": patient.phone_number or "",
        }

    def _push_conditions(self, patient, meta):
        for dx in Diagnosis.objects.filter(patient=patient):
            summary = f"{dx.icd10_code}".strip()
            self._push(patient.national_id, meta, "Condition", dx.id,
                       dx.created_at.date(), summary or "Condition")

    def _push_observations(self, patient, meta):
        for res in LabResult.objects.filter(patient=patient):
            value = res.result_value if res.result_value else (res.report_text or "")
            summary = f"{res.test_code}: {value}".strip().strip(":").strip()
            self._push(patient.national_id, meta, "Observation", res.id,
                       res.created_at.date(), summary or "Observation")

    def _push_medications(self, patient, meta):
        for rx in Prescription.objects.filter(patient=patient):
            summary = f"{rx.medication_name} — {rx.dosage_instruction}".strip(" —")
            self._push(patient.national_id, meta, "MedicationRequest", rx.id,
                       rx.created_at.date(), summary or "MedicationRequest")

    # -- HTTP ---------------------------------------------------------------
    def _push(self, nid, meta, resource_type, local_id, service_date, summary):
        payload = {
            "nid": nid,
            "patient": meta,
            "resource_type": resource_type,
            "local_record_id": str(local_id),
            "service_date": str(service_date),
            "summary": summary,
        }
        url = f"{settings.NUHRS_PLATFORM_URL.rstrip('/')}/api/index/"
        try:
            resp = requests.post(
                url, json=payload,
                headers={"X-API-Key": settings.NUHRS_API_KEY},
                timeout=10,
            )
            self.stdout.write(f"  {resource_type} '{summary[:40]}' -> {resp.status_code}")
        except requests.RequestException as exc:
            self.stdout.write(self.style.ERROR(f"  {resource_type} push failed: {exc}"))
