"""
Focused tests for RoutingEngine.fetch_all() concurrency behavior.

Pure unit tests using mocks — no database queries are executed.
"""
import os
import time
import unittest
from unittest import mock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from core import services
from core.models import AuditLog, Organization, RecordIndex
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
        bundle = engine.fetch_all("11112222333")
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
            "11112222333",
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
            bundle = engine.fetch_all("11112222333")
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
            "11112222333",
            AuditLog.Action.FETCH_ALL,
            ["Hospital A", "Hospital B", "Hospital C"],
        )


if __name__ == "__main__":
    unittest.main()