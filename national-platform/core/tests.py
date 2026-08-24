"""
Focused tests for RoutingEngine.fetch_all() concurrency behavior.

Pure unit tests using mocks — no database queries are executed.
Plus DB-backed tests for the org-admin privilege model (audit scoping, staff
deactivation, scoped password resets, facility edits, facility analytics).
"""
import os
import time
import unittest
from unittest import mock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from rest_framework.test import APITestCase

from core import services
from core.models import AuditLog, Organization, PatientIdentity, RecordIndex, User
from core.services import RoutingEngine


class _Org:
    def __init__(self, org_id, name):
        self.id = org_id
        self.organization_name = name
        self.api_base_url = f"https://org-{org_id}.example/fhir"
        self.api_key = "test-key"


class _Idx:
    def __init__(self, org_id):
        self.organization_id = org_id


class _FakeQS(list):
    def order_by(self, *args, **kwargs):
        return self

    def select_related(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self


def _run_fetch_all(orgs, responses):
    """Run engine.fetch_all with fully mocked ORM + outbound requests."""
    engine = RoutingEngine(actor_user=None, ip_address="127.0.0.1")
    engine._request_everything = mock.Mock(side_effect=responses)
    engine._audit = mock.Mock()
    with mock.patch.object(
        services.RecordIndex, "objects",
        mock.Mock(filter=mock.Mock(return_value=_FakeQS(_Idx(o.id) for o in orgs))),
    ), mock.patch.object(
        services.Organization, "objects",
        mock.Mock(filter=mock.Mock(return_value=_FakeQS(orgs))),
    ):
        bundle = engine.fetch_all("1112222333")
    return engine, bundle


class FetchAllOrderingTests(unittest.TestCase):
    def test_results_in_original_org_order(self):
        orgs = [_Org(1, "Hospital A"), _Org(2, "Hospital B"), _Org(3, "Hospital C")]
        responses = [
            [{"resourceType": "Patient", "id": "a1"}],
            [{"resourceType": "Observation", "id": "b1"}],
            [{"resourceType": "Condition", "id": "c1"}],
        ]
        engine, bundle = _run_fetch_all(orgs, responses)

        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "collection")
        self.assertEqual(bundle["total"], 3)
        self.assertEqual(
            [e["resource"]["id"] for e in bundle["entry"]], ["a1", "b1", "c1"]
        )
        engine._audit.assert_called_once_with(
            "1112222333",
            AuditLog.Action.FETCH_ALL,
            ["Hospital A", "Hospital B", "Hospital C"],
        )


class FetchAllConcurrencyTests(unittest.TestCase):
    def test_requests_run_concurrently_not_sequentially(self):
        orgs = [_Org(1, "Hospital A"), _Org(2, "Hospital B"), _Org(3, "Hospital C")]

        def slow_c(*args):
            time.sleep(1.0)
            return [{"resourceType": "Patient", "id": "a1"}]

        def fast_a(*args):
            time.sleep(0.3)
            return [{"resourceType": "Patient", "id": "b1"}]

        def mid_b(*args):
            time.sleep(0.6)
            return [{"resourceType": "Patient", "id": "c1"}]

        engine = RoutingEngine(actor_user=None, ip_address="127.0.0.1")
        engine._audit = mock.Mock()
        call_order = {"n": 0}

        def dispatch(*args):
            call_order["n"] += 1
            return [slow_c, fast_a, mid_b][call_order["n"] - 1](*args)

        engine._request_everything = mock.Mock(side_effect=dispatch)

        orgs = [_Org(1, "Hospital A"), _Org(2, "Hospital B"), _Org(3, "Hospital C")]
        with mock.patch.object(
            services.RecordIndex, "objects",
            mock.Mock(filter=mock.Mock(return_value=_FakeQS(_Idx(o.id) for o in orgs))),
        ), mock.patch.object(
            services.Organization, "objects",
            mock.Mock(filter=mock.Mock(return_value=_FakeQS(orgs))),
        ):
            start = time.monotonic()
            bundle = engine.fetch_all("1112222333")
            elapsed = time.monotonic() - start

        serial_total = 1.9
        self.assertLess(elapsed, serial_total - 0.4,
                        "wall time should be well below the serial sum")
        self.assertLessEqual(elapsed, 1.0 + 0.75,
                             "wall time should be close to the slowest request")
        self.assertEqual(
            [e["resource"]["id"] for e in bundle["entry"]], ["a1", "b1", "c1"]
        )


class FetchAllFailureTests(unittest.TestCase):
    def test_failed_org_yields_operation_outcome_and_request_succeeds(self):
        orgs = [_Org(1, "Hospital A"), _Org(2, "Hospital B"), _Org(3, "Hospital C")]

        responses = [
            [{"resourceType": "Patient", "id": "a1"}],
            RuntimeError("adapter exploded"),
            [{"resourceType": "Condition", "id": "c1"}],
        ]
        engine, bundle = _run_fetch_all(orgs, responses)

        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["total"], 3)
        entries = [e["resource"] for e in bundle["entry"]]
        self.assertEqual(entries[0]["id"], "a1")
        self.assertEqual(entries[1]["resourceType"], "OperationOutcome")
        self.assertEqual(entries[1]["_source"], "Hospital B")
        self.assertEqual(entries[2]["id"], "c1")
        engine._audit.assert_called_once_with(
            "1112222333",
            AuditLog.Action.FETCH_ALL,
            ["Hospital A", "Hospital B", "Hospital C"],
        )


# ---------------------------------------------------------------------------
# Org-admin privilege model
# ---------------------------------------------------------------------------
def _make_org(code, name):
    return Organization.objects.create(
        organization_code=code,
        organization_name=name,
        organization_type=Organization.OrgType.HOSPITAL,
        license_number=f"LIC-{code}",
        api_base_url=f"http://{code.lower()}.example/fhir",
        api_key=f"{code.lower()}-key",
        contact_email=f"contact@{code.lower()}.np",
        contact_phone="01-5550000",
        status=Organization.Status.ACTIVE,
    )


class OrgAdminPrivilegeTests(APITestCase):
    """Every org-admin power is enforced server-side to own-org scope only."""

    def setUp(self):
        self.org_a = _make_org("HSPA", "Hospital A")
        self.org_b = _make_org("HSPB", "Hospital B")
        self.admin_a = User.objects.create_user(
            username="HSPA-ADM-0001", login_name="admin", password="OrgPass!123",
            full_name="Admin A", role=User.Role.ORGANIZATION_ADMIN, organization=self.org_a,
        )
        self.admin_b = User.objects.create_user(
            username="HSPB-ADM-0001", login_name="admin", password="OrgPass!123",
            full_name="Admin B", role=User.Role.ORGANIZATION_ADMIN, organization=self.org_b,
        )
        self.doc_a = User.objects.create_user(
            username="HSPA-DOC-0001", login_name="doctor", password="DocPass!123",
            full_name="Doctor A", role=User.Role.DOCTOR, organization=self.org_a,
        )
        self.tech_a = User.objects.create_user(
            username="HSPA-TEC-0001", login_name="tech", password="TecPass!123",
            full_name="Tech A", role=User.Role.LAB_TECHNICIAN, organization=self.org_a, is_active=False,
        )
        self.doc_b = User.objects.create_user(
            username="HSPB-DOC-0001", login_name="doctor", password="DocPass!123",
            full_name="Doctor B", role=User.Role.DOCTOR, organization=self.org_b,
        )
        self.superuser = User.objects.create_superuser(username="root", password="RootPass!123")
        self.patient = User.objects.create_user(
            username="2345678901", password="PatPass!123",
            full_name="Patient P", role=User.Role.PATIENT,
        )

    def _audit_row(self, org, action=AuditLog.Action.FETCH_ALL):
        return AuditLog.objects.create(
            actor_user=self.doc_a if org == self.org_a else self.doc_b,
            actor_org=org, nid="2345678901", action=action,
        )

    # -- 1. audit log scoping -------------------------------------------------
    def test_patient_cannot_read_audit_log(self):
        self.client.force_authenticate(self.patient)
        res = self.client.get("/api/audit/")
        self.assertEqual(res.status_code, 403)

    def test_doctor_cannot_read_audit_log(self):
        self.client.force_authenticate(self.doc_a)
        res = self.client.get("/api/audit/")
        self.assertEqual(res.status_code, 403)

    def test_org_admin_sees_only_own_facility_rows(self):
        self._audit_row(self.org_a)
        self._audit_row(self.org_a)
        self._audit_row(self.org_b)
        self.client.force_authenticate(self.admin_a)
        res = self.client.get("/api/audit/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)
        self.assertTrue(all(r["actor_org_name"] == "Hospital A" for r in res.data))

    def test_super_admin_sees_full_audit_log(self):
        self._audit_row(self.org_a)
        self._audit_row(self.org_b)
        self.client.force_authenticate(self.superuser)
        res = self.client.get("/api/audit/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)

    # -- 2. staff deactivation ------------------------------------------------
    def test_deactivated_doctor_cannot_log_in_then_reactivation_restores(self):
        self.client.force_authenticate(self.admin_a)
        # deactivate Doctor A (currently active)
        res = self.client.patch(f"/api/staff/{self.doc_a.id}/", {"is_active": False}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data["is_active"])
        # login must now fail with a clear rejection
        login = self.client.post("/api/auth/login/", {
            "scope": "STAFF", "org_code": "HSPA",
            "login_name": "doctor", "password": "DocPass!123",
        }, format="json")
        self.assertEqual(login.status_code, 401)
        # reactivate -> login works again
        res = self.client.patch(f"/api/staff/{self.doc_a.id}/", {"is_active": True}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["is_active"])
        login = self.client.post("/api/auth/login/", {
            "scope": "STAFF", "org_code": "HSPA",
            "login_name": "doctor", "password": "DocPass!123",
        }, format="json")
        self.assertEqual(login.status_code, 200)

    def test_deactivation_is_audited(self):
        self.client.force_authenticate(self.admin_a)
        self.client.patch(f"/api/staff/{self.doc_a.id}/", {"is_active": False}, format="json")
        self.assertTrue(
            AuditLog.objects.filter(
                actor_org=self.org_a, action=AuditLog.Action.STAFF_DEACTIVATE,
                target_orgs=self.doc_a.username,
            ).exists()
        )

    def test_org_admin_cannot_touch_other_facility_staff(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.patch(f"/api/staff/{self.doc_b.id}/", {"is_active": False}, format="json")
        self.assertEqual(res.status_code, 404)
        self.doc_b.refresh_from_db()
        self.assertTrue(self.doc_b.is_active)

    def test_noop_state_change_is_rejected(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.patch(f"/api/staff/{self.doc_a.id}/", {"is_active": True}, format="json")
        self.assertEqual(res.status_code, 400)

    # -- 3. scoped password reset ----------------------------------------------
    def test_org_admin_resets_own_staff_password(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.post(f"/api/users/{self.doc_a.id}/reset-password/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("temporary_password", res.data)
        self.doc_a.refresh_from_db()
        self.assertTrue(self.doc_a.must_change_password)

    def test_org_admin_cannot_reset_cross_facility_or_admins(self):
        self.client.force_authenticate(self.admin_a)
        self.assertEqual(self.client.post(f"/api/users/{self.doc_b.id}/reset-password/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/users/{self.admin_b.id}/reset-password/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/users/{self.admin_a.id}/reset-password/").status_code, 404)

    def test_super_admin_still_resets_anyone(self):
        self.client.force_authenticate(self.superuser)
        res = self.client.post(f"/api/users/{self.doc_b.id}/reset-password/")
        self.assertEqual(res.status_code, 200)

    def test_password_reset_is_audited(self):
        self.client.force_authenticate(self.admin_a)
        self.client.post(f"/api/users/{self.doc_a.id}/reset-password/")
        self.assertTrue(
            AuditLog.objects.filter(
                actor_org=self.org_a, action=AuditLog.Action.PASSWORD_RESET,
            ).exists()
        )

    # -- 4. profile + facility edits -------------------------------------------
    def test_org_admin_edits_own_staff_profile(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.patch(
            f"/api/staff/{self.doc_a.id}/",
            {"full_name": "Dr. Updated A", "email": "updated@a.np"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.doc_a.refresh_from_db()
        self.assertEqual(self.doc_a.full_name, "Dr. Updated A")
        self.assertEqual(self.doc_a.email, "updated@a.np")

    def test_staff_profile_email_validated(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.patch(f"/api/staff/{self.doc_a.id}/", {"email": "not-an-email"}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_facility_get_and_patch_contact_fields(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.get("/api/facility/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["organization_code"], "HSPA")

        res = self.client.patch(
            "/api/facility/",
            {"contact_phone": "9841234567", "contact_email": "new@a.np"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.org_a.refresh_from_db()
        self.assertEqual(self.org_a.contact_phone, "9841234567")

    def test_facility_patch_rejects_protected_fields_and_bad_input(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.patch("/api/facility/", {"status": "SUSPENDED"}, format="json")
        self.assertEqual(res.status_code, 400)
        res = self.client.patch("/api/facility/", {"contact_phone": "12345"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.org_a.refresh_from_db()
        self.assertEqual(self.org_a.status, Organization.Status.ACTIVE)

    def test_doctor_cannot_edit_facility(self):
        self.client.force_authenticate(self.doc_a)
        self.assertEqual(self.client.get("/api/facility/").status_code, 403)
        self.assertEqual(self.client.patch("/api/facility/", {"contact_phone": "9841234567"}, format="json").status_code, 403)

    # -- 5. facility analytics ---------------------------------------------------
    def test_facility_analytics_scoped_to_own_org(self):
        patient = PatientIdentity.objects.create(
            nid="2345678901", full_name="P", date_of_birth="1990-01-01",
        )
        RecordIndex.objects.create(
            organization=self.org_a, resource_type=RecordIndex.ResourceType.CONDITION,
            local_record_id="r-a-1", service_date="2026-01-01", patient=patient,
        )
        RecordIndex.objects.create(
            organization=self.org_b, resource_type=RecordIndex.ResourceType.CONDITION,
            local_record_id="r-b-1", service_date="2026-01-02", patient=patient,
        )
        self._audit_row(self.org_a)  # fetch by hospital-A staff

        self.client.force_authenticate(self.admin_a)
        res = self.client.get("/api/analytics/facility/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["records_indexed"], 1)
        self.assertEqual(res.data["fetches_by_my_staff"], 1)
        self.assertEqual(res.data["by_resource_type"][0]["resource_type"], "Condition")

    def test_doctor_blocked_from_facility_analytics(self):
        self.client.force_authenticate(self.doc_a)
        self.assertEqual(self.client.get("/api/analytics/facility/").status_code, 403)


if __name__ == "__main__":
    unittest.main()