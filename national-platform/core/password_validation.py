"""
Django-native password policy shared across NUHRS.

One rule everywhere users are created:
  * at least 8 characters
  * at least one uppercase letter
  * at least one lowercase letter
  * at least one digit
  * at least one special (non-alphanumeric) character

Registered in settings.AUTH_PASSWORD_VALIDATORS so `validate_password()` — and
therefore every code path that calls it — enforces the same policy.
"""
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

# Kept identical to core.validators.PASSWORD_RE and the frontend mirror.
PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


class NuhrsPasswordPolicyValidator:
    """Enforce the shared NUHRS password complexity policy."""

    message = _(
        "Password must be at least 8 characters and include an uppercase letter, "
        "a lowercase letter, a digit and a special character."
    )
    code = "password_too_weak"

    def validate(self, password, user=None):
        if not PASSWORD_RE.match(password or ""):
            raise ValidationError(self.message, code=self.code)

    def get_help_text(self):
        return self.message
