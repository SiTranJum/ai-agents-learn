"""标准化 JSON 响应构造工具。

在 API 路由中使用以下函数（或借助 Pydantic ``response_model``）保持
全局响应信封一致。
"""

from __future__ import annotations

import math
from typing import Any

from app.schemas.common import (
    ApiResponse,
    ErrorBody,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    Pagination,
)


def success(data: Any = None, message: str = "ok") -> dict[str, Any]:
    """将数据封装到标准成功响应信封（返回 dict）。"""
    return ApiResponse[Any](data=data, message=message).model_dump()


def paginated(
    items: list[Any],
    *,
    total: int,
    page: int,
    page_size: int,
    message: str = "ok",
) -> dict[str, Any]:
    """将列表封装到标准分页响应信封（返回 dict）。"""
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0
    return PaginatedResponse[Any](
        data=items,
        pagination=Pagination(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
        message=message,
    ).model_dump()


def error(
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """构造错误响应体（不含 HTTP 状态码）。"""
    detail_models = (
        [ErrorDetail(field=d["field"], message=d["message"]) for d in details]
        if details
        else None
    )
    return ErrorResponse(
        error=ErrorBody(code=code, message=message, details=detail_models)
    ).model_dump()
