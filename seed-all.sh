#!/usr/bin/env bash
# Seed the whole federation with demo data AFTER `docker compose up` is healthy.
#
# The National Platform auto-runs `bootstrap` on start (super admin + approved
# orgs). This script populates each hospital/lab with clinical records and pushes
# their metadata to the platform index.
set -e

echo "==> Seeding hospitals..."
docker compose exec -T hospital-a python manage.py seed
docker compose exec -T hospital-b python manage.py seed

echo "==> Seeding standalone Mediciti edge service..."
docker compose exec -T mediciti-hospital python manage.py seed


echo "==> Seeding labs..."
docker compose exec -T lab-a python manage.py seed
docker compose exec -T lab-b python manage.py seed

echo ""
echo "Done. Demo credentials:"
echo "  Super Admin      superadmin / admin123"
echo "  Org Admins       HOSP001-ADM-0001 / org123  (also HOSP002, LAB001, LAB002)"
echo ""
echo "Shared demo patients (11-digit NIN): 12345678901 (Ram Bahadur Thapa),"
echo "  12345678902 (Sita Kumari Sharma), 12345678903 (Hari Prasad Koirala)"
echo "Log in as an org admin, create a doctor, then search 12345678901 to see the"
echo "unified cross-organization record."


