"""Prompt builders for the top-level chat agent."""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

SYSTEM_PROMPT = """你是“健康管家 AI Agent”，一个以对话为核心的个人健康管理助手。

行为边界：
- 你可以帮助用户记录饮食、理解营养、形成健康习惯、解释健康知识。
- 你不是医生；涉及诊断、用药、急症时，必须建议咨询专业医生。
- 回复要简洁、温和、具体，优先给用户下一步可执行建议。
- 如果上下文中有“用户记忆”或“知识库片段”，优先结合它们做个性化回复。
"""

INTENT_PROMPT = """请判断用户这条消息最适合交给哪个健康管理子模块处理。

可选 intent：
- diet：饮食记录、吃了什么、食物份量、拍照识别食物、自然语言饮食录入
- body：体重、围度、睡眠、运动、饮水、排便等身体数据记录或查询
- plan：健康计划、减脂/增肌/控糖目标、计划创建或调整
- suggestion：希望获得建议、洞察、每日/餐食建议
- memory：用户明确要求你记住/忘记某个偏好或事实
- general：闲聊、一般健康知识问答、无法归类

只根据当前消息判断，不要输出解释。用户消息：{message}
"""


def build_intent_messages(message: str) -> list[Any]:
    """Build messages for structured intent classification.

    SDK/API 说明：
    - 返回 LangChain Message 列表，供 ``ChatOpenAI.with_structured_output`` 的
      ``ainvoke(messages)`` 使用。
    - ``SystemMessage`` 固定模型角色和输出要求；``HumanMessage`` 承载用户输入。
    """
    return [
        SystemMessage(content="你是健康管理 Agent 的意图路由器。"),
        HumanMessage(content=INTENT_PROMPT.format(message=message)),
    ]


def build_chat_messages(
    *,
    user_message: str,
    history: list[dict[str, Any]],
    memories: list[dict[str, Any]],
    knowledge: list[dict[str, Any]],
) -> list[Any]:
    """Build final chat completion messages.

    SDK/API 说明：
    - Chat Completions 接口按 message 数组工作，每条消息有 role/content。
    - LangChain 用 ``SystemMessage`` / ``HumanMessage`` / ``AIMessage`` 包装这些
      role，最终由 ``ChatOpenAI`` 转成 DashScope OpenAI 兼容请求。
    - 返回值会被 ``get_chat_model(...).ainvoke(messages)`` 调用，响应对象的
      ``content`` 字段就是模型生成的文本。
    """
    memory_text = "\n".join(f"- {item.get('content')}" for item in memories if item.get("content"))
    knowledge_text = "\n".join(
        f"- {item.get('title', '知识片段')}：{item.get('content')}" for item in knowledge if item.get("content")
    )
    context = []
    if memory_text:
        context.append(f"用户记忆：\n{memory_text}")
    if knowledge_text:
        context.append(f"知识库片段：\n{knowledge_text}")
    system_content = SYSTEM_PROMPT
    if context:
        system_content += "\n\n可用上下文：\n" + "\n\n".join(context)

    messages: list[Any] = [SystemMessage(content=system_content)]
    for item in history[-10:]:
        role = item.get("role")
        content = item.get("content")
        if not content:
            continue
        if role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "user":
            messages.append(HumanMessage(content=content))
    messages.append(HumanMessage(content=user_message))
    return messages


__all__ = ["build_chat_messages", "build_intent_messages"]


