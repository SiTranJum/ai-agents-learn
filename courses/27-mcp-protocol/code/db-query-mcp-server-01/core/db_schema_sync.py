"""
数据库表结构同步工具

负责扫描数据库表结构，与 Skills 中的定义对比，并更新。
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re


class DatabaseSchemaSync:
    """
    数据库表结构同步器

    功能：
    1. 扫描数据库表结构
    2. 与 references/*.md 对比
    3. 生成差异报告
    4. 更新模块文件
    """

    def __init__(self, db_manager, skill_manager):
        self.db_manager = db_manager
        self.skill_manager = skill_manager

    def scan_database_tables(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        扫描数据库表结构

        参数：
            table_names: 要扫描的表名列表，None 表示扫描所有表

        返回：
            {
                "table_name": {
                    "columns": [
                        {"name": "id", "type": "BIGINT", "nullable": False, ...},
                        ...
                    ],
                    "indexes": [...],
                    "foreign_keys": [...]
                }
            }
        """
        if table_names is None:
            # 获取所有表
            result = self.db_manager.execute_query("SHOW TABLES")
            if result.get("error"):
                return {"error": True, "error_message": result["error_message"]}

            table_names = [list(row.values())[0] for row in result.get("rows", [])]

        tables_info = {}

        for table_name in table_names:
            # 获取表结构
            columns_result = self.db_manager.execute_query(f"DESCRIBE {table_name}")

            # 检查是否是错误返回（字典格式）
            if isinstance(columns_result, dict) and columns_result.get("error"):
                continue

            # 解析列信息（columns_result 是列表）
            columns = []
            for col in columns_result:
                columns.append({
                    "name": col.get("Field"),
                    "type": col.get("Type"),
                    "nullable": col.get("Null") == "YES",
                    "key": col.get("Key"),
                    "default": col.get("Default"),
                    "extra": col.get("Extra")
                })

            # 获取索引信息
            indexes_result = self.db_manager.execute_query(f"SHOW INDEX FROM {table_name}")
            indexes = []

            # 检查是否是错误返回
            if not (isinstance(indexes_result, dict) and indexes_result.get("error")):
                for idx in indexes_result:
                    indexes.append({
                        "name": idx.get("Key_name"),
                        "column": idx.get("Column_name"),
                        "unique": idx.get("Non_unique") == 0,
                        "type": idx.get("Index_type")
                    })

            tables_info[table_name] = {
                "columns": columns,
                "indexes": indexes
            }

        return tables_info

    def compare_with_module(self, module_name: str, db_tables: Dict[str, Any]) -> Dict[str, Any]:
        """
        对比数据库表结构与模块定义

        参数：
            module_name: 模块名称（例如：user_module）
            db_tables: 数据库表结构（从 scan_database_tables 获取）

        返回：
            {
                "has_changes": True/False,
                "changes": {
                    "new_tables": [...],
                    "removed_tables": [...],
                    "modified_tables": {
                        "table_name": {
                            "new_columns": [...],
                            "removed_columns": [...],
                            "modified_columns": [...]
                        }
                    }
                }
            }
        """
        # 获取模块元数据
        module_meta = self.skill_manager.get_module_metadata(module_name)
        if not module_meta:
            return {"error": True, "error_message": f"模块 {module_name} 不存在"}

        # 获取模块详情
        module_content = self.skill_manager.get_module_detail(module_name)
        if not module_content:
            return {"error": True, "error_message": f"无法读取模块 {module_name} 的内容"}

        # 解析模块中定义的表结构
        module_tables = self._parse_module_tables(module_content)

        # 对比
        changes = {
            "new_tables": [],
            "removed_tables": [],
            "modified_tables": {}
        }

        # 检查新增的表
        db_table_names = set(db_tables.keys())
        module_table_names = set(module_tables.keys())

        changes["new_tables"] = list(db_table_names - module_table_names)
        changes["removed_tables"] = list(module_table_names - db_table_names)

        # 检查修改的表
        for table_name in db_table_names & module_table_names:
            db_cols = {col["name"]: col for col in db_tables[table_name]["columns"]}
            module_cols = module_tables[table_name]

            new_cols = set(db_cols.keys()) - set(module_cols.keys())
            removed_cols = set(module_cols.keys()) - set(db_cols.keys())

            if new_cols or removed_cols:
                changes["modified_tables"][table_name] = {
                    "new_columns": list(new_cols),
                    "removed_columns": list(removed_cols)
                }

        has_changes = bool(
            changes["new_tables"] or
            changes["removed_tables"] or
            changes["modified_tables"]
        )

        return {
            "has_changes": has_changes,
            "changes": changes
        }

    def _parse_module_tables(self, module_content: str) -> Dict[str, Dict[str, Any]]:
        """
        解析模块内容中的表结构

        从 Markdown 表格中提取字段信息

        返回：
            {
                "table_name": {
                    "column_name": {"type": "...", ...},
                    ...
                }
            }
        """
        tables = {}
        current_table = None

        lines = module_content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # 匹配表名标题：### users 表详细结构
            if line.startswith('###') and '表' in line:
                # 提取表名
                match = re.match(r'###\s+(\w+)', line)
                if match:
                    current_table = match.group(1)
                    tables[current_table] = {}

            # 匹配表格行：| 字段名 | 类型 | ...
            elif current_table and line.startswith('|') and '字段名' not in line and '---' not in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    col_name = parts[1]
                    col_type = parts[2]
                    if col_name and col_type:
                        tables[current_table][col_name] = {"type": col_type}

            i += 1

        return tables

    def generate_update_report(self, module_name: str, changes: Dict[str, Any]) -> str:
        """
        生成更新报告（给用户确认）

        参数：
            module_name: 模块名称
            changes: 变更信息（从 compare_with_module 获取）

        返回：
            格式化的报告文本
        """
        if not changes.get("has_changes"):
            return f"模块 {module_name} 的表结构与数据库一致，无需更新。"

        report = f"# 模块 {module_name} 表结构变更报告\n\n"

        c = changes["changes"]

        if c["new_tables"]:
            report += "## 新增的表\n\n"
            for table in c["new_tables"]:
                report += f"- {table}\n"
            report += "\n"

        if c["removed_tables"]:
            report += "## 已删除的表\n\n"
            for table in c["removed_tables"]:
                report += f"- {table}\n"
            report += "\n"

        if c["modified_tables"]:
            report += "## 修改的表\n\n"
            for table, mods in c["modified_tables"].items():
                report += f"### {table}\n\n"
                if mods["new_columns"]:
                    report += "**新增字段**：\n"
                    for col in mods["new_columns"]:
                        report += f"- {col}\n"
                if mods["removed_columns"]:
                    report += "**删除字段**：\n"
                    for col in mods["removed_columns"]:
                        report += f"- {col}\n"
                report += "\n"

        report += "---\n\n"
        report += "请确认是否更新模块文件？\n"
        report += "- 输入 'yes' 确认更新\n"
        report += "- 输入 'no' 取消更新\n"

        return report

    def update_module_file(
        self,
        module_name: str,
        db_tables: Dict[str, Any],
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新模块文件

        参数：
            module_name: 模块名称
            db_tables: 数据库表结构
            changes: 变更信息

        返回：
            {"success": True/False, ...}
        """
        # 获取当前模块内容
        current_content = self.skill_manager.get_module_detail(module_name)
        if not current_content:
            return {"success": False, "error": "无法读取模块内容"}

        # 解析 frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', current_content, re.DOTALL)
        if not match:
            return {"success": False, "error": "模块文件格式错误"}

        frontmatter = match.group(1)
        body_start = match.end()

        # 更新 frontmatter 中的 tables 列表
        updated_tables = list(db_tables.keys())
        new_frontmatter = self._update_frontmatter_tables(frontmatter, updated_tables)

        # 重新生成表结构部分
        new_body = self._generate_module_body(module_name, db_tables)

        # 组合新内容
        new_content = f"---\n{new_frontmatter}\n---\n\n{new_body}"

        # 保存
        result = self.skill_manager.add_module(module_name, new_content)

        return result

    def _update_frontmatter_tables(self, frontmatter: str, tables: List[str]) -> str:
        """更新 frontmatter 中的 tables 字段"""
        lines = frontmatter.split('\n')
        new_lines = []

        for line in lines:
            if line.startswith('tables:'):
                new_lines.append(f"tables: [{', '.join(tables)}]")
            else:
                new_lines.append(line)

        return '\n'.join(new_lines)

    def _generate_module_body(self, module_name: str, db_tables: Dict[str, Any]) -> str:
        """
        根据数据库表结构生成模块正文

        这是一个简化版本，实际使用时可能需要保留原有的 SOP、约束等内容
        """
        body = f"# {module_name}\n\n"
        body += "## 模块概述\n\n"
        body += f"本模块包含 {len(db_tables)} 个表。\n\n"

        body += "## 表结构\n\n"

        for table_name, table_info in db_tables.items():
            body += f"### {table_name} 表详细结构\n\n"
            body += "| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |\n"
            body += "|--------|------|------|-----|--------|------|\n"

            for col in table_info["columns"]:
                nullable = "YES" if col["nullable"] else "NO"
                key = col.get("key", "")
                default = col.get("default", "")
                extra = col.get("extra", "")

                body += f"| {col['name']} | {col['type']} | {nullable} | {key} | {default} | {extra} |\n"

            body += "\n"

        return body
