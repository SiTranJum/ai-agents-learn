"""为 Alembic 自动发现 metadata 而集中导入所有 ORM 模型。

每当在 ``app/db/models/`` 下新增模型文件, 请在此处 import, 使其
随 ``Base.metadata`` 一起被 Alembic 自动生成迁移时识别。
"""

from app.db.base import Base  # 重新导出, 方便外部使用
from app.db.models.body import (
    BowelRecord,
    ExerciseRecord,
    MeasurementRecord,
    SleepRecord,
    WaterRecord,
    WeightRecord,
)
from app.db.models.diet import DietItem, DietRecord
from app.db.models.knowledge import Food, KnowledgeDoc
from app.db.models.user import (
    HealthProfile,
    UserHealthInfo,
    UserPreference,
    UserSetting,
)

__all__ = [
    "Base",
    "BowelRecord",
    "DietItem",
    "DietRecord",
    "ExerciseRecord",
    "Food",
    "HealthProfile",
    "KnowledgeDoc",
    "MeasurementRecord",
    "SleepRecord",
    "UserHealthInfo",
    "UserPreference",
    "UserSetting",
    "WaterRecord",
    "WeightRecord",
]
