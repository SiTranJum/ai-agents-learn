"""集中式日志配置。

替代原来 ``main.py`` 里的 ``logging.basicConfig``，提供：

- ``setup_logging()``：用 ``dictConfig`` 集中配置 root + 关键 logger（uvicorn、sqlalchemy、langchain）
- ``request_id_var``：基于 ``contextvars`` 的请求级 trace id，跨 await 传递
- ``RequestIdFilter``：把 ``request_id`` 注入到每条 ``LogRecord``，供 formatter 使用
- ``RequestIdMiddleware``：Starlette 中间件，从 ``X-Request-ID`` 读取或生成 UUID 并设置到 contextvars

日志格式：
    时间 | 级别 | request_id | 协程名 | logger名 | 消息

并发请求下，凭 ``request_id`` 即可串起一次请求里所有节点的日志。
"""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

import logging
import logging.config
import os
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# ---------- contextvars ----------

# ContextVar 在 asyncio 中跨 await/Task 自动传递；类似 Java 的 ThreadLocal，
# 但作用域是协程而不是线程。
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


# ---------- 日志 Filter：把 request_id 注入到 LogRecord ----------


class RequestIdFilter(logging.Filter):
    """从 contextvars 取出 request_id 注入到每条 LogRecord。

    Filter 在 Logger 处理 record 时被调用，这里我们不过滤、只附加属性，
    让 Formatter 可以用 ``%(request_id)s`` 输出。
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.request_id = request_id_var.get()
        return True


# ---------- 彩色 Formatter ----------


def _enable_windows_ansi() -> None:
    """在 Windows 10+ 老版 cmd.exe 上启用 ANSI VT 模式。

    Windows Terminal / VS Code Terminal / PowerShell 7+ 默认支持 ANSI，
    但 Win10 默认 cmd 需要调用一次系统命令来开启。
    """
    if sys.platform == "win32":
        os.system("")  # noqa: S605,S607 - intentional, enables VT processing


def _supports_color() -> bool:
    """决定是否输出 ANSI 颜色。

    - 显式 ``NO_COLOR=1`` 关闭（遵循 https://no-color.org/ 约定）
    - 显式 ``FORCE_COLOR=1`` 强制开启
    - 否则只在终端是 TTY 时开启（重定向到文件时关闭）
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty() if hasattr(sys.stdout, "isatty") else False


class ColorFormatter(logging.Formatter):
    """根据级别给整行上色，并把不同字段染上不同颜色。

    使用 ANSI 转义序列：``\\033[Nm`` 是颜色控制码，``\\033[0m`` 重置。
    """

    # 主题色：按级别决定时间/级别/消息的主色调
    LEVEL_COLOR = {
        "DEBUG": "\033[90m",       # gray
        "INFO": "\033[37m",        # white (终端默认前景)
        "WARNING": "\033[33m",     # yellow
        "ERROR": "\033[31m",       # red
        "CRITICAL": "\033[1;91m",  # bold bright red
    }

    DIM = "\033[2m"          # 暗淡（时间戳）
    CYAN = "\033[36m"        # 备用
    GREEN = "\033[92m"       # logger 名（亮绿，区分于级别色和消息）
    MAGENTA = "\033[35m"     # request_id
    RESET = "\033[0m"

    # logger 名固定列宽，超长用 logback 风格缩短，不足左填充空格
    LOGGER_WIDTH = 24

    def __init__(self, *, use_color: bool = True, datefmt: str | None = None) -> None:
        super().__init__(datefmt=datefmt)
        self.use_color = use_color

    @staticmethod
    def _shorten_logger(name: str, width: int) -> str:
        """把 logger 名压到指定宽度，仿 Java logback 的 ``%logger{N}``。

        策略：
        1. 不超长直接左填充返回；
        2. 超长时从最左包名开始逐段压成单字符，直到整体 <= width；
        3. 仍超长则截断尾部并加省略号。

        例：``app.agents.chat.nodes``（width=15）→ ``a.a.c.nodes``。
        """
        if len(name) <= width:
            return name.ljust(width)
        parts = name.split(".")
        for i in range(len(parts) - 1):
            parts[i] = parts[i][0]
            candidate = ".".join(parts)
            if len(candidate) <= width:
                return candidate.ljust(width)
        # 实在还是超长（最后一段太长），从右截断 + 省略号
        return name[: width - 1] + "…"

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        # 标准库 Formatter.format 内部会调 formatTime / getMessage / formatException，
        # 这里我们绕开模板字符串，直接拼字符串以便精细控制颜色和字段宽度。
        record.asctime = self.formatTime(record, self.datefmt)
        message = record.getMessage()
        request_id = getattr(record, "request_id", "-")
        level = record.levelname
        logger_name = self._shorten_logger(record.name, self.LOGGER_WIDTH)

        if not self.use_color:
            line = (
                f"{record.asctime} | {level:<8} | {request_id} | "
                f"{logger_name} | {message}"
            )
        else:
            level_color = self.LEVEL_COLOR.get(level, "")
            line = (
                f"{self.DIM}{record.asctime}{self.RESET} | "
                f"{level_color}{level:<8}{self.RESET} | "
                f"{self.MAGENTA}{request_id}{self.RESET} | "
                f"{self.GREEN}{logger_name}{self.RESET} | "
                f"{level_color}{message}{self.RESET}"
            )

        # 异常 traceback 默认追加在末尾，不上色（保持可读）
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            line += "\n" + record.exc_text
        if record.stack_info:
            line += "\n" + self.formatStack(record.stack_info)
        return line


