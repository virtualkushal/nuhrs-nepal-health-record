"""
Validate the FHIR resources this hospital emits.

Runs the local records through the configured adapter and checks each emitted
resource against a minimal FHIR R4 structural contract (required fields per
resourceType). This proves the adapter output is standards-shaped BEFORE the
National Platform ever fetches it.

Run:  python manage.py validate_fhir            # validates every seeded patient
      python manage.py validate_fhir --nid 12345678901
"""
from django.core.management.base import BaseCommand

from clinical.fhir_views import _all_resources_for

from clinical.models import LocalPatient

# Minimal required-field contract per resourceType (FHIR R4).
REQUIRED = {
    "Patient": ["id", "identifier", "name"],
    "Encounter": ["id", "status", "class", "subject"],
    "Condition": ["id", "subject", "code"],
    "Observation": ["id", "status", "subject", "code"],
    "AllergyIntolerance": ["id", "patient", "code"],
    "DiagnosticReport": ["id", "status", "code", "subject"],
    "MedicationRequest": ["id", "status", "intent", "subject", "medicationCodeableConcept"],
}


class Command(BaseCommand):
    help = "Validate emitted FHIR resources against a minimal R4 contract."

    def add_arguments(self, parser):
        parser.add_argument("--nid", help="Validate only this patient NID.")

    def handle(self, *args, **options):
        nids = ([options["nid"]] if options.get("nid")
                else list(LocalPatient.objects.values_list("nid", flat=True).distinct()))
        if not nids:
            self.stdout.write(self.style.WARNING("No patients found. Run seed first."))
            return

        total = errors = 0
        counts = {}
        for nid in nids:
            for res in _all_resources_for(nid):
                total += 1
                rtype = res.get("resourceType", "?")
                counts[rtype] = counts.get(rtype, 0) + 1
                for problem in self._check(res):
                    errors += 1
                    self.stdout.write(self.style.ERROR(f"  [{nid}] {rtype}/{res.get('id')}: {problem}"))

        summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        self.stdout.write("")
        self.stdout.write(f"Resource counts: {summary}")
        if errors:
            self.stdout.write(self.style.ERROR(f"FHIR validation FAILED: {errors} problem(s) in {total} resources."))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(f"FHIR validation PASSED: {total} resources, 0 problems."))

    def _check(self, res):
        """Yield human-readable problems for one resource; empty => valid."""
        rtype = res.get("resourceType")
        if not rtype:
            yield "missing resourceType"
            return
        required = REQUIRED.get(rtype)
        if required is None:
            yield f"unknown resourceType '{rtype}'"
            return
        for field in required:
            val = res.get(field)
            if val in (None, "", [], {}):
                yield f"missing required field '{field}'"
        # subject/patient must carry an NID identifier so the platform can link it.
        ref = res.get("subject") or res.get("patient")
        if ref is not None and isinstance(ref, dict):
            ident = ref.get("identifier", {})
            if not ident.get("value"):
                yield "subject/patient has no identifier.value (NID)"
