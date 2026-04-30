# 课程 01 总结

## 核心知识点

### 1. LLM 的本质
- 基于 Transformer 架构的大规模语言模型
- 通过预测下一个 token 来生成文本
- 本质是无状态的——每次调用都需要重新传入上下文

### 2. Token 和 Temperature
- **Token**：文本的最小处理单位，中文约 1.5-2 字/token
- **Temperature**：通过除法调整 logits，控制概率分布的尖锐/平坦程度
  - 值越小 → 输出越确定
  - 值越大 → 输出越随机
  - 默认 1.0，常用 0.7

### 3. OpenAI SDK 是行业标准
- 类比 JDBC：一套 API，换 base_url 就能调不同厂商的模型
- 核心方法：`client.chat.completions.create()`
- 其他模块：embeddings（向量化）、images（图片）、audio（语音）

### 4. 多轮对话的实现
- LLM 本身无记忆，"记忆"是通过每次传入完整 messages 列表实现的
- 产品层会做上下文管理：保留最近原文 + 压缩旧对话 + 检索相关记忆
- 长对话不会无脑全传，而是智能筛选

### 5. Transformer 核心原理
- **Self-Attention**：每个词能直接看到所有其他词，通过 Q/K/V 计算关联度
- **并行计算**：不像 RNN 串行，所以训练快、能做大
- **内存需求**：参数量大 + Attention 是 N² 复杂度

### 6. 模型参数
- 参数 = 模型通过训练学到的数字（权重）
- 参数量 = 模型容量上限，但实际能力还看训练数据和方法
- 微调 = 用特定领域数据继续训练，调整部分参数

## 实践成果
- ✅ 成功调用 DeepSeek API
- ✅ 理解了 temperature、max_tokens、messages 等核心参数
- ✅ 完成了多轮对话实验
- ✅ 掌握了 SDK 的基本用法

## Python 语法收获
- Python 文件顶层代码 = Java 的 main 方法
- `OpenAI()` = `new OpenAI()`，实例化对象
- `client.chat.completions.create()` = 嵌套对象的属性访问 + 方法调用
- 所有 .py 文件都能运行，但有些设计上是用来被 import 的

## 下一步
进入课程 2：Prompt Engineering（提示词工程）
- 如何写出高质量的 prompt
- System prompt vs User prompt 的最佳实践
- Few-shot learning
- 常见的 prompt 模式和技巧
