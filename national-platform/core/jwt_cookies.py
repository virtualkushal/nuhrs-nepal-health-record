"""
httpOnly-cookie JWT transport for the National Platform.

simplejwt 5.3.1 ships no cookie transport, so this small module adds one:

  * Access + refresh JWTs live in httpOnly cookies (``nuhrs_access_token`` /
    ``nuhrs_refresh_token``) instead of the JSON response body, so client-side
    JavaScript — and therefore an XSS payload — can never read them.
  * ``CookieJWTAuthentication`` authenticates from the access cookie when no
    ``Authorization: Bearer`` header is present, and enforces CSRF on unsafe
    methods for those cookie-authenticated requests (double-submit token).
  * SameSite=Lax cookies plus a same-origin ``/api`` proxy are the primary CSRF
    defense; the CSRF token is defense-in-depth. ``Secure`` is set automatically
    whenever DEBUG is off (i.e. everywhere but the local demo).

Login / SSO-verify / refresh set the cookies; logout clears them.
"""
from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication

# Cookie names are prefixed per app ("nuhrs_" vs "swasthya_"). Browsers scope
# cookies by HOST only — NOT by port — so when both apps run on localhost at
# the same time, generic names like "access_token" would let whichever backend
# responded last silently overwrite the other's session.
ACCESS_COOKIE = "nuhrs_access_token"
REFRESH_COOKIE = "nuhrs_refresh_token"

# Methods that never mutate state and therefore never require a CSRF token.
SAFE_METHODS = ("GET", "HEAD", "OPTIONS", "TRACE")


def _lifetime_seconds(key, fallback):
    delta = getattr(settings, "SIMPLE_JWT", {}).get(key)
    return int(delta.total_seconds()) if delta else fallback


def _cookie_flags():
    # Secure whenever we're not in local/demo DEBUG mode. SameSite=Lax is safe
    # because each SPA is served same-origin with its API (via an /api proxy),
    # so the cookie rides along on same-site requests but not cross-site POSTs.
    return {
        "httponly": True,
        "secure": not settings.DEBUG,
        "samesite": "Lax",
        "path": "/",
    }


def set_auth_cookies(response, access=None, refresh=None):
    """Attach the access (and optionally refresh) JWT as httpOnly cookies."""
    flags = _cookie_flags()
    if access is not None:
        response.set_cookie(
            ACCESS_COOKIE,
            access,
            max_age=_lifetime_seconds("ACCESS_TOKEN_LIFETIME", 8 * 3600),
            **flags,
        )
    if refresh is not None:
        response.set_cookie(
            REFRESH_COOKIE,
            refresh,
            max_age=_lifetime_seconds("REFRESH_TOKEN_LIFETIME", 24 * 3600),
            **flags,
        )
    return response


def clear_auth_cookies(response):
    """Remove both JWT cookies (logout)."""
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")
    return response


def enforce_csrf(request):
    """Run Django's CSRF check for cookie-authenticated unsafe requests.

    Safe methods are exempt. On failure raises PermissionDenied (HTTP 403),
    matching how DRF surfaces authentication-layer CSRF failures.
    """
    if request.method in SAFE_METHODS:
        return
    check = CSRFCheck(lambda req: None)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate from the ``nuhrs_access_token`` cookie.

    A real ``Authorization: Bearer`` header still wins (service-to-service calls
    and tests keep working) and is exempt from CSRF, because a header is not an
    ambient credential a malicious site can force the browser to send. Only the
    cookie path — the ambient credential — enforces CSRF on unsafe methods.
    """

    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None
            validated = self.get_validated_token(raw_token)
            return self.get_user(validated), validated

        raw_token = request.COOKIES.get(ACCESS_COOKIE)
        if not raw_token:
            return None
        validated = self.get_validated_token(raw_token)
        enforce_csrf(request)
        return self.get_user(validated), validated
