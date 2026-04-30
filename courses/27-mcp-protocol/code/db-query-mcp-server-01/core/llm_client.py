"""
LLM 客户端封装

封装通义千问 API 调用，提供统一的接口。
这个模块比较简单，直接提供完整实现。

类比 Java：
    类似 Spring 中封装 RestTemplate 的 Service
    @Service
    public class LLMClient {
        private final RestTemplate restTemplate;
    }
"""

from openai import OpenAI
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import sys
from functools import partial

print = partial(print, file=sys.stderr, flush=True)

print = partial(print, file=sys.stderr, flush=True)


@dataclass
class LLMConfig:
    """
    LLM 配置

    类比 Java：
        @ConfigurationProperties(prefix = "llm")
        public class LLMConfig {
            private String apiKey;
            private String baseUrl;
            private String model;
        }
    """
    api_key: str
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "qwen-plus"
    max_tokens: int = 2000
    temperature: float = 0.3  # 低温度，SQL 生成需要精确


class LLMClient:
    """
    LLM 客户端

    使用 OpenAI SDK 调用通义千问 API。
    封装了 chat 方法，支持 Function Calling。

    类比 Java：
        @Component
        public class LLMClient {
            private final OpenAiService openAiService;

            public ChatCompletionResponse chat(List<Message> messages, List<Tool> tools) {
                return openAiService.createChatCompletion(request);
            }
        }
    """

    def __init__(self, config: LLMConfig):
        """
        初始化 LLM 客户端

        参数：
            config: LLM 配置（api_key, base_url, model）

        内部创建 OpenAI 客户端实例：
            - api_key: 通义千问的 API Key
            - base_url: DashScope 兼容模式的 URL
        """
        self.config = config

        # OpenAI(api_key, base_url) - 创建客户端
        # 通义千问兼容 OpenAI 协议，所以可以用 OpenAI SDK 调用
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto"
    ) -> Any:
        """
        调用 LLM Chat API

        参数：
            messages: 消息列表
                [
                    {"role": "system", "content": "你是..."},
                    {"role": "user", "content": "查询..."},
                    {"role": "assistant", "content": None, "tool_calls": [...]},
                    {"role": "tool", "tool_call_id": "xxx", "content": "结果..."}
                ]

            tools: 工具定义列表（Function Calling 格式）
                [
                    {
                        "type": "function",
                        "function": {
                            "name": "execute_sql",
                            "description": "执行 SQL 查询",
                            "parameters": { ... }
                        }
                    }
                ]

            tool_choice: 工具选择策略
                - "auto": LLM 自动决定是否调用工具
                - "none": 禁止调用工具
                - "required": 强制调用工具

        返回：
            OpenAI ChatCompletion 响应对象
            response.choices[0].message 包含：
                - .content: 文本回复（如果不调用工具）
                - .tool_calls: 工具调用列表（如果决定调用工具）

        类比 Java：
            ChatCompletionRequest request = ChatCompletionRequest.builder()
                .model("qwen-plus")
                .messages(messages)
                .tools(tools)
                .toolChoice("auto")
                .build();

            return openAiService.createChatCompletion(request);
        """
        try:
            # 构建请求参数
            kwargs = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }

            # 如果有工具定义，添加到请求中
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice

            # 调用 API
            response = self.client.chat.completions.create(**kwargs)
            return response

        except Exception as e:
            print(f"[LLM 错误] {type(e).__name__}: {e}")
            return None

    def test_connection(self) -> Dict[str, Any]:
        """
        测试 LLM 连接是否正常

        发送一个简单的请求，验证 API Key 和网络连接。

        返回：
            {"connected": True, "model": "qwen-plus"}
            或
            {"connected": False, "error": "错误信息"}
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            return {
                "connected": True,
                "model": self.config.model
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }
