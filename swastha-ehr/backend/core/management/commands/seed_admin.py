"""
Create (or ensure) a default ADMIN account for local development / first run.

Login is by EMAIL in v2.

Usage:
    python manage.py seed_admin
    python manage.py seed_admin --email boss@swasthya.org.np --password secret123 --name "Big Boss"

Never run this against production with the default password.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.constants import Role, StaffStatus

Staff = get_user_model()


class Command(BaseCommand):
    help = "Create a default ADMIN staff account if it does not already exist."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="admin@swasthya.org.np")
        parser.add_argument("--password", default="admin12345")
        parser.add_argument("--name", default="System Administrator")

    def handle(self, *args, **options):
        email = options["email"].lower()
        password = options["password"]
        name = options["name"]

        if Staff.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"Staff '{email}' already exists — skipping.")
            )
            return

        user = Staff(
            email=email,
            full_name=name,
            role=Role.ADMIN,
            status=StaffStatus.ACTIVE,
            is_staff=True,
            is_superuser=True,
            must_change_password=False,
        )
        user.set_password(password)
        user.save()
        self.stdout.write(
            self.style.SUCCESS(f"Created ADMIN '{email}' with password '{password}'.")
        )
