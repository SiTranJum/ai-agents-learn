"""FastAPI 应用入口。

职责：
- 配置日志
- 构造带元信息和 CORS 的 ``FastAPI`` 实例
- 注册全局异常处理器（统一错误响应信封）
- 在 ``/api/v1`` 下挂载 v1 路由
- 通过 ``lifespan`` 管理异步数据库引擎的生命周期
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import AppException
from app.core.responses import error as error_body
from app.db.session import dispose_engine

# ---------- 日志 ----------

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("app")


# ---------- 生命周期 ----------


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """应用启动/关闭钩子：日志输出 + 引擎释放。"""
    logger.info(
        "Starting %s in %s mode (debug=%s)",
        settings.app_name,
        settings.app_env,
        settings.app_debug,
    )
    try:
        yield
    finally:
        await dispose_engine()
        logger.info("数据库引擎已释放，应用关闭完成")


# ---------- 应用工厂 ----------


def create_app() -> FastAPI:
    """构造并返回 FastAPI 应用实例。"""
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="健康管家 AI Agent 后端服务",
        debug=settings.app_debug,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    # CORS：允许 settings 中配置的开发端口（Expo / Web）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_exception_handlers(app)

    # 健康探针（也方便部署平台做健康检查）
    @app.get("/health", tags=["meta"], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.app_env}

    @app.get("/", tags=["meta"], include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
        }

    app.include_router(api_router, prefix="/api/v1")

    return app


# ---------- 异常处理器 ----------


def _register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器，统一输出错误响应信封。"""

    @app.exception_handler(AppException)
    async def handle_app_exception(_req: Request, exc: AppException) -> JSONResponse:
        logger.info(
            "AppException code=%s status=%s msg=%s",
            exc.code,
            exc.status_code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _req: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # 将 Pydantic 校验错误转成统一的 details 列表
        details = [
            {
                "field": ".".join(str(p) for p in err.get("loc", []) if p != "body"),
                "message": err.get("msg", "invalid value"),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_body(
                "VALIDATION_ERROR",
                "请求参数校验失败",
                details=details,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        _req: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        # 将常见的 HTTP 错误映射到统一信封，同时保留原状态码
        code_map = {
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code, str(exc.detail) if exc.detail else code),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_req: Request, exc: Exception) -> JSONResponse:
        logger.exception("未捕获异常", exc_info=exc)
        # 非 debug 环境下不暴露内部细节
        message = "服务器内部错误"
        details = None
        if settings.app_debug:
            details = jsonable_encoder([{"field": "traceback", "message": str(exc)}])
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_body("INTERNAL_ERROR", message, details=details),
        )


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
