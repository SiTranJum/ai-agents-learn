"""
长期记忆：持久化存储用户数据

作用：
- 存储用户档案（基本信息、目标、偏好）
- 存储历史数据（饮食记录、体重记录等）
- 跨会话保持数据（即使程序重启，数据也不会丢失）

存储方案：JSON 文件（简单、易理解）
后续课程会升级到数据库（Supabase + Milvus）
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


class LongTermMemory:
    """
    长期记忆类：持久化存储

    类比 Java：类似 DAO（Data Access Object）层
    - _load_json / _save_json 类似 JDBC 的 select / insert
    - JSON 文件类似简单的数据库表
    """

    def __init__(self, user_id: str, storage_dir: str = "./data"):
        """
        初始化长期记忆

        参数：
        - user_id: 用户 ID，用于区分不同用户的数据
        - storage_dir: 数据存储目录，默认为 ./data

        属性：
        - self.user_id: 用户 ID
        - self.storage_dir: 存储目录（Path 对象）
        - self.profile_file: 用户档案文件路径
        - self.history_file: 历史记录文件路径
        - self.profile: 用户档案数据（dict）
        - self.history: 历史记录数据（list）
        """
        self.user_id = user_id
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)  # 创建目录（如果不存在）

        # 用户数据文件路径
        self.profile_file = self.storage_dir / f"{user_id}_profile.json"
        self.history_file = self.storage_dir / f"{user_id}_history.json"

        # 加载数据到内存
        self.profile = self._load_json(self.profile_file, default={})
        self.history = self._load_json(self.history_file, default=[])

    def _load_json(self, file_path: Path, default: Any) -> Any:
        """
        从 JSON 文件加载数据

        参数：
        - file_path: 文件路径（Path 对象）
        - default: 文件不存在时的默认值

        返回：
        - 加载的数据（dict 或 list）

        作用：
        - 如果文件存在，读取并解析 JSON
        - 如果文件不存在，返回默认值
        """
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default

    def _save_json(self, file_path: Path, data: Any):
        """
        保存数据到 JSON 文件

        参数：
        - file_path: 文件路径
        - data: 要保存的数据（dict 或 list）

        作用：
        - 将数据序列化为 JSON 格式
        - 写入文件（UTF-8 编码，格式化输出）
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ========== 用户档案管理 ==========

    def update_profile(self, **kwargs):
        """
        更新用户档案

        参数：
        - **kwargs: 任意键值对，会合并到 profile 中

        示例：
        memory.update_profile(height=170, weight=70, goal="减肥")
        memory.update_profile(age=25, gender="male")

        作用：
        - 更新内存中的 profile 数据
        - 立即保存到文件
        """
        self.profile.update(kwargs)
        self._save_json(self.profile_file, self.profile)

    def get_profile(self) -> Dict[str, Any]:
        """
        获取用户档案

        返回：
        - dict: 用户档案数据

        示例：
        profile = memory.get_profile()
        print(profile["height"])  # 170
        """
        return self.profile

    def get_profile_field(self, field: str, default: Any = None) -> Any:
        """
        获取用户档案的某个字段

        参数：
        - field: 字段名
        - default: 字段不存在时的默认值

        返回：
        - 字段值，如果不存在则返回 default

        示例：
        height = memory.get_profile_field("height", 0)
        """
        return self.profile.get(field, default)

    # ========== 历史记录管理 ==========

    def add_record(self, record_type: str, data: Dict[str, Any]):
        """
        添加历史记录

        参数：
        - record_type: 记录类型（如 "meal", "weight", "exercise"）
        - data: 记录数据（dict）

        示例：
        memory.add_record("meal", {
            "time": "早餐",
            "food": "鸡蛋",
            "amount": 2,
            "calories": 140
        })

        作用：
        - 创建一条记录，包含类型、时间戳、数据
        - 添加到 history 列表
        - 立即保存到文件
        """
        record = {
            "type": record_type,
            "timestamp": datetime.now().isoformat(),  # ISO 8601 格式时间戳
            "data": data
        }
        self.history.append(record)
        self._save_json(self.history_file, self.history)

    def get_recent_records(
        self,
        record_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取最近的记录

        参数：
        - record_type: 记录类型（None 表示所有类型）
        - limit: 返回数量（默认 10 条）

        返回：
        - list: 记录列表，按时间倒序（最新的在前）

        示例：
        # 获取最近 5 条饮食记录
        meals = memory.get_recent_records("meal", limit=5)

        # 获取最近 10 条所有类型的记录
        all_records = memory.get_recent_records()
        """
        records = self.history

        # 按类型过滤
        if record_type:
            records = [r for r in records if r["type"] == record_type]

        # 返回最近的 N 条（列表末尾是最新的）
        return records[-limit:]

    def get_records_by_date(
        self,
        date: str,
        record_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取指定日期的记录

        参数：
        - date: 日期字符串（格式：YYYY-MM-DD）
        - record_type: 记录类型（None 表示所有类型）

        返回：
        - list: 该日期的记录列表

        示例：
        # 获取今天的饮食记录
        today_meals = memory.get_records_by_date("2024-03-27", "meal")
        """
        records = self.history

        # 按类型过滤
        if record_type:
            records = [r for r in records if r["type"] == record_type]

        # 按日期过滤（比较时间戳的日期部分）
        return [r for r in records if r["timestamp"].startswith(date)]

    def clear_history(self):
        """
        清空历史记录

        警告：此操作不可逆！

        用途：
        - 测试时清空数据
        - 用户要求删除所有历史记录
        """
        self.history = []
        self._save_json(self.history_file, self.history)

    # ========== 统计方法 ==========

    def get_total_records(self, record_type: Optional[str] = None) -> int:
        """
        获取记录总数

        参数：
        - record_type: 记录类型（None 表示所有类型）

        返回：
        - int: 记录数量
        """
        if record_type:
            return len([r for r in self.history if r["type"] == record_type])
        return len(self.history)


# 使用示例
if __name__ == "__main__":
    print("=== 长期记忆示例 ===\n")

    # 创建长期记忆实例
    memory = LongTermMemory(user_id="user_001", storage_dir="./data")

    # 1. 更新用户档案
    print("1. 更新用户档案")
    memory.update_profile(
        name="张三",
        age=25,
        gender="male",
        height=175,
        weight=70,
        goal="减肥",
        target_weight=65
    )
    print(f"用户档案：{memory.get_profile()}\n")

    # 2. 添加饮食记录
    print("2. 添加饮食记录")
    memory.add_record("meal", {
        "time": "早餐",
        "food": "鸡蛋",
        "amount": 2,
        "calories": 140
    })
    memory.add_record("meal", {
        "time": "午餐",
        "food": "米饭",
        "amount": 1,
        "unit": "碗",
        "calories": 200
    })
    print("已添加 2 条饮食记录\n")

    # 3. 添加体重记录
    print("3. 添加体重记录")
    memory.add_record("weight", {
        "weight": 70.5,
        "bmi": 23.0
    })
    print("已添加体重记录\n")

    # 4. 查询最近的饮食记录
    print("4. 查询最近的饮食记录")
    recent_meals = memory.get_recent_records("meal", limit=5)
    for meal in recent_meals:
        print(f"  - {meal['timestamp']}: {meal['data']}")
    print()

    # 5. 统计
    print("5. 统计信息")
    print(f"总记录数：{memory.get_total_records()}")
    print(f"饮食记录数：{memory.get_total_records('meal')}")
    print(f"体重记录数：{memory.get_total_records('weight')}")
    print()

    # 6. 查看文件
    print("6. 数据文件位置")
    print(f"用户档案：{memory.profile_file}")
    print(f"历史记录：{memory.history_file}")
