"""Decimal money matching PostgreSQL NUMERIC(19,4).

Document 00 stores money as Decimal / NUMERIC(19,4) and sends API amounts as
decimal strings. Values with more than four decimal places are rejected
rather than rounded. Floating-point values are rejected.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Final

MONEY_MAX_DIGITS: Final = 19
MONEY_DECIMAL_PLACES: Final = 4
_QUANTUM: Final = Decimal("0.0001")
_MAX_WHOLE_DIGITS: Final = MONEY_MAX_DIGITS - MONEY_DECIMAL_PLACES


def money(value: Decimal | int | str) -> Decimal:
    """Return a value that fits NUMERIC(19,4).

    ``int`` and decimal strings are exact. ``bool`` and ``float`` are rejected.
    """
    amount = _decimal(value)
    if not amount.is_finite():
        raise ValueError("money values must be finite")
    exponent = amount.as_tuple().exponent
    if not isinstance(exponent, int):
        raise ValueError("money values must be finite")
    scale = -exponent if exponent < 0 else 0
    if scale > MONEY_DECIMAL_PLACES:
        raise ValueError("money values have at most 4 decimal places")
    whole_digits = len(amount.as_tuple().digits) + exponent
    if whole_digits > _MAX_WHOLE_DIGITS:
        raise ValueError("money value exceeds NUMERIC(19,4)")
    return amount.quantize(_QUANTUM)


def money_to_json(value: Decimal | int | str) -> str:
    """Decimal string for an API amount. The result is not a JSON number."""
    return format(money(value), "f")


def _decimal(value: Decimal | int | str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Decimal | int | str):
        raise TypeError("money values must be Decimal, int, or a decimal string")
    try:
        return value if isinstance(value, Decimal) else Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("money values must be decimal strings") from exc
