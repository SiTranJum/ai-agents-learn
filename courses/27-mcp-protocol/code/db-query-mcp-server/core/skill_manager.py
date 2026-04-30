"""
Skills 管理器

负责加载和管理 Skills Markdown 文件。
核心设计：三层渐进式上下文注入，减少 token 消耗。

新架构：
- skills/SKILL.md - 外层文件，frontmatter 是模块目录，正文是总体说明
- skills/references/*.md - 每个文件代表一个数据库模块，有自己的 frontmatter 和详细表结构

三层加载：
1. 第一层：SKILL.md 的 frontmatter（模块目录）- ~50 tokens
2. 第二层：SKILL.md 的正文（总体说明）- ~300 tokens
3. 第三层：references/ 下的具体模块文件 - ~800 tokens/模块
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import sys
from functools import partial

print = partial(print, file=sys.stderr, flush=True)


class SkillMetadata:
    """Skill 元数据（第一层：SKILL.md 的 frontmatter）"""
    def __init__(self, name: str, description: str, **kwargs):
        self.name = name
        self.description = description
        self.category = kwargs.get('category', '')
        self.modules = kwargs.get('modules', [])  # 可用的模块列表
        self.owner = kwargs.get('owner', '')


class ModuleMetadata:
    """模块元数据（references/*.md 的 frontmatter）"""
    def __init__(self, module: str, description: str, **kwargs):
        self.module = module
        self.description = description
        self.tables = kwargs.get('tables', [])  # 包含的表列表
        self.category = kwargs.get('category', '')


class SkillManager:
    """
    Skills 管理器

    新架构三层加载：
    - 第一层：SKILL.md frontmatter（模块目录）
    - 第二层：SKILL.md 正文（总体说明）
    - 第三层：references/*.md（具体模块详情）
    """

    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self.skill_metadata: Optional[SkillMetadata] = None  # SKILL.md 的元数据
        self.skill_content: Optional[str] = None  # SKILL.md 的正文（缓存）
        self.module_metadata: Dict[str, ModuleMetadata] = {}  # 模块元数据缓存
        self.load_skill()

    def load_skill(self):
        """
        加载 SKILL.md 的元数据（第一层）

        只解析 SKILL.md 的 YAML frontmatter，不读取正文。
        """
        skill_file = self.skills_dir / "SKILL.md"
        if not skill_file.exists():
            print(f"[Skills] SKILL.md 不存在：{skill_file}")
            return

        try:
            # 只读取并解析 YAML frontmatter
            self.skill_metadata = self._parse_frontmatter(skill_file, SkillMetadata)
            if self.skill_metadata:
                print(f"[Skills] 已加载 skill: {self.skill_metadata.name}")
                print(f"[Skills] 可用模块: {self.skill_metadata.modules}")
        except Exception as e:
            print(f"[Skills] 加载失败 {skill_file}: {e}")

    def get_skill_metadata(self) -> Optional[SkillMetadata]:
        """
        获取 skill 元数据（第一层：SKILL.md frontmatter）

        返回模块目录，用于 LLM 快速选择需要的模块。
        """
        return self.skill_metadata

    def get_skill_content(self) -> Optional[str]:
        """
        获取 skill 正文（第二层：SKILL.md 正文）

        返回总体说明、使用指南、通用规则等。
        """
        if self.skill_content:
            return self.skill_content

        skill_file = self.skills_dir / "SKILL.md"
        if not skill_file.exists():
            return None

        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 去掉 YAML frontmatter，只保留正文
            match = re.match(r'^---\s*\n.*?\n---\s*\n', content, re.DOTALL)
            if match:
                body = content[match.end():]
            else:
                body = content

            # 缓存
            self.skill_content = body
            return body

        except Exception as e:
            print(f"[Skills] 读取失败 {skill_file}: {e}")
            return None

    def get_module_detail(self, module_name: str) -> Optional[str]:
        """
        获取模块详情（第三层：references/*.md）

        参数：
            module_name: 模块名称（例如：user_module）

        返回：
            模块的完整 Markdown 内容（包含 frontmatter）
        """
        module_file = self.skills_dir / "references" / f"{module_name}.md"
        if not module_file.exists():
            return None

        try:
            with open(module_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"[Skills] 读取模块失败 {module_file}: {e}")
            return None

    def list_available_modules(self) -> List[str]:
        """
        列出所有可用的模块

        返回：
            模块名称列表（例如：['user_module', 'order_module']）
        """
        if not self.skill_metadata:
            return []
        return self.skill_metadata.modules

    def get_module_metadata(self, module_name: str) -> Optional[ModuleMetadata]:
        """
        获取模块元数据（从 references/*.md 的 frontmatter）

        参数：
            module_name: 模块名称

        返回：
            模块元数据（包含表列表等）
        """
        # 检查缓存
        if module_name in self.module_metadata:
            return self.module_metadata[module_name]

        module_file = self.skills_dir / "references" / f"{module_name}.md"
        if not module_file.exists():
            return None

        try:
            metadata = self._parse_frontmatter(module_file, ModuleMetadata)
            if metadata:
                self.module_metadata[module_name] = metadata
            return metadata
        except Exception as e:
            print(f"[Skills] 解析模块元数据失败 {module_file}: {e}")
            return None

    def _parse_frontmatter(self, file_path: Path, metadata_class) -> Optional[Any]:
        """
        解析 Markdown 文件的 YAML frontmatter

        参数：
            file_path: 文件路径
            metadata_class: 元数据类（SkillMetadata 或 ModuleMetadata）

        返回：
            元数据对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配 YAML frontmatter: ---\n...\n---
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            print(f"[Skills] {file_path.name} 缺少 YAML frontmatter")
            return None

        yaml_text = match.group(1)
        metadata_dict = self._parse_yaml(yaml_text)

        # 检查必填字段
        if metadata_class == SkillMetadata:
            if 'name' not in metadata_dict or 'description' not in metadata_dict:
                print(f"[Skills] {file_path.name} 缺少必填字段 name 或 description")
                return None
        elif metadata_class == ModuleMetadata:
            if 'module' not in metadata_dict or 'description' not in metadata_dict:
                print(f"[Skills] {file_path.name} 缺少必填字段 module 或 description")
                return None

        return metadata_class(**metadata_dict)

    def _parse_yaml(self, yaml_text: str) -> Dict[str, Any]:
        """
        简单的 YAML 解析器（避免依赖 pyyaml）

        支持：
        - key: value
        - key: [item1, item2]
        """
        result = {}
        for line in yaml_text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if ':' not in line:
                continue

            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # 处理数组：[item1, item2]
            if value.startswith('[') and value.endswith(']'):
                items = value[1:-1].split(',')
                result[key] = [item.strip() for item in items if item.strip()]
            else:
                result[key] = value

        return result

    def update_skill_modules(self, module_name: str) -> Dict[str, Any]:
        """
        更新 SKILL.md 的 modules 列表

        如果模块不在列表中，自动添加。

        参数：
            module_name: 要添加的模块名称

        返回：
            {"success": True/False, "message": "..."}
        """
        skill_file = self.skills_dir / "SKILL.md"

        if not skill_file.exists():
            return {"success": False, "error": "SKILL.md 文件不存在"}

        # 读取当前内容
        content = skill_file.read_text(encoding='utf-8')

        # 解析 frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not match:
            return {"success": False, "error": "SKILL.md 格式错误，缺少 frontmatter"}

        frontmatter_text = match.group(1)
        body = match.group(2)

        # 解析当前的 modules 列表
        modules_match = re.search(r'modules:\s*\[(.*?)\]', frontmatter_text)
        if not modules_match:
            return {"success": False, "error": "SKILL.md 中未找到 modules 字段"}

        # 解析现有模块列表
        modules_str = modules_match.group(1)
        current_modules = [m.strip() for m in modules_str.split(',') if m.strip()]

        # 检查模块是否已存在
        if module_name in current_modules:
            return {
                "success": True,
                "message": f"模块 {module_name} 已在 SKILL.md 中",
                "already_exists": True
            }

        # 添加新模块
        current_modules.append(module_name)
        new_modules_str = ', '.join(current_modules)

        # 更新 frontmatter
        new_frontmatter = re.sub(
            r'modules:\s*\[.*?\]',
            f'modules: [{new_modules_str}]',
            frontmatter_text
        )

        # 组合新内容
        new_content = f"---\n{new_frontmatter}\n---\n{body}"

        # 保存
        skill_file.write_text(new_content, encoding='utf-8')

        return {
            "success": True,
            "message": f"已将 {module_name} 添加到 SKILL.md 的 modules 列表",
            "modules": current_modules
        }

    def add_module(self, module_name: str, content: str) -> Dict[str, Any]:
        """
        添加新模块（保存为 references/*.md）

        参数：
            module_name: 模块名称
            content: 完整的 Markdown 内容（包含 frontmatter）

        返回：
            {"success": True/False, ...}
        """
        ref_dir = self.skills_dir / "references"
        module_file = ref_dir / f"{module_name}.md"

        try:
            ref_dir.mkdir(parents=True, exist_ok=True)

            with open(module_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # 清除缓存
            if module_name in self.module_metadata:
                del self.module_metadata[module_name]

            return {
                "success": True,
                "module_name": module_name,
                "file_path": str(module_file)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
