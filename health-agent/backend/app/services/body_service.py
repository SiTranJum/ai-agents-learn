"""身体数据追踪 Service。"""

from __future__ import annotations

import statistics
import uuid
from collections import defaultdict
from collections.abc import Iterable
from datetime import date, time, timedelta

from app.core.exceptions import NotFoundException, ValidationException
from app.db.models.body import (
    BowelRecord,
    ExerciseRecord,
    MeasurementRecord,
    SleepRecord,
    WaterRecord,
    WeightRecord,
)
from app.db.repositories.body_repo import BodyRepository
from app.schemas.body import (
    BodyRecordType,
    BowelRecordCreate,
    BowelRecordResponse,
    BowelRecordUpdate,
    BowelStatus,
    ExerciseRecordCreate,
    ExerciseRecordResponse,
    ExerciseRecordUpdate,
    MeasurementMetric,
    MeasurementRecordCreate,
    MeasurementRecordResponse,
    MeasurementRecordUpdate,
    SleepQuality,
    SleepRecordCreate,
    SleepRecordResponse,
    SleepRecordUpdate,
    TimeRange,
    TodayRecords,
    TrendPoint,
    TrendResponse,
    TrendStatistics,
    WaterRecordCreate,
    WaterRecordResponse,
    WaterRecordUpdate,
    WeightRecordCreate,
    WeightRecordResponse,
    WeightRecordUpdate,
)

PERIOD_DAYS = {
    TimeRange.seven_days: 7,
    TimeRange.thirty_days: 30,
    TimeRange.ninety_days: 90,
    TimeRange.year: 365,
}


