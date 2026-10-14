"""Settings shared by development, test, and production.

Secrets and environment-specific flags are read from the process environment.
Import this module only after the selected environment file has prepared that
environment.
"""

from __future__ import annotations

from pathlib import Path

from config.env import (
    cors_origins,
    csrf_trusted_origins,
    env_bool,
    env_list,
    postgresql_from_url,
    require_env,
)

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = require_env("SECRET_KEY")
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "shared.database",
    "modules.tenants",
    "modules.identity",
    "modules.access",
    "modules.audit",
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
    "shared.api.middleware.EnsureCsrfCookieMiddleware",
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
# stays readable by the browser client so it can send the CSRF header.
# The session cookie itself is HttpOnly and is never a localStorage token.
SESSION_COOKIE_NAME = "ameen_session"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_PATH = "/"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
# Document 06 starting values. Production sets Secure on the cookie.
SESSION_IDLE_SECONDS = 8 * 60 * 60
SESSION_ABSOLUTE_SECONDS = 30 * 24 * 60 * 60
# Document 06 asks for length rather than composition rules and does not set a number.
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
PASSWORD_RESET_TTL_SECONDS = 60 * 60
LOGIN_MAX_FAILURES = 5
LOGIN_FAILURE_WINDOW_SECONDS = 15 * 60
LOGIN_PROGRESSIVE_DELAY_SECONDS = 0.25
CSRF_FAILURE_VIEW = "shared.api.errors.csrf_failure"

CORS_ALLOWED_ORIGINS = cors_origins()
CORS_ALLOW_CREDENTIALS = True
# Cookie POSTs from the Vite SPA (different origin in local development) need
# an explicit CSRF trusted origin. Defaults to the CORS allowlist when
# CSRF_TRUSTED_ORIGINS is unset; set that env var to a narrower list in
# production if CORS must stay wider than CSRF. Never use *.
CSRF_TRUSTED_ORIGINS = csrf_trusted_origins(CORS_ALLOWED_ORIGINS)

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Fail closed. Health and login opt out. Protected views declare a Document 07 key.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "modules.identity.api.authentication.CookieSessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "modules.access.api.permissions.DenyByDefault",
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
