"""
Django settings for the Norvic International Hospital service.

This is a STANDALONE hospital edge system in the NUHRS federation. It owns its
own database (schema shaped like Norvic's real HMIS — "variant B") and exposes a
read-only FHIR API that the National Platform fetches from. It knows nothing
about any other hospital — only its own data and how to map it to FHIR.

Norvic is deliberately DIFFERENT from Nepal Mediciti in two ways:
  1. Its database uses different column names for the same clinical facts
     (first_name/last_name, physician, condition_desc, measurement_name ...).
  2. It offers services Mediciti does not: Immunization (vaccination records)
     and Procedure (surgical/cardiac procedures) — reflecting that no two real
     hospitals offer an identical set of services.

Configuration comes from environment variables:
  - ORG_NAME, ORG_CODE, PLATFORM_URL, ORG_API_KEY
  - DB_NAME etc.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-norvic-key")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "clinical",
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
        "NAME": os.getenv("DB_NAME", "norvic_db"),
        "USER": os.getenv("DB_USER", "nuhrs"),
        "PASSWORD": os.getenv("DB_PASSWORD", "nuhrs"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
}

CORS_ALLOW_ALL_ORIGINS = True

# ---- NUHRS org-specific configuration ----
ORG_NAME = os.getenv("ORG_NAME", "Norvic International Hospital")
ORG_CODE = os.getenv("ORG_CODE", "HOSP002")
PLATFORM_URL = os.getenv("PLATFORM_URL", "http://localhost:8000")
ORG_API_KEY = os.getenv("ORG_API_KEY", "norvic-demo-key-0002")
NID_SYSTEM = "https://nid.gov.np"