# ---------- dictConfig ----------


def build_logging_config(level: str = "INFO") -> dict[str, Any]:
    """构造 dictConfig 字典。集中管理所有 handler / formatter / logger。"""
    use_color = _supports_color()
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {"()": RequestIdFilter},
        },
        "formatters": {
            # ColorFormatter 会自动按级别上色；非 TTY 环境下退化为纯文本。
            # datefmt 去掉年份和毫秒，保留 "月-日 时:分:秒"
            "default": {
                "()": ColorFormatter,
                "use_color": use_color,
                "datefmt": "%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                # 默认 StreamHandler 写 stderr，PyCharm/IDEA Run 控制台会把 stderr
                # 整行染红，覆盖我们自己的 ANSI 颜色。改写 stdout 才能正常显示。
                "stream": "ext://sys.stdout",
                "formatter": "default",
                "filters": ["request_id"],
            },
        },
        "loggers": {
            # 业务代码统一前缀
            "app": {"level": level, "handlers": ["console"], "propagate": False},
            # uvicorn 三个 logger 统一收编，避免重复输出
            "uvicorn": {"level": level, "handlers": ["console"], "propagate": False},
            "uvicorn.error": {"level": level, "handlers": ["console"], "propagate": False},
            "uvicorn.access": {"level": "INFO", "handlers": ["console"], "propagate": False},
            # SQLAlchemy 默认很吵，调成 WARNING；需要看 SQL 时改 INFO
            "sqlalchemy.engine": {"level": "WARNING", "handlers": ["console"], "propagate": False},
            # LangChain / LangGraph
            "langchain": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "langgraph": {"level": "INFO", "handlers": ["console"], "propagate": False},
        },
        "root": {"level": level, "handlers": ["console"]},
    }


def setup_logging(level: str = "INFO") -> None:
    """应用启动时调用一次。"""
    _enable_windows_ansi()
    logging.config.dictConfig(build_logging_config(level))


# ---------- 中间件 ----------


class RequestIdMiddleware(BaseHTTPMiddleware):
    """生成或透传 request_id，写入 contextvars，并在响应头回写。

    优先使用客户端传入的 ``X-Request-ID``（便于联调链路追踪），
    否则生成 8 位短 UUID（足够单次日志关联使用）。
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming = request.headers.get(self.header_name)
        request_id = incoming or uuid.uuid4().hex[:8]
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers[self.header_name] = request_id
            return response
        finally:
            # 清理 contextvars，避免 worker 复用时状态泄漏
            request_id_var.reset(token)


__all__ = [
    "RequestIdFilter",
    "RequestIdMiddleware",
    "build_logging_config",
    "request_id_var",
    "setup_logging",
]
