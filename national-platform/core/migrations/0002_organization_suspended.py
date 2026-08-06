# Generated manually for SUSPENDED status
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('ACTIVE', 'Active'),
                    ('SUSPENDED', 'Suspended'),
                    ('REJECTED', 'Rejected')
                ],
                default='PENDING',
                max_length=10
            ),
        ),
    ]
