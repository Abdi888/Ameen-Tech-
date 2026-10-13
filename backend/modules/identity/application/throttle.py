from __future__ import annotations

import time
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.utils import timezone

from modules.identity.models import LoginAttempt


def serialize_attempts(*, email: str, ip: str | None, purpose: str) -> None:
    """Hold a transaction lock so concurrent attempts cannot pass the same count.

    Call inside ``transaction.atomic``. The lock releases when that transaction ends.
    """
    key = f"{purpose}:{email}:{ip or '-'}"
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", [key])


def locked(*, email: str, ip: str | None, purpose: str) -> bool:
    since = timezone.now() - timedelta(seconds=settings.LOGIN_FAILURE_WINDOW_SECONDS)
    failures = LoginAttempt.objects.filter(
        email=email,
        ip=ip,
        purpose=purpose,
        succeeded=False,
        attempted_at__gte=since,
    ).count()
    return failures >= settings.LOGIN_MAX_FAILURES


def pause(*, email: str, ip: str | None, purpose: str) -> None:
    delay = float(settings.LOGIN_PROGRESSIVE_DELAY_SECONDS)
    if delay <= 0:
        return
    since = timezone.now() - timedelta(seconds=settings.LOGIN_FAILURE_WINDOW_SECONDS)
    failures = LoginAttempt.objects.filter(
        email=email,
        ip=ip,
        purpose=purpose,
        succeeded=False,
        attempted_at__gte=since,
    ).count()
    if failures:
        time.sleep(min(delay * failures, 2))


def record(*, email: str, ip: str | None, purpose: str, succeeded: bool) -> None:
    LoginAttempt.objects.create(email=email, ip=ip, purpose=purpose, succeeded=succeeded)
