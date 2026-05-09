"""diet subgraph 工具函数。

这些函数是 diet subgraph 节点与 Service 层之间的薄胶水。Phase 6 集成全局
chat_graph 时，这些函数可以再通过 LangChain 的 ``@tool`` 注册为 LLM 可直接
调用的工具。
"""

from __future__ import annotations

from datetime import date

from app.schemas.diet import DietRecordResponse, FoodItemInput, MealType, ParsedFood
from app.services.diet_service import DietService


async def enrich_food_tool(service: DietService, food: FoodItemInput) -> ParsedFood:
    """通过 DietService/RagService 补全单个食物营养。"""
    return await service.food_input_to_parsed(food)


async def save_diet_record_tool(
    service: DietService,
    *,
    meal_type: MealType,
    foods: list[ParsedFood],
    record_date: date,
) -> DietRecordResponse:
    """保存 subgraph 已解析完成的饮食记录。"""
    return await service.create_record_from_parsed(
        meal_type=meal_type,
        foods=foods,
        record_date=record_date,
    )


__all__ = ["enrich_food_tool", "save_diet_record_tool"]
