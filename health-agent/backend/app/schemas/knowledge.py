"""RAG 知识库 Pydantic 模型。"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FoodCategory(StrEnum):
    grains = "grains"
    meat = "meat"
    vegetables = "vegetables"
    fruits = "fruits"
    dairy = "dairy"
    beverages = "beverages"
    snacks = "snacks"
    condiments = "condiments"
    nuts = "nuts"
    other = "other"


class NutritionInfo(BaseModel):
    """每 100g 或换算份量的营养信息。"""

    calories: float = Field(ge=0)
    protein: float = Field(ge=0)
    fat: float = Field(ge=0)
    carbs: float = Field(ge=0)
    fiber: float | None = Field(None, ge=0)
    sodium: float | None = Field(None, ge=0)
    sugar: float | None = Field(None, ge=0)


class PortionInfo(BaseModel):
    """常见份量换算。"""

    name: str = Field(min_length=1, max_length=20)
    weight_grams: float = Field(gt=0)


class FoodSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    aliases: list[str] = Field(default_factory=list)
    category: FoodCategory
    calories_per_100g: float = Field(ge=0)
    match_score: float = Field(ge=0, le=1)


class FoodDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    aliases: list[str] = Field(default_factory=list)
    category: FoodCategory
    nutrition_per_100g: NutritionInfo
    common_portions: list[PortionInfo] = Field(default_factory=list)
    data_source: str


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    category: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchResult(BaseModel):
    id: UUID
    title: str
    content: str
    score: float = Field(ge=0, le=1)
    metadata: dict = Field(default_factory=dict)


__all__ = [
    "FoodCategory",
    "FoodDetailResponse",
    "FoodSearchResponse",
    "KnowledgeSearchRequest",
    "KnowledgeSearchResult",
    "NutritionInfo",
    "PortionInfo",
]

