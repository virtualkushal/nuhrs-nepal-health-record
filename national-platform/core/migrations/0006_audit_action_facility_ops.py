from django.db import migrations, models


class Migration(migrations.Migration):
    """Widen AuditLog.action for the facility-admin operations (STAFF_*,
    ORG_UPDATE, PASSWORD_RESET). Choices/max_length only — no data changes."""

    dependencies = [
        ("core", "0005_add_ministry_role"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("SEARCH", "Search"),
                    ("FETCH_ALL", "Fetch All"),
                    ("FETCH_ONE", "Fetch One"),
                    ("STAFF_DEACTIVATE", "Staff Deactivated"),
                    ("STAFF_REACTIVATE", "Staff Reactivated"),
                    ("STAFF_UPDATE", "Staff Updated"),
                    ("ORG_UPDATE", "Organization Updated"),
                    ("PASSWORD_RESET", "Password Reset"),
                ],
                max_length=20,
            ),
        ),
    ]