class BodyService:
    """身体数据 CRUD + 趋势计算 + 异常检测。

    本 Service 是纯业务层: 只处理结构化身体数据, 不做 LLM 调用。
    """

    def __init__(
        self,
        repo: BodyRepository,
        *,
        height_cm: float | None = None,
        target_weight: float | None = None,
    ) -> None:
        self.repo = repo
        self.height_cm = height_cm
        self.target_weight = target_weight

    async def create_weight(self, data: WeightRecordCreate) -> WeightRecordResponse:
        history = await self._weight_history(data.date)
        record = await self.repo.create_weight(
            WeightRecord(date=data.date, weight=round(data.weight, 1), note=data.note)
        )
        await self.repo.session.commit()
        return self._weight_response(record, anomaly_warning=self._detect_anomaly(data.weight, history))

    async def list_weight(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WeightRecordResponse], int]:
        offset, limit = self._pagination(page, page_size)
        records = await self.repo.list_weight(
            start_date=start_date,
            end_date=end_date,
            offset=offset,
            limit=limit,
        )
        total = await self.repo.count_weight(start_date=start_date, end_date=end_date)
        return [self._weight_response(record) for record in records], total

    async def update_weight(
        self,
        record_id: uuid.UUID,
        data: WeightRecordUpdate,
    ) -> WeightRecordResponse:
        record = await self.repo.get_weight(record_id)
        if record is None:
            raise NotFoundException("体重记录不存在", code="BODY_RECORD_NOT_FOUND")
        next_date = data.date or record.date
        next_weight = data.weight if data.weight is not None else record.weight
        history = await self._weight_history(next_date, exclude_id=record.id)
        if data.date is not None:
            record.date = data.date
        if data.weight is not None:
            record.weight = round(data.weight, 1)
        if data.note is not None:
            record.note = data.note
        await self.repo.session.commit()
        return self._weight_response(
            record,
            anomaly_warning=self._detect_anomaly(next_weight, history),
        )

    async def delete_weight(self, record_id: uuid.UUID) -> None:
        record = await self.repo.get_weight(record_id)
        if record is not None:
            await self.repo.soft_delete(record)
            await self.repo.session.commit()

    async def create_measurement(self, data: MeasurementRecordCreate) -> MeasurementRecordResponse:
        history = await self._measurement_history(data.date)
        record = await self.repo.create_measurement(
            MeasurementRecord(
                date=data.date,
                waist=self._round_optional(data.waist),
                hip=self._round_optional(data.hip),
                thigh=self._round_optional(data.thigh),
                arm=self._round_optional(data.arm),
                note=data.note,
            )
        )
        await self.repo.session.commit()
        return self._measurement_response(
            record,
            anomaly_warning=self._measurement_anomaly(data, history),
        )

    async def list_measurement(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[MeasurementRecordResponse], int]:
        offset, limit = self._pagination(page, page_size)
        records = await self.repo.list_measurement(
            start_date=start_date,
            end_date=end_date,
            offset=offset,
            limit=limit,
        )
        total = await self.repo.count_measurement(start_date=start_date, end_date=end_date)
        return [self._measurement_response(record) for record in records], total

    async def update_measurement(
        self,
        record_id: uuid.UUID,
        data: MeasurementRecordUpdate,
    ) -> MeasurementRecordResponse:
        record = await self.repo.get_measurement(record_id)
        if record is None:
            raise NotFoundException("围度记录不存在", code="BODY_RECORD_NOT_FOUND")
        next_values = {
            "waist": data.waist if data.waist is not None else record.waist,
            "hip": data.hip if data.hip is not None else record.hip,
            "thigh": data.thigh if data.thigh is not None else record.thigh,
            "arm": data.arm if data.arm is not None else record.arm,
        }
        if all(value is None for value in next_values.values()):
            raise ValidationException("至少需要填写一项围度", code="BODY_MEASUREMENT_EMPTY")
        if data.date is not None:
            record.date = data.date
        for field, value in next_values.items():
            setattr(record, field, self._round_optional(value))
        if data.note is not None:
            record.note = data.note
        history = await self._measurement_history(record.date, exclude_id=record.id)
        await self.repo.session.commit()
        return self._measurement_response(
            record,
            anomaly_warning=self._measurement_values_anomaly(next_values, history),
        )

    async def delete_measurement(self, record_id: uuid.UUID) -> None:
        record = await self.repo.get_measurement(record_id)
        if record is not None:
            await self.repo.soft_delete(record)
            await self.repo.session.commit()

    async def create_sleep(self, data: SleepRecordCreate) -> SleepRecordResponse:
        bed_time = self._parse_time(data.bed_time)
        wake_time = self._parse_time(data.wake_time)
        duration = self.calculate_sleep_duration(data.bed_time, data.wake_time)
        record = await self.repo.create_sleep(
            SleepRecord(
                date=data.date,
                bed_time=bed_time,
                wake_time=wake_time,
                duration_minutes=duration,
                quality=data.quality.value,
                note=data.note,
            )
        )
        await self.repo.session.commit()
        return self._sleep_response(record)

    async def list_sleep(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SleepRecordResponse], int]:
        offset, limit = self._pagination(page, page_size)
        records = await self.repo.list_sleep(
            start_date=start_date,
            end_date=end_date,
            offset=offset,
            limit=limit,
        )
        total = await self.repo.count_sleep(start_date=start_date, end_date=end_date)
        return [self._sleep_response(record) for record in records], total

    async def update_sleep(self, record_id: uuid.UUID, data: SleepRecordUpdate) -> SleepRecordResponse:
        record = await self.repo.get_sleep(record_id)
        if record is None:
            raise NotFoundException("睡眠记录不存在", code="BODY_RECORD_NOT_FOUND")
        bed_time = data.bed_time or self._format_time(record.bed_time)
        wake_time = data.wake_time or self._format_time(record.wake_time)
        if data.date is not None:
            record.date = data.date
        if data.bed_time is not None:
            record.bed_time = self._parse_time(data.bed_time)
        if data.wake_time is not None:
            record.wake_time = self._parse_time(data.wake_time)
        if data.quality is not None:
            record.quality = data.quality.value
        if data.note is not None:
            record.note = data.note
        record.duration_minutes = self.calculate_sleep_duration(bed_time, wake_time)
        await self.repo.session.commit()
        return self._sleep_response(record)

    async def delete_sleep(self, record_id: uuid.UUID) -> None:
        record = await self.repo.get_sleep(record_id)
        if record is not None:
            await self.repo.soft_delete(record)
            await self.repo.session.commit()

    async def create_exercise(self, data: ExerciseRecordCreate) -> ExerciseRecordResponse:
        calories = data.calories
        if calories is None:
            calories = self.calculate_exercise_calories(data.type, data.duration)
        record = await self.repo.create_exercise(
            ExerciseRecord(
                date=data.date,
                exercise_type=data.type,
                duration_minutes=data.duration,
                calories=calories,
                note=data.note,
            )
        )
        await self.repo.session.commit()
        return self._exercise_response(record)

    async def list_exercise(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ExerciseRecordResponse], int]:
        offset, limit = self._pagination(page, page_size)
        records = await self.repo.list_exercise(
            start_date=start_date,
            end_date=end_date,
            offset=offset,
            limit=limit,
        )
        total = await self.repo.count_exercise(start_date=start_date, end_date=end_date)
        return [self._exercise_response(record) for record in records], total

    async def update_exercise(
        self,
        record_id: uuid.UUID,
        data: ExerciseRecordUpdate,
    ) -> ExerciseRecordResponse:
        record = await self.repo.get_exercise(record_id)
        if record is None:
            raise NotFoundException("运动记录不存在", code="BODY_RECORD_NOT_FOUND")
        if data.date is not None:
            record.date = data.date
        if data.type is not None:
            record.exercise_type = data.type
        if data.duration is not None:
            record.duration_minutes = data.duration
        if data.calories is not None:
            record.calories = data.calories
        elif data.type is not None or data.duration is not None:
            record.calories = self.calculate_exercise_calories(
                record.exercise_type,
                record.duration_minutes,
            )
        if data.note is not None:
            record.note = data.note
        await self.repo.session.commit()
        return self._exercise_response(record)

    async def delete_exercise(self, record_id: uuid.UUID) -> None:
        record = await self.repo.get_exercise(record_id)
        if record is not None:
            await self.repo.soft_delete(record)
            await self.repo.session.commit()

    async def create_water(self, data: WaterRecordCreate) -> WaterRecordResponse:
        record = await self.repo.get_water_by_date(data.date)
        if record is None:
            record = await self.repo.create_water(
                WaterRecord(date=data.date, amount_ml=data.amount, target_ml=data.target)
            )
        else:
            record.amount_ml += data.amount
            record.target_ml = data.target
        await self.repo.session.commit()
        return self._water_response(record)

    async def list_water(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WaterRecordResponse], int]:
        offset, limit = self._pagination(page, page_size)
        records = await self.repo.list_water(
            start_date=start_date,
            end_date=end_date,
            offset=offset,
            limit=limit,
        )
        total = await self.repo.count_water(start_date=start_date, end_date=end_date)
        return [self._water_response(record) for record in records], total

    async def update_water(self, record_id: uuid.UUID, data: WaterRecordUpdate) -> WaterRecordResponse:
        record = await self.repo.get_water(record_id)
        if record is None:
            raise NotFoundException("饮水记录不存在", code="BODY_RECORD_NOT_FOUND")
        if data.date is not None:
            record.date = data.date
        if data.amount is not None:
            record.amount_ml = data.amount
        if data.target is not None:
            record.target_ml = data.target
        await self.repo.session.commit()
        return self._water_response(record)

    async def delete_water(self, record_id: uuid.UUID) -> None:
        record = await self.repo.get_water(record_id)
        if record is not None:
            await self.repo.soft_delete(record)
            await self.repo.session.commit()

    async def create_bowel(self, data: BowelRecordCreate) -> BowelRecordResponse:
        record = await self.repo.create_bowel(
            BowelRecord(
                date=data.date,
                time=self._parse_time(data.time),
                status=data.status.value,
                note=data.note,
            )
        )
        await self.repo.session.commit()
        return self._bowel_response(record)

    async def list_bowel(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BowelRecordResponse], int]:
        offset, limit = self._pagination(page, page_size)
        records = await self.repo.list_bowel(
            start_date=start_date,
            end_date=end_date,
            offset=offset,
            limit=limit,
        )
        total = await self.repo.count_bowel(start_date=start_date, end_date=end_date)
        return [self._bowel_response(record) for record in records], total

    async def update_bowel(self, record_id: uuid.UUID, data: BowelRecordUpdate) -> BowelRecordResponse:
        record = await self.repo.get_bowel(record_id)
        if record is None:
            raise NotFoundException("排便记录不存在", code="BODY_RECORD_NOT_FOUND")
        if data.date is not None:
            record.date = data.date
        if data.time is not None:
            record.time = self._parse_time(data.time)
        if data.status is not None:
            record.status = data.status.value
        if data.note is not None:
            record.note = data.note
        await self.repo.session.commit()
        return self._bowel_response(record)

    async def delete_bowel(self, record_id: uuid.UUID) -> None:
        record = await self.repo.get_bowel(record_id)
        if record is not None:
            await self.repo.soft_delete(record)
            await self.repo.session.commit()

    async def get_today_records(self, target_date: date) -> TodayRecords:
        return TodayRecords(
            weight=self._weight_response(record) if (record := await self.repo.latest_weight(target_date)) else None,
            measurement=self._measurement_response(record) if (record := await self.repo.latest_measurement(target_date)) else None,
            sleep=self._sleep_response(record) if (record := await self.repo.latest_sleep(target_date)) else None,
            exercise=self._exercise_response(record) if (record := await self.repo.latest_exercise(target_date)) else None,
            water=self._water_response(record) if (record := await self.repo.latest_water(target_date)) else None,
            bowel=self._bowel_response(record) if (record := await self.repo.latest_bowel(target_date)) else None,
        )

    async def get_latest(self) -> TodayRecords:
        return TodayRecords(
            weight=self._weight_response(record) if (record := await self.repo.latest_weight()) else None,
            measurement=self._measurement_response(record) if (record := await self.repo.latest_measurement()) else None,
            sleep=self._sleep_response(record) if (record := await self.repo.latest_sleep()) else None,
            exercise=self._exercise_response(record) if (record := await self.repo.latest_exercise()) else None,
            water=self._water_response(record) if (record := await self.repo.latest_water()) else None,
            bowel=self._bowel_response(record) if (record := await self.repo.latest_bowel()) else None,
        )

    async def get_trends(
        self,
        record_type: BodyRecordType,
        period: TimeRange,
        metric: MeasurementMetric | None = None,
    ) -> TrendResponse:
        start_date = date.today() - timedelta(days=PERIOD_DAYS[period] - 1)
        points = await self._trend_points(record_type, period, start_date, metric)
        return TrendResponse(
            type=record_type,
            period=period,
            metric=self._trend_metric(record_type, metric),
            data_points=points,
            statistics=self._statistics(point.value for point in points),
            target=self.target_weight if record_type == BodyRecordType.weight else None,
        )

    async def _trend_points(
        self,
        record_type: BodyRecordType,
        period: TimeRange,
        start_date: date,
        metric: MeasurementMetric | None,
    ) -> list[TrendPoint]:
        if record_type == BodyRecordType.weight:
            records = await self.repo.list_weight(start_date=start_date, limit=500, ascending=True)
            raw = [TrendPoint(date=record.date, value=record.weight) for record in records]
        elif record_type == BodyRecordType.measurement:
            selected = metric or MeasurementMetric.waist
            records = await self.repo.list_measurement(start_date=start_date, limit=500, ascending=True)
            raw = [
                TrendPoint(date=record.date, value=value)
                for record in records
                if (value := getattr(record, selected.value)) is not None
            ]
        elif record_type == BodyRecordType.sleep:
            records = await self.repo.list_sleep(start_date=start_date, limit=500, ascending=True)
            raw = [TrendPoint(date=record.date, value=round(record.duration_minutes / 60, 1)) for record in records]
        elif record_type == BodyRecordType.exercise:
            records = await self.repo.list_exercise(start_date=start_date, limit=500, ascending=True)
            raw = [TrendPoint(date=record.date, value=float(record.duration_minutes)) for record in records]
        elif record_type == BodyRecordType.water:
            records = await self.repo.list_water(start_date=start_date, limit=500, ascending=True)
            raw = [TrendPoint(date=record.date, value=float(record.amount_ml)) for record in records]
        else:
            records = await self.repo.list_bowel(start_date=start_date, limit=500, ascending=True)
            counts: dict[date, int] = defaultdict(int)
            for record in records:
                counts[record.date] += 1
            raw = [TrendPoint(date=day, value=float(count)) for day, count in sorted(counts.items())]
        if period == TimeRange.year:
            return self._weekly_average(raw)
        return raw

    async def _weight_history(self, target_date: date, exclude_id: uuid.UUID | None = None) -> list[float]:
        start_date = target_date - timedelta(days=30)
        records = await self.repo.list_weight(start_date=start_date, end_date=target_date, limit=100, ascending=True)
        return [record.weight for record in records if record.id != exclude_id]

    async def _measurement_history(
        self,
        target_date: date,
        exclude_id: uuid.UUID | None = None,
    ) -> dict[str, list[float]]:
        start_date = target_date - timedelta(days=30)
        records = await self.repo.list_measurement(start_date=start_date, end_date=target_date, limit=100, ascending=True)
        history: dict[str, list[float]] = {"waist": [], "hip": [], "thigh": [], "arm": []}
        for record in records:
            if record.id == exclude_id:
                continue
            for field in history:
                value = getattr(record, field)
                if value is not None:
                    history[field].append(value)
        return history

    def _weight_response(
        self,
        record: WeightRecord,
        *,
        anomaly_warning: str | None = None,
    ) -> WeightRecordResponse:
        return WeightRecordResponse(
            id=record.id,
            date=record.date,
            weight=round(record.weight, 1),
            bmi=self.calculate_bmi(record.weight),
            change=0.0,
            note=record.note,
            anomaly_warning=anomaly_warning,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _measurement_response(
        self,
        record: MeasurementRecord,
        *,
        anomaly_warning: str | None = None,
    ) -> MeasurementRecordResponse:
        return MeasurementRecordResponse(
            id=record.id,
            date=record.date,
            waist=record.waist,
            hip=record.hip,
            thigh=record.thigh,
            arm=record.arm,
            note=record.note,
            anomaly_warning=anomaly_warning,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _sleep_response(self, record: SleepRecord) -> SleepRecordResponse:
        return SleepRecordResponse(
            id=record.id,
            date=record.date,
            bed_time=self._format_time(record.bed_time),
            wake_time=self._format_time(record.wake_time),
            duration=record.duration_minutes,
            quality=SleepQuality(record.quality),
            note=record.note,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _exercise_response(self, record: ExerciseRecord) -> ExerciseRecordResponse:
        return ExerciseRecordResponse(
            id=record.id,
            date=record.date,
            type=record.exercise_type,
            duration=record.duration_minutes,
            calories=record.calories,
            note=record.note,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _water_response(self, record: WaterRecord) -> WaterRecordResponse:
        return WaterRecordResponse(
            id=record.id,
            date=record.date,
            amount=record.amount_ml,
            target=record.target_ml,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _bowel_response(self, record: BowelRecord) -> BowelRecordResponse:
        return BowelRecordResponse(
            id=record.id,
            date=record.date,
            time=self._format_time(record.time),
            status=BowelStatus(record.status),
            note=record.note,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def calculate_bmi(self, weight: float) -> float | None:
        if self.height_cm is None or self.height_cm <= 0:
            return None
        height_m = self.height_cm / 100
        return round(weight / (height_m * height_m), 1)

    def calculate_exercise_calories(self, exercise_type: str, duration_minutes: int) -> int:
        met = {
            "跑步": 8.0,
            "游泳": 7.0,
            "瑜伽": 3.0,
            "力量训练": 6.0,
            "骑行": 7.5,
            "篮球": 8.0,
            "羽毛球": 5.5,
            "快走": 4.0,
            "其他": 5.0,
        }.get(exercise_type, 5.0)
        weight = 65.0
        return round(met * weight * (duration_minutes / 60))

    @staticmethod
    def calculate_sleep_duration(bed_time: str, wake_time: str) -> int:
        bed = BodyService._parse_time(bed_time)
        wake = BodyService._parse_time(wake_time)
        diff = wake.hour * 60 + wake.minute - (bed.hour * 60 + bed.minute)
        if diff <= 0:
            diff += 24 * 60
        return diff

    @staticmethod
    def _parse_time(value: str) -> time:
        hour, minute = value.split(":")
        return time(hour=int(hour), minute=int(minute))

    @staticmethod
    def _format_time(value: time) -> str:
        return value.strftime("%H:%M")

    @staticmethod
    def _round_optional(value: float | None) -> float | None:
        return round(value, 1) if value is not None else None

    @staticmethod
    def _pagination(page: int, page_size: int) -> tuple[int, int]:
        limit = min(max(page_size, 1), 50)
        offset = (max(page, 1) - 1) * limit
        return offset, limit

    @staticmethod
    def _detect_anomaly(new_value: float, history: list[float]) -> str | None:
        if len(history) < 5:
            return None
        mean = statistics.mean(history)
        stdev = statistics.stdev(history)
        if stdev == 0:
            return None
        if abs(new_value - mean) > 2 * stdev:
            return f"本次记录 {new_value:.1f} 偏离近 30 天均值 {mean:.1f} 较大, 请确认是否正确"
        return None

    def _measurement_anomaly(
        self,
        data: MeasurementRecordCreate,
        history: dict[str, list[float]],
    ) -> str | None:
        values = {"waist": data.waist, "hip": data.hip, "thigh": data.thigh, "arm": data.arm}
        return self._measurement_values_anomaly(values, history)

    def _measurement_values_anomaly(
        self,
        values: dict[str, float | None],
        history: dict[str, list[float]],
    ) -> str | None:
        labels = {"waist": "腰围", "hip": "臀围", "thigh": "大腿围", "arm": "上臂围"}
        for field, value in values.items():
            if value is None:
                continue
            warning = self._detect_anomaly(value, history[field])
            if warning is not None:
                return f"{labels[field]}{warning}"
        return None

    @staticmethod
    def _statistics(values: Iterable[float]) -> TrendStatistics:
        data = list(values)
        if not data:
            return TrendStatistics()
        return TrendStatistics(
            min=round(min(data), 1),
            max=round(max(data), 1),
            average=round(sum(data) / len(data), 1),
            latest=round(data[-1], 1),
            change=round(data[-1] - data[0], 1),
        )

    @staticmethod
    def _weekly_average(points: list[TrendPoint]) -> list[TrendPoint]:
        buckets: dict[date, list[float]] = defaultdict(list)
        for point in points:
            week_start = point.date - timedelta(days=point.date.weekday())
            buckets[week_start].append(point.value)
        return [
            TrendPoint(date=week_start, value=round(sum(values) / len(values), 1))
            for week_start, values in sorted(buckets.items())
        ]

    @staticmethod
    def _trend_metric(record_type: BodyRecordType, metric: MeasurementMetric | None) -> str:
        if record_type == BodyRecordType.measurement:
            return (metric or MeasurementMetric.waist).value
        return {
            BodyRecordType.weight: "weight",
            BodyRecordType.sleep: "duration_hours",
            BodyRecordType.exercise: "duration_minutes",
            BodyRecordType.water: "amount_ml",
            BodyRecordType.bowel: "count",
        }[record_type]


__all__ = ["BodyService"]






