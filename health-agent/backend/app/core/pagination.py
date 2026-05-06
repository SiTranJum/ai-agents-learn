"""基于偏移量的分页工具。

API 规范：``page`` 从 1 开始，``page_size`` 取值范围 1-100。
详见 ``docs/specs/backend/00-architecture/api-design.md`` §5。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import Query

SortOrder = Literal["asc", "desc"]


@dataclass(slots=True)
class PageParams:
    """分页参数对象，便于 service / repository 层使用。"""

    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: SortOrder = "desc"

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def page_params(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数（1-100）"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: SortOrder = Query("desc", description="排序方向"),
) -> PageParams:
    """FastAPI 依赖：解析标准分页查询参数。"""
    return PageParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
