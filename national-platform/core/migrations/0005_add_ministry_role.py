# Generated manually for the MINISTRY role.
#
# Choices-only change: `role` is already CharField(max_length=20), which fits
# "MINISTRY", so this alters the field's choices metadata with NO column or SQL
# schema change. Precedent: 0002_organization_suspended did the same for status.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_ssoticket"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("SUPER_ADMIN", "Super Admin"),
                    ("MINISTRY", "Ministry"),
                    ("ORGANIZATION_ADMIN", "Organization Admin"),
                    ("DOCTOR", "Doctor"),
                    ("LAB_TECHNICIAN", "Lab Technician"),
                    ("PATIENT", "Patient"),
                ],
                max_length=20,
            ),
        ),
    ]
