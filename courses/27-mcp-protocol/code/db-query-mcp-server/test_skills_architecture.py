"""
测试新的 Skills 架构

验证三层加载是否正常工作
"""

from core import SkillManager

print("="*60)
print("测试新的 Skills 架构")
print("="*60)

# 初始化 SkillManager
sm = SkillManager('./skills')

print("\n[第一层] SKILL.md frontmatter（模块目录）")
print("-"*60)
meta = sm.get_skill_metadata()
if meta:
    print(f"Skill 名称: {meta.name}")
    print(f"描述: {meta.description}")
    print(f"可用模块: {meta.modules}")
    print(f"Token 估算: ~50 tokens")
else:
    print("❌ 未找到 skill 元数据")

print("\n[第二层] SKILL.md 正文（总体说明）")
print("-"*60)
content = sm.get_skill_content()
if content:
    print(f"内容长度: {len(content)} 字符")
    print(f"Token 估算: ~{len(content.split())} words")
    print(f"\n前 300 字符预览:")
    print(content[:300] + "...")
else:
    print("❌ 未找到 skill 内容")

print("\n[第三层] 模块详情（references/*.md）")
print("-"*60)
modules = sm.list_available_modules()
print(f"可用模块: {modules}")

if modules:
    for module_name in modules:
        print(f"\n--- {module_name} ---")

        # 获取模块元数据
        module_meta = sm.get_module_metadata(module_name)
        if module_meta:
            print(f"  描述: {module_meta.description}")
            print(f"  包含的表: {module_meta.tables}")

        # 获取模块详情
        detail = sm.get_module_detail(module_name)
        if detail:
            print(f"  内容长度: {len(detail)} 字符")
            print(f"  Token 估算: ~{len(detail.split())} words")
        else:
            print(f"  ❌ 未找到模块详情")

print("\n" + "="*60)
print("测试完成")
print("="*60)

# 总结
print("\n[Token 消耗总结]")
print("-"*60)
if meta and content and modules:
    layer1_tokens = 50
    layer2_tokens = len(content.split())
    layer3_tokens = sum(
        len(sm.get_module_detail(m).split())
        for m in modules
        if sm.get_module_detail(m)
    )

    print(f"第一层（模块目录）: ~{layer1_tokens} tokens")
    print(f"第二层（总体说明）: ~{layer2_tokens} tokens")
    print(f"第三层（所有模块）: ~{layer3_tokens} tokens")
    print(f"\n如果只加载 1 个模块:")
    avg_module_tokens = layer3_tokens // len(modules) if modules else 0
    print(f"  总消耗: ~{layer1_tokens + layer2_tokens + avg_module_tokens} tokens")
    print(f"\n传统方式（一次性加载）: ~5000+ tokens")
    print(f"节省: ~{100 - (layer1_tokens + layer2_tokens + avg_module_tokens) * 100 // 5000}%")
