"""
Agent Harness - 核心模块

实现三层渐进式上下文注入的 Agent 循环：
1. 第一阶段：LLM 只看到 SKILL.md frontmatter（模块目录），选择需要的模块
2. 第二阶段：加载 SKILL.md 正文（总体说明），LLM 生成 SQL 并执行
3. 第三阶段：按需加载 references/*.md（具体模块详情）
"""

import json
from typing import Dict, List, Any, Any
from .skill_manager import SkillManager
from .db_manager import DatabaseManager
from .llm_client import LLMClient
from .db_schema_sync import DatabaseSchemaSync
import sys
from functools import partial

print = partial(print, file=sys.stderr, flush=True)


class AgentHarness:
    """Agent 执行器 - 三层渐进式加载"""

    def __init__(
        self,
        skill_manager: SkillManager,
        db_manager: DatabaseManager,
        llm_client: LLMClient,
        max_iterations: int = 10
    ):
        self.skill_manager = skill_manager
        self.db_manager = db_manager
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.schema_sync = DatabaseSchemaSync(db_manager, skill_manager)

    def query_database(self, user_question: str) -> str:
        """处理数据库查询请求（MCP 工具入口）"""
        print(f"\n{'='*60}")
        print(f"[用户问题] {user_question}")
        print(f"{'='*60}\n")

        # 第一阶段：选择模块（只看 SKILL.md frontmatter）
        print("[阶段 1] 选择相关的模块（只加载模块目录）...")
        selected_modules = self._stage1_select_modules(user_question)
        print(f"  选中的模块: {selected_modules}\n")

        # 第二阶段：生成和执行 SQL（加载 SKILL.md 正文 + 按需加载模块详情）
        print("[阶段 2] 生成 SQL 并执行（加载总体说明 + 按需加载模块详情）...")
        result = self._stage2_execute_query(user_question, selected_modules)

        return result

    def _stage1_select_modules(self, user_question: str) -> List[str]:
        """
        第一阶段：让 LLM 从模块目录中选择需要的模块

        这一轮只提供 SKILL.md 的 frontmatter（模块目录），成本极低（~50 tokens）。
        """
        skill_meta = self.skill_manager.get_skill_metadata()
        if not skill_meta:
            print("  [警告] 未找到 skill 元数据")
            return []

        # 构建模块目录
        modules_summary = "# 可用的数据库模块\n\n"
        for i, module_name in enumerate(skill_meta.modules, 1):
            # 尝试获取模块元数据（如果已缓存）
            module_meta = self.skill_manager.get_module_metadata(module_name)
            if module_meta:
                desc = module_meta.description
            else:
                desc = module_name

            modules_summary += f"{i}. **{module_name}** - {desc}\n"

        system_prompt = f"""你是数据库查询助手。

你的任务：
1. 理解用户的查询需求
2. 从下面的模块列表中，选择最相关的模块
3. 只回复模块名称，如果需要多个，用逗号分隔
4. 不要解释原因，不要输出其他内容

{modules_summary}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]

        response = self.llm_client.chat(messages)
        if response is None:
            print("  [警告] LLM 调用失败，默认返回所有模块")
            return skill_meta.modules

        content = response.choices[0].message.content or ""
        print(f"  [LLM 选择] {content}")

        # 解析模块名称
        all_modules = set(skill_meta.modules)
        selected = []

        # 支持逗号分隔
        for part in content.replace('，', ',').split(','):
            module_name = part.strip()
            if module_name in all_modules:
                selected.append(module_name)

        # 如果 LLM 没有正确返回，尝试简单匹配
        if not selected:
            for module_name in all_modules:
                if module_name in content:
                    selected.append(module_name)

        # 兜底：返回所有模块
        if not selected:
            print("  [警告] 无法解析 LLM 返回，默认使用所有模块")
            selected = skill_meta.modules

        return selected

    def _stage2_execute_query(
        self,
        user_question: str,
        selected_modules: List[str]
    ) -> str:
        """
        第二阶段：加载 SKILL.md 正文，让 LLM 生成 SQL 并执行

        这一阶段是真正的 Agent 循环：
        LLM 思考 → 调用 execute_sql 工具 → 观察结果 → 生成最终答案

        如果 SKILL.md 中提示需要更多信息，LLM 可以调用 load_module 工具
        进入第三阶段。
        """
        # 加载 SKILL.md 正文（第二层）
        skill_content = self.skill_manager.get_skill_content()
        if not skill_content:
            return "未找到 skill 内容，无法生成 SQL。"

        system_prompt = self._build_stage2_system_prompt(skill_content, selected_modules)
        tools = self._define_tools(selected_modules)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]

        for iteration in range(self.max_iterations):
            print(f"  [迭代 {iteration + 1}]")
            response = self.llm_client.chat(messages, tools)
            if response is None:
                return "LLM 调用失败，无法完成查询。"

            message = response.choices[0].message

            # 情况 1：LLM 决定调用工具
            if message.tool_calls:
                print("    LLM 决定调用工具")
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    # 执行工具
                    if tool_name == "execute_sql":
                        result = self._execute_sql_tool(args)
                    elif tool_name == "load_module":
                        result = self._load_module_tool(args)
                    else:
                        result = {"error": True, "error_message": f"未知工具: {tool_name}"}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False, indent=2)
                    })

            # 情况 2：LLM 直接给出最终回复
            else:
                print("    LLM 生成最终答案")
                return message.content or "查询完成，但 LLM 没有返回内容。"

        return "达到最大迭代次数，未能完成查询。"

    def _execute_sql_tool(self, args: Dict) -> Dict:
        """执行 SQL 工具"""
        sql = args["sql"]
        params = args.get("params")

        print(f"    [SQL] {sql}")
        if params:
            print(f"    [参数] {params}")

        # SQL 安全检查
        sql_upper = sql.strip().upper()
        if sql_upper.startswith(("DROP", "TRUNCATE", "ALTER")):
            return {"error": True, "error_message": "禁止执行危险 SQL 操作"}
        elif sql_upper.startswith(("UPDATE", "DELETE", "INSERT")):
            return {"error": True, "error_message": "UPDATE/DELETE/INSERT 需要用户确认，当前版本暂不支持"}

        # 执行查询
        return self.db_manager.execute_query(
            sql,
            tuple(params) if params else None
        )

    def _load_module_tool(self, args: Dict) -> Dict:
        """
        加载模块详情工具（第三层）

        只有当 SKILL.md 中明确提示需要更多信息时，LLM 才会调用这个工具。
        """
        module_name = args["module_name"]

        print(f"    [加载模块] {module_name}")

        content = self.skill_manager.get_module_detail(module_name)
        if content:
            return {
                "success": True,
                "module_name": module_name,
                "content": content
            }
        else:
            return {
                "error": True,
                "error_message": f"模块不存在: {module_name}"
            }

    def _build_stage2_system_prompt(
        self,
        skill_content: str,
        selected_modules: List[str]
    ) -> str:
        """
        构建第二阶段的 System Prompt

        这一轮加载 SKILL.md 正文（总体说明、使用指南、通用规则）。
        如果需要更多信息（完整表结构），可以调用 load_module 工具。
        """
        prompt = """你是数据库查询助手 Agent。

