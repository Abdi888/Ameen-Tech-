"""Database field types shared by later domain tables."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

from django.db import models

from shared.money import MONEY_DECIMAL_PLACES, MONEY_MAX_DIGITS

if TYPE_CHECKING:
    _MoneyFieldBase = models.DecimalField[Decimal, Decimal]
else:
    _MoneyFieldBase = models.DecimalField


class MoneyField(_MoneyFieldBase):
    """PostgreSQL NUMERIC(19,4). Digits and scale are fixed by Document 00."""

    description = "NUMERIC(19,4) money"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["max_digits"] = MONEY_MAX_DIGITS
        kwargs["decimal_places"] = MONEY_DECIMAL_PLACES
        super().__init__(*args, **kwargs)

    def to_python(self, value: Any) -> Decimal | None:
        if isinstance(value, float):
            raise TypeError("money values must be Decimal, int, or a decimal string")
        return cast("Decimal | None", super().to_python(value))

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        kwargs.pop("max_digits", None)
        kwargs.pop("decimal_places", None)
        return name, path, args, kwargs
