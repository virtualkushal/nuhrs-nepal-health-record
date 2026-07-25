"""
Bootstrap the National Platform:
- create a super admin
- pre-register + approve the 2 hospitals and 2 labs with fixed api_keys
  so the whole federation works out-of-the-box for the demo.

Fixed api_keys let docker-compose wire each org's key via env without a manual
approval step. In a real deployment approval is manual (and demonstrated in UI).
"""
from django.core.management.base import BaseCommand

from core.models import Organization, User

# Fixed demo credentials (shared with each org service via docker-compose env)
SEED_ORGS = [
    {
        "organization_name": "Nepal Mediciti Hospital",
        "organization_type": Organization.OrgType.HOSPITAL,
        "organization_code": "HOSP001",
        "license_number": "NMC-HOSP-001",
        "api_base_url": "http://hospital-a:8001/fhir",
        "api_key": "mediciti-demo-key-0001",
        "district": "Lalitpur", "province": "Bagmati",
        "contact_email": "admin@mediciti.example", "contact_phone": "01-5555001",
    },
    {
        "organization_name": "Norvic International Hospital",
        "organization_type": Organization.OrgType.HOSPITAL,
        "organization_code": "HOSP002",
        "license_number": "NMC-HOSP-002",
        "api_base_url": "http://hospital-b:8002/fhir",
        "api_key": "norvic-demo-key-0002",
        "district": "Kathmandu", "province": "Bagmati",
        "contact_email": "admin@norvic.example", "contact_phone": "01-5555002",
    },
    {
        "organization_name": "Central Diagnostic Laboratory",
        "organization_type": Organization.OrgType.LAB,
        "organization_code": "LAB001",
        "license_number": "NPL-LAB-001",
        "api_base_url": "http://lab-a:9001/fhir",
        "api_key": "central-demo-key-0003",
        "district": "Kathmandu", "province": "Bagmati",
        "contact_email": "admin@centrallab.example", "contact_phone": "01-5555003",
    },
    {
        "organization_name": "Pathlabs Nepal",
        "organization_type": Organization.OrgType.LAB,
        "organization_code": "LAB002",
        "license_number": "NPL-LAB-002",
        "api_base_url": "http://lab-b:9002/fhir",
        "api_key": "pathlabs-demo-key-0004",
        "district": "Lalitpur", "province": "Bagmati",
        "contact_email": "admin@pathlabs.example", "contact_phone": "01-5555004",
    },
]


class Command(BaseCommand):
    help = "Bootstrap super admin and seed/approve the demo organizations."

    def handle(self, *args, **options):
        # super admin
        if not User.objects.filter(username="superadmin").exists():
            User.objects.create_superuser(username="superadmin", password="admin123")
            self.stdout.write(self.style.SUCCESS("Created superadmin / admin123"))
        else:
            self.stdout.write("superadmin already exists")

        # organizations (pre-approved for demo)
        for data in SEED_ORGS:
            org, created = Organization.objects.update_or_create(
                organization_code=data["organization_code"],
                defaults={**data, "status": Organization.Status.ACTIVE},
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{verb} {org.organization_name} [{org.organization_code}]"))

            # org admin account
            admin_username = f"{org.organization_code}-ADM-0001"
            if not User.objects.filter(username=admin_username).exists():
                User.objects.create_user(
                    username=admin_username,
                    password="org123",
                    full_name=f"{org.organization_name} Admin",
                    email=org.contact_email,
                    role=User.Role.ORGANIZATION_ADMIN,
                    organization=org,
                    must_change_password=False,
                )
                self.stdout.write(f"  admin: {admin_username} / org123")

        self.stdout.write(self.style.SUCCESS("Bootstrap complete."))
