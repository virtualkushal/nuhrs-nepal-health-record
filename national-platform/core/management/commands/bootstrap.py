"""
Bootstrap the National Platform:
- create a super admin
- pre-register + approve the 2 hospitals and 2 labs with fixed api_keys
  so the whole federation works out-of-the-box for the demo.

Fixed api_keys let docker-compose wire each org's key via env without a manual
approval step. In a real deployment approval is manual (and demonstrated in UI).
"""
from django.core.management.base import BaseCommand

from core.models import Organization, PatientIdentity, User


# Fixed demo credentials (shared with each org service via docker-compose env)
SEED_ORGS = [
    {
        "organization_name": "Nepal Mediciti Hospital",
        "organization_type": Organization.OrgType.HOSPITAL,
        "organization_code": "HOSP001",
        "license_number": "NMC-HOSP-001",
        "api_base_url": "http://mediciti-hospital:8003/fhir",
        "api_key": "mediciti-demo-key-0001",
        "district": "Lalitpur", "province": "Bagmati",
        "contact_email": "admin@mediciti.example", "contact_phone": "01-5555001",
    },
    {
        "organization_name": "Norvic International Hospital",
        "organization_type": Organization.OrgType.HOSPITAL,
        "organization_code": "HOSP002",
        "license_number": "NMC-HOSP-002",
        "api_base_url": "http://norvic-hospital:8004/fhir",
        "api_key": "norvic-demo-key-0002",
        "district": "Kathmandu", "province": "Bagmati",
        "contact_email": "admin@norvic.example", "contact_phone": "01-5555002",
    },
    {
        "organization_name": "SwasthyaEHR Hospital",
        "organization_type": Organization.OrgType.HOSPITAL,
        "organization_code": "HOSP003",
        "license_number": "NMC-HOSP-003",
        "api_base_url": "http://swastha-backend:8090/fhir",
        "api_key": "swastha-demo-key-0005",
        "district": "Kathmandu", "province": "Bagmati",
        "contact_email": "admin@swastha.example", "contact_phone": "01-5555005",
    },

    {
        "organization_name": "Central Diagnostic Laboratory",
        "organization_type": Organization.OrgType.LAB,
        "organization_code": "LAB001",
        "license_number": "NPL-LAB-001",
        "api_base_url": "http://central-diagnostic-lab:9001/fhir",
        "api_key": "central-demo-key-0003",
        "district": "Kathmandu", "province": "Bagmati",
        "contact_email": "admin@centrallab.example", "contact_phone": "01-5555003",
    },
    {
        "organization_name": "Pathlabs Nepal",
        "organization_type": Organization.OrgType.LAB,
        "organization_code": "LAB002",
        "license_number": "NPL-LAB-002",
        "api_base_url": "http://pathlabs-nepal:9002/fhir",
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

        # -- demo users for a ready-to-use demo ---------------------------------
        # Canonical demographics per NID — MUST match hospital/lab/swastha seeds.
        demo_patients = [
            {
                "nid": "12345678901", "full_name": "Ram Bahadur Thapa",
                "date_of_birth": "1970-05-12", "gender": "MALE", "phone": "9841000001",
                "email": "ram@demo.np",
            },
            {
                "nid": "12345678902", "full_name": "Sita Kumari Sharma",
                "date_of_birth": "1988-11-23", "gender": "FEMALE", "phone": "9803000002",
                "email": "sita@demo.np",
            },
            {
                "nid": "12345678903", "full_name": "Hari Prasad Koirala",
                "date_of_birth": "1979-02-03", "gender": "MALE", "phone": "9841000003",
                "email": "hari@demo.np",
            },
        ]
        for p in demo_patients:
            identity, created = PatientIdentity.objects.get_or_create(
                nid=p["nid"],
                defaults={
                    "full_name": p["full_name"],
                    "date_of_birth": p["date_of_birth"],
                    "gender": p["gender"],
                    "phone": p["phone"],
                    "email": p["email"],
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  identity: {p['nid']} {p['full_name']}"))

        # Demo doctor per organization (ready login, no temp password dance)
        for data in SEED_ORGS:
            org = Organization.objects.get(organization_code=data["organization_code"])
            doctor_username = f"{org.organization_code}-DOC-0001"
            if not User.objects.filter(username=doctor_username).exists():
                User.objects.create_user(
                    username=doctor_username,
                    password="doctor123",
                    full_name=f"{org.organization_name} Demo Doctor",
                    email=org.contact_email,
                    role=User.Role.DOCTOR,
                    organization=org,
                    must_change_password=False,
                )
                self.stdout.write(f"  doctor: {doctor_username} / doctor123")

        # Pre-activated demo patient on the national platform
        # (username = NID, password patient123) so the portal login works
        # immediately without the activation form.
        ram = PatientIdentity.objects.get(nid="12345678901")
        if not User.objects.filter(username="12345678901").exists():
            User.objects.create_user(
                username="12345678901",
                password="patient123",
                full_name=ram.full_name,
                email=ram.email,
                phone=ram.phone,
                role=User.Role.PATIENT,
                patient_identity=ram,
                must_change_password=False,
            )
            self.stdout.write("  patient: 12345678901 / patient123")

        self.stdout.write(self.style.SUCCESS("Bootstrap complete."))


