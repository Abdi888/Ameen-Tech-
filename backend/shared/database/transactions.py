"""Database transaction boundary for one business use case.

Later use cases call ``run_in_transaction`` once. The callable is the whole
operation: domain changes, module contracts, and the audit write. The
database commits when the callable returns and rolls those writes back when
it raises. Do not commit inside the callable, and do not schedule Celery
there. Document 00 runs workers only after commit; a later phase can register
``transaction.on_commit`` inside the operation when it has post-commit work.

If a caller is already inside a transaction, this joins it with a savepoint.
A failure still undoes the operation's writes. The test suite uses that
outer transaction.

Outbox schema dependency (unresolved): Document 00 §6 and Document 09 §8
require an outbox row in the same commit as CompleteSale. Document 02 does
not define that table. This phase does not invent its columns. A later
approval has to name the schema before any outbox migration.
"""

from __future__ import annotations

from collections.abc import Callable

from django.db import transaction


def run_in_transaction[T](operation: Callable[[], T]) -> T:
    with transaction.atomic():
        return operation()
