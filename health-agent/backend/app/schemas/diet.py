"""饮食记录 Pydantic 模型。"""

from __future__ import annotations

from datetime import date as date_
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class MealType(StrEnum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"


class DataSource(StrEnum):
    database = "database"
    api = "api"
    llm_estimate = "llm_estimate"


class NutritionSummary(BaseModel):
    total_calories: float = Field(default=0, ge=0)
    total_protein: float = Field(default=0, ge=0)
    total_fat: float = Field(default=0, ge=0)
    total_carbs: float = Field(default=0, ge=0)
    total_fiber: float | None = Field(default=None, ge=0)
    total_sodium: float | None = Field(default=None, ge=0)


class ParsedFood(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)
    amount_grams: float = Field(gt=0)
    cooking_method: str | None = Field(default=None, max_length=50)
    calories: float = Field(default=0, ge=0)
    protein: float = Field(default=0, ge=0)
    fat: float = Field(default=0, ge=0)
    carbs: float = Field(default=0, ge=0)
    fiber: float | None = Field(default=None, ge=0)
    sodium: float | None = Field(default=None, ge=0)
    data_source: DataSource = DataSource.database
    food_id: UUID | None = None


class FoodItemInput(BaseModel):
    id: UUID | None = None
    name: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)
    amount_grams: float | None = Field(default=None, gt=0)
    cooking_method: str | None = Field(default=None, max_length=50)
    calories: float | None = Field(default=None, ge=0)
    protein: float | None = Field(default=None, ge=0)
    fat: float | None = Field(default=None, ge=0)
    carbs: float | None = Field(default=None, ge=0)
    fiber: float | None = Field(default=None, ge=0)
    sodium: float | None = Field(default=None, ge=0)
    data_source: DataSource | None = None
    food_id: UUID | None = None


class DietRecordCreate(BaseModel):
    """POST /diet/records 请求体（纯 CRUD，结构化输入）。

    自然语言解析路径走 ``/ai/chat`` + diet subgraph；本接口仅接收**已结构化**
    的 foods，由前端确认或手工录入。详见 ``docs/specs/shared/api-contract.md`` §5。
    """

    meal_type: MealType
    date: date_ = Field(default_factory=date_.today)
    foods: list[FoodItemInput] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_create_input(self) -> DietRecordCreate:
        if self.date > date_.today():
            raise ValueError("日期不能是未来日期")
        return self


class DietRecordUpdate(BaseModel):
    meal_type: MealType | None = None
    date: date_ | None = None
    foods: list[FoodItemInput] | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def validate_update_input(self) -> DietRecordUpdate:
        if self.date is not None and self.date > date_.today():
            raise ValueError("日期不能是未来日期")
        return self


class FoodItemResponse(BaseModel):
    id: UUID
    name: str
    amount: float
    unit: str
    amount_grams: float
    cooking_method: str | None = None
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float | None = None
    sodium: float | None = None
    data_source: DataSource
    food_id: UUID | None = None


class DietRecordResponse(BaseModel):
    id: UUID
    meal_type: MealType
    date: date_
    foods: list[FoodItemResponse]
    nutrition_summary: NutritionSummary
    created_at: datetime
    updated_at: datetime


class ParseResult(BaseModel):
    foods: list[ParsedFood]
    meal_type: MealType | None = None
    confidence: float = Field(ge=0, le=1)
    nutrition_summary: NutritionSummary = Field(default_factory=NutritionSummary)


class DailySummary(BaseModel):
    date: date_
    meals: dict[MealType, list[DietRecordResponse]]
    total_nutrition: NutritionSummary
    target_nutrition: NutritionSummary | None = None
    completion_rate: dict[str, float] = Field(default_factory=dict)


class WeeklySummary(BaseModel):
    start_date: date_
    end_date: date_
    daily_summaries: list[DailySummary]
    avg_nutrition: NutritionSummary
    total_nutrition: NutritionSummary


def week_end(start_date: date_) -> date_:
    return start_date + timedelta(days=6)


__all__ = [
    "DailySummary",
    "DataSource",
    "DietRecordCreate",
    "DietRecordResponse",
    "DietRecordUpdate",
    "FoodItemInput",
    "FoodItemResponse",
    "MealType",
    "NutritionSummary",
    "ParseResult",
    "ParsedFood",
    "WeeklySummary",
    "week_end",
]


