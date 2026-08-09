"""
Push this SwasthyaEHR instance's clinical record metadata to the National
Platform index so a patient's records here become discoverable federation-wide.

Only lightweight pointers leave the building (NID + patient demographics +
resource type + local UUID + a one-line summary). The actual clinical data is
fetched back on demand through core.nuhrs_adapter (the NID-keyed FHIR endpoints).

Since core.nuhrs_publish.push_patient_records is also wired to post_save signals,
this command is mainly for initial seeding / re-sync after local data edits.

Usage:
    python manage.py nuhrs_push          # push all patients' records
    python manage.py nuhrs_push --nid 1234500001

Idempotent for a demo: the platform upserts index rows on
(org, resource_type, local_record_id), so re-running is safe.
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import Patient
from core.nuhrs_publish import push_patient_records


class Command(BaseCommand):
    help = "Index this hospital's clinical records on the National Platform."

    def add_arguments(self, parser):
        parser.add_argument("--nid", help="Only push records for this national ID.")

    def handle(self, *args, **options):
        if not settings.NUHRS_ENABLED:
            self.stdout.write(self.style.WARNING("NUHRS_ENABLED is False - nothing pushed."))
            return

        patients = Patient.objects.all()
        if options.get("nid"):
            patients = patients.filter(national_id=options["nid"])
        if not patients:
            self.stdout.write(self.style.WARNING("No patients to index."))
            return

        for patient in patients:
            if not patient.national_id:
                self.stdout.write(self.style.WARNING(f"  = {patient} has no NID - skipped"))
                continue
            push_patient_records(patient)

        self.stdout.write(self.style.SUCCESS(f"Indexed {settings.NUHRS_ORG_CODE} records on the platform."))