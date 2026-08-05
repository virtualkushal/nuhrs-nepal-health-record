"""
Sync Diagnosis.icd10_code choices with the expanded ICD10 vocabulary.

Adds the Nepal-endemic diagnoses (scrub typhus, kala-azar, Japanese
encephalitis, cholera, snakebite envenomation) to the field's choices. This is
a state-only change — `choices` are validated in forms/serializers, not enforced
at the database level — so no data migration is required.

The field references core.constants.ICD10.CHOICES directly so the migration
stays in lockstep with the single source of truth.
"""
from django.db import migrations, models

import core.constants


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_accessrequest_approved_by_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="diagnosis",
            name="icd10_code",
            field=models.CharField(choices=core.constants.ICD10.CHOICES, max_length=10),
        ),
    ]
