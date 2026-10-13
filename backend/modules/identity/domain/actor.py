from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class Actor:
    """Authenticated user attached to the request. Not a Django auth user."""

    id: uuid.UUID
    tenant_id: uuid.UUID | None
    membership_id: uuid.UUID | None

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def pk(self) -> uuid.UUID:
        return self.id
