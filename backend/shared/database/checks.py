"""Database reachability used by the health check.

The driver exception is not logged. Its message can contain connection
details. The client receives SERVICE_UNAVAILABLE and nothing else.
"""

from __future__ import annotations

import logging

from django.db import DatabaseError, connection

logger = logging.getLogger("ameen.request")


def database_is_reachable() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
    except DatabaseError:
        logger.error("database health check failed")
        return False
    return row is not None and row[0] == 1
