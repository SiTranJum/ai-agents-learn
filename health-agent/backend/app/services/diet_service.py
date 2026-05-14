"""饮食记录 Service。"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from app.core.exceptions import NotFoundException, ValidationException
from app.db.models.diet import DietItem, DietRecord
from app.db.repositories.diet_repo import DietRepository
from app.schemas.diet import (
    DailySummary,
    DataSource,
    DietRecordResponse,
    DietRecordUpdate,
    FoodItemInput,
    FoodItemResponse,
    MealType,
    NutritionSummary,
    ParsedFood,
    WeeklySummary,
    week_end,
)
from app.services.rag_service import RagService


class DietService:
    """饮食记录 CRUD + 营养计算。

    职责边界：
    - **不做 LLM 调用**；不接受自然语言 ``input_text`` / ``image_url``；
    - 结构化 foods 的营养缺口通过 :class:`RagService` 查询知识库补全；
    - AI 自然语言入口在 ``/ai/chat`` → diet subgraph，subgraph 的工具函数
      ``save_diet_record_tool`` 最终也回调本 Service 的 :meth:`create_record_from_parsed`
      完成持久化。
    """

    def __init__(self, repo: DietRepository, rag_service: RagService) -> None:
        self.repo = repo
        self.rag_service = rag_service

    async def create_record(
        self,
        *,
        meal_type: MealType,
        foods: list[FoodItemInput],
        record_date: date,
    ) -> DietRecordResponse:
        """创建饮食记录（API 层调用，结构化入口）。

        foods 的营养信息若已完整直接落库；不完整则通过 RAG 查询补全。
        """
        if len(foods) > 20:
            raise ValidationException(
                "单条记录食物不能超过 20 项", code="DIET_RECORD_LIMIT_EXCEEDED"
            )
        parsed = [await self.food_input_to_parsed(food) for food in foods]
        return await self.create_record_from_parsed(
            meal_type=meal_type,
            foods=parsed,
            record_date=record_date,
        )

    async def create_record_from_parsed(
        self,
        *,
        meal_type: MealType,
        foods: list[ParsedFood],
        record_date: date,
    ) -> DietRecordResponse:
        """从已解析好的 ParsedFood 列表创建记录（diet subgraph 调用）。"""
        if len(foods) > 20:
            raise ValidationException(
                "单条记录食物不能超过 20 项", code="DIET_RECORD_LIMIT_EXCEEDED"
            )
        items = [self._parsed_food_to_item(food) for food in foods]
        record = await self.repo.create_record(
            meal_type=meal_type.value,
            record_date=record_date,
            items=items,
        )
        await self.repo.session.commit()
        return self._record_to_response(record)

    async def get_record(self, record_id: uuid.UUID) -> DietRecordResponse:
        record = await self.repo.get_record(record_id)
        if record is None:
            raise NotFoundException("饮食记录不存在", code="DIET_RECORD_NOT_FOUND")
        return self._record_to_response(record)

    async def list_records(
        self,
        *,
        start_date: date,
        end_date: date | None = None,
        meal_type: MealType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DietRecordResponse], int]:
        resolved_end = end_date or start_date
        if resolved_end < start_date:
            raise ValidationException("结束日期不能早于开始日期", code="DIET_INVALID_DATE")
        page_size = min(max(page_size, 1), 50)
        offset = (max(page, 1) - 1) * page_size
        records = await self.repo.list_records(
            start_date=start_date,
            end_date=resolved_end,
            meal_type=meal_type.value if meal_type else None,
            offset=offset,
            limit=page_size,
        )
        total = await self.repo.count_records(
            start_date=start_date,
            end_date=resolved_end,
            meal_type=meal_type.value if meal_type else None,
        )
        return [self._record_to_response(record) for record in records], total

    async def update_record(self, record_id: uuid.UUID, data: DietRecordUpdate) -> DietRecordResponse:
        record = await self.repo.get_record(record_id)
        if record is None:
            raise NotFoundException("饮食记录不存在", code="DIET_RECORD_NOT_FOUND")
        if data.meal_type is not None:
            record.meal_type = data.meal_type.value
        if data.date is not None:
            record.date = data.date
        if data.foods is not None:
            parsed = [await self.food_input_to_parsed(food) for food in data.foods]
            await self.repo.replace_items(record, [self._parsed_food_to_item(food) for food in parsed])
        await self.repo.session.commit()
        return self._record_to_response(record)

    async def delete_record(self, record_id: uuid.UUID) -> None:
        record = await self.repo.get_record(record_id)
        if record is not None:
            await self.repo.soft_delete(record)
            await self.repo.session.commit()

    async def upsert_record(
        self,
        *,
        meal_type: MealType,
        foods: list[FoodItemInput],
        record_date: date,
    ) -> DietRecordResponse:
        """按 date + meal_type 替换为 1 条记录（upsert 语义）。

        1. 软删除该日期+餐次的所有现有记录
        2. 创建一条新记录
        3. 返回新记录

        前端"保存饮食卡片"统一走此端点，避免同 mealType 多条记录的幽灵问题。
        """
        if len(foods) > 20:
            raise ValidationException(
                "单条记录食物不能超过 20 项", code="DIET_RECORD_LIMIT_EXCEEDED"
            )
        # 1. 软删除旧记录
        await self.repo.soft_delete_by_date_meal(record_date, meal_type.value)
        # 2. 创建新记录
        parsed = [await self.food_input_to_parsed(food) for food in foods]
        items = [self._parsed_food_to_item(food) for food in parsed]
        record = await self.repo.create_record(
            meal_type=meal_type.value,
            record_date=record_date,
            items=items,
        )
        await self.repo.session.commit()
        return self._record_to_response(record)

    async def get_daily_summary(self, target_date: date) -> DailySummary:
        records, _ = await self.list_records(start_date=target_date, end_date=target_date, page_size=50)
        meals = {meal: [] for meal in MealType}
        for record in records:
            meals[record.meal_type].append(record)
        total = self.calculate_summary_from_records(records)
        return DailySummary(
            date=target_date,
            meals=meals,
            total_nutrition=total,
            target_nutrition=None,
            completion_rate={},
        )

    async def get_weekly_summary(self, start_date: date) -> WeeklySummary:
        end_date = week_end(start_date)
        daily = [await self.get_daily_summary(start_date + timedelta(days=i)) for i in range(7)]
        total = self.calculate_summary([day.total_nutrition for day in daily])
        avg = NutritionSummary(
            total_calories=round(total.total_calories / 7, 1),
            total_protein=round(total.total_protein / 7, 1),
            total_fat=round(total.total_fat / 7, 1),
            total_carbs=round(total.total_carbs / 7, 1),
            total_fiber=round(total.total_fiber / 7, 1) if total.total_fiber is not None else None,
            total_sodium=round(total.total_sodium / 7, 1) if total.total_sodium is not None else None,
        )
        return WeeklySummary(
            start_date=start_date,
            end_date=end_date,
            daily_summaries=daily,
            avg_nutrition=avg,
            total_nutrition=total,
        )

    async def food_input_to_parsed(self, food: FoodItemInput) -> ParsedFood:
        amount_grams = food.amount_grams or self.estimate_amount_grams(food.name, food.amount, food.unit)
        if all(value is not None for value in (food.calories, food.protein, food.fat, food.carbs)):
            return ParsedFood(
                name=food.name,
                amount=food.amount,
                unit=food.unit,
                amount_grams=amount_grams,
                cooking_method=food.cooking_method,
                calories=food.calories or 0,
                protein=food.protein or 0,
                fat=food.fat or 0,
                carbs=food.carbs or 0,
                fiber=food.fiber,
                sodium=food.sodium,
                data_source=food.data_source or DataSource.database,
                food_id=food.food_id,
            )
        nutrition = await self.rag_service.lookup_nutrition(food.name, amount_grams, "g")
        return ParsedFood(
            name=food.name,
            amount=food.amount,
            unit=food.unit,
            amount_grams=amount_grams,
            cooking_method=food.cooking_method,
            calories=nutrition.calories,
            protein=nutrition.protein,
            fat=nutrition.fat,
            carbs=nutrition.carbs,
            fiber=nutrition.fiber,
            sodium=nutrition.sodium,
            data_source=DataSource.database,
            food_id=food.food_id,
        )

    @staticmethod
    def estimate_amount_grams(name: str, amount: float, unit: str) -> float:
        normalized = unit.strip().lower()
        if normalized in {"g", "克", "gram", "grams", "ml", "毫升"}:
            return amount
        if "米饭" in name and unit in {"碗", "一碗"}:
            return amount * 200
        if name in {"鸡蛋", "苹果", "梨"} and unit in {"个", "一个"}:
            return amount * (50 if name == "鸡蛋" else 200)
        if "牛奶" in name and unit in {"杯", "一杯"}:
            return amount * 250
        table = {"份": 150, "一份": 150, "盘": 300, "一盘": 300, "半份": 75, "片": 40, "一片": 40, "杯": 300, "一杯": 300}
        return amount * table.get(unit, 100)

    @staticmethod
    def calculate_summary_from_records(records: list[DietRecordResponse]) -> NutritionSummary:
        return DietService.calculate_summary([record.nutrition_summary for record in records])

    @staticmethod
    def calculate_summary(values: list[NutritionSummary]) -> NutritionSummary:
        fiber_values = [item.total_fiber for item in values if item.total_fiber is not None]
        sodium_values = [item.total_sodium for item in values if item.total_sodium is not None]
        return NutritionSummary(
            total_calories=round(sum(item.total_calories for item in values), 1),
            total_protein=round(sum(item.total_protein for item in values), 1),
            total_fat=round(sum(item.total_fat for item in values), 1),
            total_carbs=round(sum(item.total_carbs for item in values), 1),
            total_fiber=round(sum(fiber_values), 1) if fiber_values else None,
            total_sodium=round(sum(sodium_values), 1) if sodium_values else None,
        )

    @staticmethod
    def _parsed_food_to_item(food: ParsedFood) -> DietItem:
        return DietItem(
            food_name=food.name,
            amount=food.amount,
            unit=food.unit,
            amount_grams=food.amount_grams,
            cooking_method=food.cooking_method,
            calories=food.calories,
            protein=food.protein,
            fat=food.fat,
            carbs=food.carbs,
            fiber=food.fiber,
            sodium=food.sodium,
            data_source=food.data_source.value,
            food_id=food.food_id,
        )

    def _record_to_response(self, record: DietRecord) -> DietRecordResponse:
        foods = [self._item_to_response(item) for item in record.items]
        return DietRecordResponse(
            id=record.id,
            meal_type=MealType(record.meal_type),
            date=record.date,
            foods=foods,
            nutrition_summary=self._calculate_food_summary(foods),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _item_to_response(item: DietItem) -> FoodItemResponse:
        return FoodItemResponse(
            id=item.id,
            name=item.food_name,
            amount=item.amount,
            unit=item.unit,
            amount_grams=item.amount_grams,
            cooking_method=item.cooking_method,
            calories=item.calories,
            protein=item.protein,
            fat=item.fat,
            carbs=item.carbs,
            fiber=item.fiber,
            sodium=item.sodium,
            data_source=DataSource(item.data_source),
            food_id=item.food_id,
        )

    @staticmethod
    def _calculate_food_summary(foods: list[FoodItemResponse]) -> NutritionSummary:
        fiber_values = [food.fiber for food in foods if food.fiber is not None]
        sodium_values = [food.sodium for food in foods if food.sodium is not None]
        return NutritionSummary(
            total_calories=round(sum(food.calories for food in foods), 1),
            total_protein=round(sum(food.protein for food in foods), 1),
            total_fat=round(sum(food.fat for food in foods), 1),
            total_carbs=round(sum(food.carbs for food in foods), 1),
            total_fiber=round(sum(fiber_values), 1) if fiber_values else None,
            total_sodium=round(sum(sodium_values), 1) if sodium_values else None,
        )


__all__ = ["DietService"]
