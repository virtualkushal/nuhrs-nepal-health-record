"""Reusable DRF permission classes for the National Platform.

These centralize the role checks that were previously inlined per view
(see ``AnalyticsSummaryView``) so the federated exchange and oversight
endpoints enforce access control consistently instead of relying on
``IsAuthenticated`` alone.
"""
from rest_framework.permissions import BasePermission

from .models import User


class IsMinistryOrSuperAdmin(BasePermission):
    """Oversight endpoints (audit log, analytics): Ministry + Super Admin only."""

    message = "Only Ministry or Super Admin may access this resource."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and user.role in (User.Role.SUPER_ADMIN, User.Role.MINISTRY)
        )


class IsExchangeUser(BasePermission):
    """Federated exchange (patient lookup / index / fetch by NID).

    Allows any authenticated role EXCEPT a patient. Patients must use their
    own self-scoped endpoints (``/patient/bundle/``, ``/patient/records/``),
    which derive the NID from ``request.user`` rather than from the URL, so
    they can never read another person's records.
    """

    message = "Patients cannot look up other patients; use your own records."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and user.role != User.Role.PATIENT
        )
