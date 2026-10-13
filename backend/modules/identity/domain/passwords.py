"""Argon2id password hashing. Document 06 prefers length over composition rules."""

from __future__ import annotations

import secrets

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError, VerifyMismatchError

_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=19_456,
    parallelism=1,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)
_dummy_hash: str | None = None


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def password_rejection(password: str, *, minimum: int, maximum: int) -> str | None:
    if len(password) < minimum:
        return f"Password must be at least {minimum} characters."
    if len(password) > maximum:
        return f"Password must be at most {maximum} characters."
    return None


def verify_password(password: str, encoded: str | None) -> bool:
    """Return whether `password` matches. Unknown users still pay one Argon2id check."""
    usable = bool(encoded and encoded.startswith("$argon2id$"))
    candidate = encoded if usable and encoded is not None else _dummy()
    matched: bool
    try:
        matched = _hasher.verify(candidate, password)
    except (VerifyMismatchError, VerificationError):
        matched = False
    return usable and matched


def _dummy() -> str:
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password(secrets.token_urlsafe(32))
    return _dummy_hash
