"""应用级异常体系。

所有业务异常继承自 :class:`AppException`，并由 :mod:`app.main` 中
注册的全局异常处理器统一转换为标准 JSON 错误响应
（参见 :mod:`app.core.responses`）。
"""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """所有应用异常的基类。

    属性：
        code: 稳定的机器可读错误码（例如 ``USER_NOT_FOUND``）。
        message: 面向用户的可读错误信息（允许中文）。
        status_code: 对应的 HTTP 状态码。
        details: 可选的结构化错误详情（如字段级校验错误列表）。
    """

    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    default_message: str = "服务器内部错误"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.message = message or self.default_message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details
        super().__init__(self.message)


# ---------- 4xx ----------


class ValidationException(AppException):
    code = "VALIDATION_ERROR"
    status_code = 400
    default_message = "请求参数校验失败"


class UnauthorizedException(AppException):
    code = "UNAUTHORIZED"
    status_code = 401
    default_message = "未认证或登录已过期"


class ForbiddenException(AppException):
    code = "FORBIDDEN"
    status_code = 403
    default_message = "无权访问该资源"


class NotFoundException(AppException):
    code = "NOT_FOUND"
    status_code = 404
    default_message = "资源不存在"


class ConflictException(AppException):
    code = "CONFLICT"
    status_code = 409
    default_message = "资源冲突"


class BusinessRuleException(AppException):
    """422 — 请求格式合法但违反领域规则。"""

    code = "BUSINESS_RULE_VIOLATION"
    status_code = 422
    default_message = "业务规则校验失败"


# ---------- 5xx ----------


class ExternalServiceException(AppException):
    """外部依赖（LLM、Supabase 等）调用失败时抛出。"""

    code = "EXTERNAL_SERVICE_UNAVAILABLE"
    status_code = 503
    default_message = "外部服务暂时不可用"


class LLMProviderException(ExternalServiceException):
    code = "LLM_SERVICE_UNAVAILABLE"
    default_message = "LLM 服务暂时不可用"
