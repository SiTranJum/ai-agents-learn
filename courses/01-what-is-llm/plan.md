# 课程 01：什么是 LLM？

## 学习目标
- 理解 LLM（大语言模型）的基本概念
- 了解 LLM 的工作原理（高层次理解，不深入数学）
- 掌握如何通过 API 调用 LLM
- 理解 Token、Temperature、Max Tokens 等关键参数
- 完成第一个 LLM API 调用实践

## 知识点
1. **LLM 是什么**
   - 定义：基于 Transformer 架构的大规模语言模型
   - 能力：文本生成、理解、推理、翻译等
   - 代表产品：GPT-4、Claude、DeepSeek、通义千问等

2. **LLM 的工作原理（简化版）**
   - 输入：文本 → Token 化
   - 处理：神经网络预测下一个 Token
   - 输出：逐个生成 Token → 组合成文本
   - 关键：基于概率分布选择下一个词

3. **关键概念**
   - **Token**：文本的最小单位（中文约 1.5-2 字/token）
   - **Temperature**：控制输出随机性（0=确定，1=创造）
   - **Max Tokens**：限制输出长度
   - **System Prompt**：设定 AI 角色和行为
   - **User Prompt**：用户的输入

4. **API 调用基础**
   - 选择 LLM 提供商（本课使用 DeepSeek）
   - 获取 API Key
   - 安装 SDK
   - 发送请求、接收响应

## 实践任务
1. 注册 DeepSeek 账号，获取 API Key
2. 安装 Python 环境和 openai SDK（DeepSeek 兼容 OpenAI 格式）
3. 编写第一个 LLM 调用程序
4. 实验不同参数（temperature、max_tokens）的效果

## 预计时长
- 讲解：30 分钟
- 实践：30 分钟
- 总计：1 小时
