"""
Django settings for the SwasthyaEHR backend (config project).

Sprint 1 scaffolding: reads configuration from a git-ignored .env file,
connects to PostgreSQL, and wires up DRF, JWT auth, and CORS for the
React dev server.
"""

from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# Core security settings.
# DEBUG is safe-by-default (off); the Docker demo explicitly sets DJANGO_DEBUG=True.
DEBUG = env_bool("DJANGO_DEBUG", False)

# SECRET_KEY must come from the environment in any real deployment. Fall back to
# a throwaway key ONLY when DEBUG is on; with DEBUG off a missing key hard-fails
# rather than silently signing JWTs with a repo-committed value.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-dev-only-change-me"
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY environment variable is required when DJANGO_DEBUG is off."
        )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local
    "core",
]

# Our custom user model = hospital staff (role lives on the user for JWT).
AUTH_USER_MODEL = "core.Staff"


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
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database (PostgreSQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "swasthya"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "minorproject"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    # Shared NUHRS policy: >=8 chars, upper + lower + digit + special.
    {"NAME": "core.password_validation.NuhrsPasswordPolicyValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "static/"

# Media files (uploaded lab report PDFs — future PDF pipeline)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"



# Django REST Framework + JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core.jwt_cookies.CookieJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
}


# CORS / CSRF (React dev server + prod nginx). The SPA is served same-origin
# with the API via an /api proxy, so credentials (the httpOnly JWT cookie) must
# be allowed. A wildcard origin is not permitted together with credentials.
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:3090,http://127.0.0.1:3090")
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "http://localhost:3090,http://127.0.0.1:3090")

# httpOnly JWT cookies (see core.jwt_cookies): keep the csrftoken cookie
# readable by JS for the X-CSRFToken double-submit header; SameSite=Lax + the
# same-origin proxy block cross-site use; Secure is forced on when DEBUG is off.
#
# Cookie NAMES are app-prefixed ("swasthya_" vs "nuhrs_") because browsers scope
# cookies by host, not port — shared default names would let the two local apps
# clobber each other's CSRF token and admin session.
CSRF_COOKIE_NAME = "swasthya_csrf"
SESSION_COOKIE_NAME = "swasthya_session"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# Email configuration (development - prints to console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# ---------------------------------------------------------------------------
# NUHRS federation
# ---------------------------------------------------------------------------
# This SwasthyaEHR instance participates in the Nepal Unified Health Record
# System as an ACTIVE organization. The National Platform pushes clinical
# record metadata to its index and later fetches the real data back through the
# NID-keyed FHIR adapter (core.nuhrs_adapter), authenticated by NUHRS_API_KEY.
NUHRS_PLATFORM_URL = os.getenv("NUHRS_PLATFORM_URL", "http://localhost:8000")
NUHRS_API_KEY = os.getenv("NUHRS_API_KEY", "swastha-demo-key-0005")
NUHRS_ORG_CODE = os.getenv("NUHRS_ORG_CODE", "HOSP003")
# National-platform doctor account every SwasthyaEHR doctor is mapped to when
# launching the National Dashboard via SSO. Defaults to this org's seeded doctor.
NUHRS_DOCTOR_USERNAME = os.getenv("NUHRS_DOCTOR_USERNAME", f"{NUHRS_ORG_CODE}-DOC-0001")

NUHRS_ENABLED = env_bool("NUHRS_ENABLED", True)


