"""
Role-based access control for SwasthyaEHR.

Views declare an `allowed_roles` list; this permission class enforces it at the
API layer, independent of anything the frontend shows or hides.
"""

from rest_framework.permissions import BasePermission


class EnforceStrictRole(BasePermission):
    """
    Allow the request only if the authenticated user's role is in the view's
    `allowed_roles`. If `allowed_roles` is empty, any authenticated user passes.
    """

    message = "Your role is not authorized to perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        allowed_roles = getattr(view, "allowed_roles", [])
        if not allowed_roles:
            return True

        return getattr(user, "role", None) in allowed_roles
