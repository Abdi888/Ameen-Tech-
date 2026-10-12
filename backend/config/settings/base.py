"""Settings shared by development, test, and production.

Secrets and environment-specific flags are read from the process environment.
Import this module only after the selected environment file has prepared that
environment.
"""

from __future__ import annotations

from pathlib import Path

from config.env import cors_origins, env_bool, env_list, postgresql_from_url, require_env

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = require_env("SECRET_KEY")
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "shared.database",
]

# Outermost first. Request context is outside everything so error responses
# still carry X-Request-Id. Django's session and auth apps are intentionally
# absent: web sessions are a hashed token in our own table, added with login.
MIDDLEWARE = [
    "shared.api.middleware.RequestContextMiddleware",
    "shared.api.middleware.RequestLogMiddleware",
    "shared.api.middleware.ApiEnvelopeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "shared.api.middleware.RejectTenantIdMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {"default": postgresql_from_url(require_env("DATABASE_URL"))}

# Document 00: timestamps are UTC. Business-day conversion waits for tenants.
TIME_ZONE = "UTC"
USE_TZ = True

# Public URLs in Document 05 have no trailing slash.
APPEND_SLASH = False

# Cookie flags for the session cookie Document 06 requires. The CSRF cookie
# stays readable by the future browser client so it can send the CSRF header.
# The session cookie itself is HttpOnly and is never a localStorage token.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_FAILURE_VIEW = "shared.api.errors.csrf_failure"

CORS_ALLOWED_ORIGINS = cors_origins()
CORS_ALLOW_CREDENTIALS = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Fail closed. Health opts out. CookieSessionAuthentication authenticates
# nobody until the session table and login use case exist.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "shared.api.authentication.CookieSessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "shared.api.errors.exception_handler",
    "UNAUTHENTICATED_USER": None,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": "shared.api.middleware.RequestContextLogFilter",
        },
    },
    "formatters": {
        "structured": {
            "format": (
                "%(levelname)s request_id=%(request_id)s tenant_id=%(tenant_id)s "
                "user_id=%(user_id)s endpoint=%(endpoint)s error_code=%(error_code)s "
                "%(message)s"
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_context"],
            "formatter": "structured",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
