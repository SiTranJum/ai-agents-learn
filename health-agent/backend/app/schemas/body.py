"""身体数据追踪 Pydantic 模型。"""

from __future__ import annotations

import re
from datetime import date as date_
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class BodyRecordType(StrEnum):
    weight = "weight"
    measurement = "measurement"
    sleep = "sleep"
    exercise = "exercise"
    water = "water"
    bowel = "bowel"


class TimeRange(StrEnum):
    seven_days = "7d"
    thirty_days = "30d"
    ninety_days = "90d"
    year = "365d"


class SleepQuality(StrEnum):
    excellent = "excellent"
    good = "good"
    fair = "fair"
    poor = "poor"


class BowelStatus(StrEnum):
    normal = "normal"
    constipation = "constipation"
    diarrhea = "diarrhea"


class MeasurementMetric(StrEnum):
    waist = "waist"
    hip = "hip"
    thigh = "thigh"
    arm = "arm"


class BodyCreateBase(BaseModel):
    date: date_ = Field(default_factory=date_.today)

    @model_validator(mode="after")
    def validate_not_future(self) -> BodyCreateBase:
        if self.date > date_.today():
            raise ValueError("日期不能是未来日期")
        return self


class WeightRecordCreate(BodyCreateBase):
    weight: float = Field(ge=30.0, le=300.0)
    note: str | None = Field(default=None, max_length=200)


class WeightRecordUpdate(BaseModel):
    date: date_ | None = None
    weight: float | None = Field(default=None, ge=30.0, le=300.0)
    note: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_not_future(self) -> WeightRecordUpdate:
        if self.date is not None and self.date > date_.today():
            raise ValueError("日期不能是未来日期")
        return self


class MeasurementRecordCreate(BodyCreateBase):
    waist: float | None = Field(default=None, ge=30.0, le=200.0)
    hip: float | None = Field(default=None, ge=30.0, le=200.0)
    thigh: float | None = Field(default=None, ge=10.0, le=100.0)
    arm: float | None = Field(default=None, ge=10.0, le=80.0)
    note: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_has_measurement(self) -> MeasurementRecordCreate:
        super().validate_not_future()
        if all(value is None for value in (self.waist, self.hip, self.thigh, self.arm)):
            raise ValueError("至少需要填写一项围度")
        return self


class MeasurementRecordUpdate(BaseModel):
    date: date_ | None = None
    waist: float | None = Field(default=None, ge=30.0, le=200.0)
    hip: float | None = Field(default=None, ge=30.0, le=200.0)
    thigh: float | None = Field(default=None, ge=10.0, le=100.0)
    arm: float | None = Field(default=None, ge=10.0, le=80.0)
    note: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_not_future(self) -> MeasurementRecordUpdate:
        if self.date is not None and self.date > date_.today():
            raise ValueError("日期不能是未来日期")
        return self


class SleepRecordCreate(BodyCreateBase):
    bed_time: str = Field(pattern=TIME_PATTERN.pattern, description="HH:mm")
    wake_time: str = Field(pattern=TIME_PATTERN.pattern, description="HH:mm")
    quality: SleepQuality
    note: str | None = Field(default=None, max_length=200)


class SleepRecordUpdate(BaseModel):
    date: date_ | None = None
    bed_time: str | None = Field(default=None, pattern=TIME_PATTERN.pattern, description="HH:mm")
    wake_time: str | None = Field(default=None, pattern=TIME_PATTERN.pattern, description="HH:mm")
    quality: SleepQuality | None = None
    note: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_not_future(self) -> SleepRecordUpdate:
        if self.date is not None and self.date > date_.today():
            raise ValueError("日期不能是未来日期")
        return self


class ExerciseRecordCreate(BodyCreateBase):
    type: str = Field(min_length=1, max_length=50)
    duration: int = Field(ge=1, le=600, description="分钟")
    calories: int | None = Field(default=None, ge=0, le=5000)
    note: str | None = Field(default=None, max_length=200)


class ExerciseRecordUpdate(BaseModel):
    date: date_ | None = None
    type: str | None = Field(default=None, min_length=1, max_length=50)
    duration: int | None = Field(default=None, ge=1, le=600)
    calories: int | None = Field(default=None, ge=0, le=5000)
    note: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_not_future(self) -> ExerciseRecordUpdate:
        if self.date is not None and self.date > date_.today():
            raise ValueError("日期不能是未来日期")
        return self


