"""Production settings. Missing or placeholder secrets fail at import."""

from __future__ import annotations

from config.env import assert_production_settings, env_bool, env_list, require_env

assert_production_settings(
    debug=env_bool("DEBUG", False),
    secret_key=require_env("SECRET_KEY"),
    allowed_hosts=env_list("ALLOWED_HOSTS"),
)

from .base import *  # noqa: E402,F403

DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
