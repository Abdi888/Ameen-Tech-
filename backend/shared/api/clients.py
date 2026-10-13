"""Client address and user agent taken from the direct connection, not forwarded headers."""

from __future__ import annotations

import ipaddress

from django.http import HttpRequest


def request_ip(request: HttpRequest) -> str | None:
    remote = str(request.META.get("REMOTE_ADDR", "")).strip()
    if not remote:
        return None
    try:
        ipaddress.ip_address(remote)
    except ValueError:
        return None
    return remote


def request_user_agent(request: HttpRequest) -> str:
    raw = request.META.get("HTTP_USER_AGENT", "")
    cleaned = "".join(char for char in raw if char.isprintable())
    return cleaned[:512]
