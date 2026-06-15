"""LangGraph Checkpointer 装配（Postgres / 内存）。

为什么需要 checkpointer：
- ``interrupt()`` 让 graph 在节点内"就地暂停"，把问题抛给用户。
- 暂停时的完整 state（解析结果、草案、走到哪一步）必须被持久化，
  否则用户回答后无法从中断点恢复。checkpointer 就是这个"存档点"。
- 没有 checkpointer，``interrupt()`` 无处保存现场 → 无法暂停/恢复。

实现要点（对 Java 开发者的类比）：
- ``AsyncConnectionPool`` ≈ HikariCP 连接池，但用的是 psycopg(3) 驱动。
  注意 **不是 asyncpg**：业务 ORM 用 asyncpg，checkpointer 用 psycopg，二者分开。
- ``AsyncPostgresSaver`` ≈ 一个把 graph 状态读写到几张 checkpoint 表的 DAO。
- ``setup()`` ≈ 建表 DDL（幂等），首次调用时创建 checkpoints / checkpoint_writes 等表。
"""

from __future__ import annotations

import enum
import importlib
import inspect
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# 进程内单例：连接池 + saver 复用，避免每次请求重建连接。
_pool = None
_saver = None

# state 中会被 checkpoint 序列化的 pydantic 模型 / 枚举所在模块。
# langgraph 用 msgpack 持久化 state，未来版本会**禁止**反序列化未在
# ``allowed_msgpack_modules`` 注册的自定义类型。这里列出所有可能进 state
# 的 schema 模块，``_build_serde`` 会自动扫描其中的 BaseModel/Enum 子类注册。
_CHECKPOINT_SCHEMA_MODULES = (
    "app.schemas.auth",
    "app.schemas.diet",
    "app.schemas.body",
    "app.schemas.plan",
    "app.schemas.chat",
)


def _build_serde():
    """构造允许反序列化项目 schema 类型的 JsonPlusSerializer。

    自动扫描 ``_CHECKPOINT_SCHEMA_MODULES`` 内定义的 pydantic ``BaseModel`` 与
    ``enum.Enum`` 子类，生成 ``(module, qualname)`` 白名单。避免手工逐个枚举
    导致漏注册（漏注册会触发"未来版本将阻止反序列化"告警，且最终会反序列化失败）。
    """
    from pydantic import BaseModel

    allowed: list[tuple[str, str]] = []
    for module_name in _CHECKPOINT_SCHEMA_MODULES:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            logger.warning("checkpoint serde: cannot import %s, skipped", module_name)
            continue
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # 只注册本模块定义的类，避免把 re-import 的第三方类也算进来。
            if obj.__module__ == module_name and issubclass(obj, (BaseModel, enum.Enum)):
                allowed.append((module_name, name))

    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    return JsonPlusSerializer(allowed_msgpack_modules=allowed)


def checkpointer_dsn() -> str:
    """返回供 psycopg 使用的 DSN。

    SQLAlchemy 用 ``postgresql+asyncpg://...``，但 psycopg 不认 ``+asyncpg``，
    需要裸 ``postgresql://...``。优先用显式配置的 ``checkpointer_dsn``，
    否则从 ``database_url`` 推导。

    自动补 ``connect_timeout``（若 DSN 未显式带），避免库连不上时单次连接
    长时间挂起拖慢启动。
    """
    dsn = settings.checkpointer_dsn or settings.database_url.replace("+asyncpg", "")
    if "connect_timeout" not in dsn:
        sep = "&" if "?" in dsn else "?"
        dsn = f"{dsn}{sep}connect_timeout=10"
    return dsn


def _memory_saver():
    """降级用的进程内 MemorySaver（重启即丢，但能让对话/中断恢复正常工作）。"""
    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver(serde=_build_serde())


async def get_checkpointer():
    """构造并复用全局 checkpointer。

    - ``checkpointer_enabled=False`` → 返回进程内 ``MemorySaver``
      （重启即丢，仅用于本地无 Postgres 的快速验证）。
    - 否则返回 ``AsyncPostgresSaver``，首次调用执行 ``setup()`` 幂等建表。

    兜底原则：Postgres 装配（连池 / 建表）出任何问题都**降级到 MemorySaver**，
    绝不让 checkpointer 故障把 ``/chat`` 请求打成 500——对话可用性优先于持久化。

    Supabase 兼容：
    - ``autocommit=True`` + ``prepare_threshold=None``：关闭服务端预编译语句，
      避免 transaction-mode 连接池下 "prepared statement already exists"。
    - ``statement_timeout=0``：建表 DDL 较慢，Supabase 默认 statement_timeout
      会把 ``setup()`` 的 CREATE TABLE/INDEX 掐断（QueryCanceled），这里对
      checkpointer 连接关闭该超时。
    """
    global _pool, _saver
    if _saver is not None:
        return _saver

    if not settings.checkpointer_enabled:
        logger.warning("checkpointer disabled → using in-memory MemorySaver (no persistence)")
        _saver = _memory_saver()
        return _saver

    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool

        # min_size 取 1 并不大于 max_size：AsyncConnectionPool 默认 min_size=4，
        # 若 max_size 配得更小（默认 3）会抛 "max_size must be >= min_size"。
        min_size = min(1, settings.checkpointer_pool_max_size)
        _pool = AsyncConnectionPool(
            conninfo=checkpointer_dsn(),
            min_size=min_size,
            max_size=settings.checkpointer_pool_max_size,
            open=False,
            # psycopg 连接级参数：Supabase 连接池兼容 + 关闭建表 DDL 超时
            kwargs={
                "autocommit": True,
                "prepare_threshold": None,
                "options": "-c statement_timeout=0",
            },
        )
        await _pool.open(wait=True, timeout=10)
        saver = AsyncPostgresSaver(_pool, serde=_build_serde())
        await saver.setup()  # 幂等建表
        _saver = saver
        logger.info(
            "AsyncPostgresSaver ready (pool max_size=%s)", settings.checkpointer_pool_max_size
        )
        return _saver
    except Exception as exc:  # noqa: BLE001
        # 连池失败 / 建表超时 / 网络问题 → 降级，保证对话不挂。
        logger.error(
            "checkpointer Postgres setup failed (%s) → falling back to in-memory MemorySaver; "
            "中断态将无法跨进程持久化",
            exc,
        )
        if _pool is not None:
            try:
                await _pool.close()
            except Exception:  # noqa: BLE001
                pass
            _pool = None
        _saver = _memory_saver()
        return _saver


async def close_checkpointer() -> None:
    """应用关闭时释放连接池。"""
    global _pool, _saver
    if _pool is not None:
        await _pool.close()
        _pool = None
    _saver = None


__all__ = ["checkpointer_dsn", "close_checkpointer", "get_checkpointer"]