class WaterRecordCreate(BodyCreateBase):
    amount: int = Field(ge=1, le=5000, description="本次新增饮水量 ml")
    target: int = Field(default=2000, ge=500, le=10000)


class WaterRecordUpdate(BaseModel):
    date: date_ | None = None
    amount: int | None = Field(default=None, ge=0, le=10000)
    target: int | None = Field(default=None, ge=500, le=10000)

    @model_validator(mode="after")
    def validate_not_future(self) -> WaterRecordUpdate:
        if self.date is not None and self.date > date_.today():
            raise ValueError("日期不能是未来日期")
        return self


class BowelRecordCreate(BodyCreateBase):
    time: str = Field(pattern=TIME_PATTERN.pattern, description="HH:mm")
    status: BowelStatus
    note: str | None = Field(default=None, max_length=200)


class BowelRecordUpdate(BaseModel):
    date: date_ | None = None
    time: str | None = Field(default=None, pattern=TIME_PATTERN.pattern, description="HH:mm")
    status: BowelStatus | None = None
    note: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_not_future(self) -> BowelRecordUpdate:
        if self.date is not None and self.date > date_.today():
            raise ValueError("日期不能是未来日期")
        return self


class WeightRecordResponse(BaseModel):
    id: UUID
    date: date_
    weight: float
    bmi: float | None = None
    change: float
    note: str | None = None
    anomaly_warning: str | None = None
    created_at: datetime
    updated_at: datetime


class MeasurementRecordResponse(BaseModel):
    id: UUID
    date: date_
    waist: float | None = None
    hip: float | None = None
    thigh: float | None = None
    arm: float | None = None
    note: str | None = None
    anomaly_warning: str | None = None
    created_at: datetime
    updated_at: datetime


class SleepRecordResponse(BaseModel):
    id: UUID
    date: date_
    bed_time: str
    wake_time: str
    duration: int
    quality: SleepQuality
    note: str | None = None
    created_at: datetime
    updated_at: datetime


class ExerciseRecordResponse(BaseModel):
    id: UUID
    date: date_
    type: str
    duration: int
    calories: int
    note: str | None = None
    created_at: datetime
    updated_at: datetime


class WaterRecordResponse(BaseModel):
    id: UUID
    date: date_
    amount: int
    target: int
    created_at: datetime
    updated_at: datetime


class BowelRecordResponse(BaseModel):
    id: UUID
    date: date_
    time: str
    status: BowelStatus
    note: str | None = None
    created_at: datetime
    updated_at: datetime


BodyRecordResponse = (
    WeightRecordResponse
    | MeasurementRecordResponse
    | SleepRecordResponse
    | ExerciseRecordResponse
    | WaterRecordResponse
    | BowelRecordResponse
)


class TodayRecords(BaseModel):
    weight: WeightRecordResponse | None = None
    measurement: MeasurementRecordResponse | None = None
    sleep: SleepRecordResponse | None = None
    exercise: ExerciseRecordResponse | None = None
    water: WaterRecordResponse | None = None
    bowel: BowelRecordResponse | None = None


class TrendPoint(BaseModel):
    date: date_
    value: float


class TrendStatistics(BaseModel):
    min: float = 0
    max: float = 0
    average: float = 0
    latest: float = 0
    change: float = 0


class TrendResponse(BaseModel):
    type: BodyRecordType
    period: TimeRange
    metric: str
    data_points: list[TrendPoint]
    statistics: TrendStatistics
    target: float | None = None


__all__ = [
    "BodyRecordResponse",
    "BodyRecordType",
    "BowelRecordCreate",
    "BowelRecordResponse",
    "BowelRecordUpdate",
    "BowelStatus",
    "ExerciseRecordCreate",
    "ExerciseRecordResponse",
    "ExerciseRecordUpdate",
    "MeasurementMetric",
    "MeasurementRecordCreate",
    "MeasurementRecordResponse",
    "MeasurementRecordUpdate",
    "SleepQuality",
    "SleepRecordCreate",
    "SleepRecordResponse",
    "SleepRecordUpdate",
    "TimeRange",
    "TodayRecords",
    "TrendPoint",
    "TrendResponse",
    "TrendStatistics",
    "WaterRecordCreate",
    "WaterRecordResponse",
    "WaterRecordUpdate",
    "WeightRecordCreate",
    "WeightRecordResponse",
    "WeightRecordUpdate",
]

