"""为 Alembic 自动发现 metadata 而集中导入所有 ORM 模型。

每当在 ``app/db/models/`` 下新增模型文件，请在此处 import，使其
随 ``Base.metadata`` 一起被 Alembic 自动生成迁移时识别。

Phase 0 暂未引入业务表模型，将在后续阶段陆续补齐。
"""

from app.db.base import Base  # 重新导出，方便外部使用

# 后续按阶段陆续放开下列 import，例如：
# from app.db.models.user import User, HealthProfile  # noqa: F401

__all__ = ["Base"]
