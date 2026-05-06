"""通用 Pydantic 响应模型。

封装统一响应信封，定义见
``docs/specs/backend/00-architecture/api-design.md``。
"""

from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Pagination(BaseModel):
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_pages: int = Field(ge=0)


class ApiResponse(BaseModel, Generic[T]):
    """单资源/无分页接口的统一响应。"""

    data: T | None = None
    message: str = "ok"


class PaginatedResponse(BaseModel, Generic[T]):
    """分页列表接口的统一响应。"""

    data: list[T]
    pagination: Pagination
    message: str = "ok"


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Optional[list[ErrorDetail]] = None


class ErrorResponse(BaseModel):
    error: ErrorBody
