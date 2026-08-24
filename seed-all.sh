#!/usr/bin/env bash
# Seed the whole federation with demo data AFTER `docker compose up` is healthy.
#
# The National Platform auto-runs `bootstrap` on start (super admin + approved
# orgs). This script populates each hospital/lab with clinical records and pushes
# their metadata to the platform index.
set -e

echo "==> Seeding Mediciti edge service (HOSP001, variant A)..."
docker compose exec -T mediciti-hospital python manage.py seed

echo "==> Seeding Norvic edge service (HOSP002, variant B + immunizations + procedures)..."
docker compose exec -T norvic-hospital python manage.py seed



echo "==> Seeding standalone labs (Central Diagnostic + Pathlabs Nepal)..."
docker compose exec -T central-diagnostic-lab python manage.py seed
docker compose exec -T pathlabs-nepal python manage.py seed

echo ""
echo "Done. Demo credentials:"
echo "  Super Admin      superadmin / admin123"
echo "  Org Admins       HOSP001-ADM-0001 / org123  (also HOSP002, LAB001, LAB002)"
echo ""
echo "Shared demo patients (10-digit NIN): 2345678901 (Ram Bahadur Thapa),"
echo "  2345678902 (Sita Kumari Sharma), 2345678903 (Hari Prasad Koirala)"
echo "Log in as an org admin, create a doctor, then search 2345678901 to see the"
echo "unified cross-organization record."


