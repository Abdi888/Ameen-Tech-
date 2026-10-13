"""Document 05 collection parameters: page, page_size, and a sort whitelist."""

from __future__ import annotations

from collections.abc import Mapping

from shared.exceptions import ApiError

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


def read_page(
    params: Mapping[str, str], *, allowed_sorts: Mapping[str, str]
) -> tuple[int, int, str]:
    unknown = set(params) - {"page", "page_size", "sort"}
    if unknown:
        field = sorted(unknown)[0]
        raise ApiError("INVALID_VALUE", "This query parameter is not supported.", field=field)
    page = _positive_int(params.get("page"), default=1, field="page")
    page_size = _positive_int(
        params.get("page_size"),
        default=DEFAULT_PAGE_SIZE,
        field="page_size",
        maximum=MAX_PAGE_SIZE,
    )
    sort_key = params.get("sort", "")
    if not sort_key:
        return page, page_size, ""
    if sort_key not in allowed_sorts:
        raise ApiError("INVALID_VALUE", "This sort field is not supported.", field="sort")
    return page, page_size, allowed_sorts[sort_key]


def pagination_meta(*, page: int, page_size: int, total: int) -> dict[str, object]:
    total_pages = (total + page_size - 1) // page_size if total else 0
    return {
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }
    }


def _positive_int(
    raw: str | None,
    *,
    default: int,
    field: str,
    maximum: int | None = None,
) -> int:
    if raw is None or raw == "":
        return default
    if not raw.isdigit():
        raise ApiError("INVALID_VALUE", "This value must be a positive integer.", field=field)
    value = int(raw)
    if value < 1:
        raise ApiError("INVALID_VALUE", "This value must be a positive integer.", field=field)
    if maximum is not None and value > maximum:
        raise ApiError("INVALID_VALUE", f"This value cannot exceed {maximum}.", field=field)
    return value
