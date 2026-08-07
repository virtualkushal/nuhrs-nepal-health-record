"""
Django settings for Pathlabs Nepal.

This is a STANDALONE lab service in the NUHRS federation. It owns its own
database (MySQL, variant B schema — different column names than Central
Diagnostic) and exposes read-only FHIR DiagnosticReport resources that the
National Platform fetches from. Self-contained, hard-wired to variant B.

Running on MySQL (not PostgreSQL) demonstrates that the FHIR adapter is
storage-engine agnostic: the platform fetches identical HL7 FHIR R4 whether the
lab stores its data in Postgres (Central Diagnostic) or MySQL (Pathlabs Nepal).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-pathlabs-key")
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
    "lab",
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
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "lab_b_db"),
        "USER": os.getenv("DB_USER", "nuhrs"),
        "PASSWORD": os.getenv("DB_PASSWORD", "nuhrs"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "3306"),
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
ORG_NAME = os.getenv("ORG_NAME", "Pathlabs Nepal")
ORG_CODE = os.getenv("ORG_CODE", "LAB002")
PLATFORM_URL = os.getenv("PLATFORM_URL", "http://localhost:8000")
ORG_API_KEY = os.getenv("ORG_API_KEY", "pathlabs-demo-key-0004")
NID_SYSTEM = "https://nid.gov.np"
