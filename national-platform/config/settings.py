"""
Django settings for the NUHRS National Platform.

The National Platform is the federated exchange. It stores ONLY metadata
(patient identity, provider registry, record index, audit logs) — never
clinical data.
"""
import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# --- Core security -----------------------------------------------------------
# DEBUG is safe-by-default (off). The Docker demo explicitly sets DEBUG=True.
DEBUG = env_bool("DEBUG", False)

# SECRET_KEY must come from the environment in any real deployment. We fall back
# to a throwaway key ONLY when DEBUG is on (local dev / demo); with DEBUG off a
# missing key hard-fails rather than silently signing JWTs with a value that is
# committed to the repo (which would let anyone forge a valid login token).
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-insecure-national-platform-key-change-me"
    else:
        raise ImproperlyConfigured(
            "SECRET_KEY environment variable is required when DEBUG is off."
        )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "corsheaders",
    # local
    "core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "national_db"),
        "USER": os.getenv("DB_USER", "nuhrs"),
        "PASSWORD": os.getenv("DB_PASSWORD", "nuhrs"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "core.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    # Shared NUHRS policy: >=8 chars, upper + lower + digit + special.
    {"NAME": "core.password_validation.NuhrsPasswordPolicyValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    # Cookie-first: authenticate from the httpOnly access_token cookie, falling
    # back to a Bearer header for service-to-service calls / tests.
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core.jwt_cookies.CookieJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

# CORS / CSRF. Credentials must be allowed so the browser will attach the
# httpOnly JWT cookie (Phase 3); that in turn forbids the wildcard origin, so we
# use an explicit allow-list (overridable via env). CORS_ALLOW_ALL_ORIGINS is
# honored only as an explicit, DEBUG-only escape hatch.
CORS_ALLOW_ALL_ORIGINS = DEBUG and env_bool("CORS_ALLOW_ALL_ORIGINS", False)
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)

# --- Session / CSRF cookies (httpOnly JWT cookies) ---------------------------
# The JWTs live in httpOnly cookies (see core.jwt_cookies); the csrftoken cookie
# must stay readable by JS so the SPA can echo it back in the X-CSRFToken header
# (double-submit). SameSite=Lax + the same-origin /api proxy block cross-site
# use; Secure is forced on whenever DEBUG is off.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# Trust store for organization api_keys is the Organization table itself.
NID_SYSTEM = "https://nid.gov.np"

# Base URL of the NUHRS National Dashboard (React portal). Used to build the
# SSO redirect URL returned by /api/auth/sso-exchange/.
NUHRS_PORTAL_URL = os.getenv("NUHRS_PORTAL_URL", "http://localhost:3000")


