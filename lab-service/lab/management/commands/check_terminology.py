"""
Verify the canonical LOINC terminology tables are conflict-free, so every
facility emits identical FHIR codes for the same measurable property.

Exits non-zero if any conflict is found (safe to run in CI).
"""
from django.core.management.base import BaseCommand, CommandError

from lab import terminology


class Command(BaseCommand):
    help = "Check the canonical LOINC terminology for alias/code conflicts."

    def handle(self, *args, **options):
        issues = terminology.check_integrity()
        if issues:
            for issue in issues:
                self.stderr.write(self.style.ERROR(f"  [CONFLICT] {issue}"))
            raise CommandError(f"{len(issues)} terminology conflict(s) found.")
        self.stdout.write(
            self.style.SUCCESS(
                f"Terminology OK: {len(terminology.OBSERVABLES)} observables, "
                f"{len(terminology.PANELS)} panels, no conflicts."
            )
        )