你的任务：
1. 理解用户的查询需求
2. 根据提供的信息，生成精准的 SQL 语句
3. 调用 execute_sql 工具执行 SQL
4. 将查询结果用自然语言返回给用户

注意：
- 必须先调用 execute_sql 工具获取真实数据，然后才能回答
- 如果当前信息不足以生成 SQL，可以调用 load_module 工具加载模块详情
- 如果用户问题无法回答，要诚实说明原因

# Skill 总体说明

"""

        prompt += skill_content + "\n\n"

        prompt += f"""
# 当前选中的模块

{', '.join(selected_modules)}

如果需要查看某个模块的详细表结构，可以调用 load_module 工具：

```
load_module(module_name="user_module")
```

这将返回该模块的完整信息，包括：
- 详细的表结构（字段、类型、索引）
- SOP（标准操作流程）
- 约束条件
- 示例查询
"""

        return prompt

    def _define_tools(self, selected_modules: List[str]) -> List[Dict]:
        """
        定义工具（Function Calling 格式）

        包含两个工具：
        1. execute_sql - 执行 SQL 查询
        2. load_module - 加载模块详情（第三层）
        """
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_sql",
                    "description": "执行 SQL 查询并返回结果。只支持 SELECT 查询。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL 语句（支持参数化查询，使用 %s 占位符）"
                            },
                            "params": {
                                "type": "array",
                                "description": "参数列表（可选，对应 SQL 中的 %s 占位符）",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["sql"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "load_module",
                    "description": "加载模块的详细信息（完整表结构、SOP、约束条件等）。只有当当前信息不足以生成 SQL 时才调用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "module_name": {
                                "type": "string",
                                "description": f"模块名称，可选值：{', '.join(selected_modules)}"
                            }
                        },
                        "required": ["module_name"]
                    }
                }
            }
        ]

        return tools

    # ============ 表结构同步功能 ============

    def sync_schema_check(self, module_name: str, table_names: List[str]) -> str:
        """
        检查表结构变更（MCP 工具入口）

        扫描指定表并与模块定义对比，返回差异报告（不执行更新）。

        参数：
            module_name: 模块名称（例如：user_module）
            table_names: 要检查的表名列表

        返回：
            差异报告文本
        """
        print(f"\n{'='*60}")
        print(f"[检查表结构] 模块: {module_name}, 表: {table_names}")
        print(f"{'='*60}\n")

        # 扫描数据库表结构
        db_tables = self.schema_sync.scan_database_tables(table_names)
        if isinstance(db_tables, dict) and db_tables.get("error"):
            return f"扫描失败: {db_tables.get('error_message')}"

        # 对比差异
        changes = self.schema_sync.compare_with_module(module_name, db_tables)
        if isinstance(changes, dict) and changes.get("error"):
            return f"对比失败: {changes.get('error_message')}"

        # 生成报告
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
        report += "如需应用更新，请调用 sync_schema_apply 工具。\n"

        return report

    def sync_schema_apply(self, module_name: str, table_names: List[str]) -> str:
        """
        应用表结构更新（MCP 工具入口）

        将数据库表结构同步到模块文件。如果模块不存在，自动创建。

        参数：
            module_name: 模块名称
            table_names: 要更新的表名列表

        返回：
            更新结果
        """
        print(f"\n{'='*60}")
        print(f"[应用更新] 模块: {module_name}, 表: {table_names}")
        print(f"{'='*60}\n")

        # 扫描最新的表结构
        db_tables = self.schema_sync.scan_database_tables(table_names)
        if isinstance(db_tables, dict) and db_tables.get("error"):
            return f"扫描失败: {db_tables.get('error_message')}"

        # 检查模块是否存在
        module_meta = self.skill_manager.get_module_metadata(module_name)

        if not module_meta:
            # 模块不存在，自动创建
            print(f"  模块 {module_name} 不存在，自动创建...")

            # 生成新模块内容
            module_content = self._generate_new_module(module_name, db_tables)

            # 保存模块文件
            result = self.skill_manager.add_module(module_name, module_content)

            if result.get("success"):
                # 自动更新 SKILL.md
                skill_result = self.skill_manager.update_skill_modules(module_name)
                msg = f"新模块 {module_name} 已创建。\n文件路径: {result.get('file_path', '')}"
                if skill_result.get("success"):
                    msg += f"\nSKILL.md 已自动更新：{skill_result.get('message', '')}"
                return msg
            else:
                return f"创建失败: {result.get('error', '未知错误')}"

        # 模块已存在，对比差异
        changes = self.schema_sync.compare_with_module(module_name, db_tables)
        if isinstance(changes, dict) and changes.get("error"):
            return f"对比失败: {changes.get('error_message')}"

        # 更新模块文件
        result = self.schema_sync.update_module_file(module_name, db_tables, changes)

        if result.get("success"):
            return f"✓ 模块 {module_name} 已成功更新。\n文件路径: {result.get('file_path', '')}"
        else:
            return f"更新失败: {result.get('error', '未知错误')}"

    def _generate_new_module(self, module_name: str, db_tables: Dict[str, Any]) -> str:
        """
        生成新模块的内容

        参数：
            module_name: 模块名称
            db_tables: 数据库表结构

        返回：
            模块文件内容（Markdown 格式）
        """
        # 生成 frontmatter
        table_names = list(db_tables.keys())
        frontmatter = f"""---
module: {module_name}
description: {module_name.replace('_', ' ').title()} - 自动生成
tables: {table_names}
category: 自动生成模块
---"""

        # 生成正文
        body = f"\n\n# {module_name}\n\n"
        body += "## 模块概述\n\n"
        body += f"本模块包含 {len(db_tables)} 个表，由数据库表结构自动生成。\n\n"
        body += "## 表结构\n\n"

        for table_name, table_info in db_tables.items():
            body += f"### {table_name} 表详细结构\n\n"
            body += "| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |\n"
            body += "|--------|------|------|-----|--------|------|\n"

            for col in table_info["columns"]:
                nullable = "YES" if col["nullable"] else "NO"
                key = col.get("key", "")
                default = str(col.get("default", ""))
                extra = col.get("extra", "")

                body += f"| {col['name']} | {col['type']} | {nullable} | {key} | {default} | {extra} |\n"

            body += "\n"

        return frontmatter + body

