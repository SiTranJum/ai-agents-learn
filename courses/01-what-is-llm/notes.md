# 课程 01 学习笔记

## Temperature 的本质

不是一个简单的"随机性开关"，而是作用在 softmax 之前的除数：

```
调整后分数 = 原始分数(logits) / temperature
```

- 值越小 → 分数差距放大 → 概率分布尖锐 → 几乎只选最高分的词 → 输出确定
- 值越大 → 分数差距缩小 → 概率分布平坦 → 各词机会均等 → 输出随机

实际应用参考：
- 数据提取/分类 → 0
- 健康建议等需要准确性的场景 → 0.3-0.5
- 日常对话 → 0.7
- 创意写作 → 0.9-1.2

## OpenAI SDK 是行业事实标准

类比 JDBC：同一套 API，换驱动连不同数据库。OpenAI SDK 换 `base_url` 就能调不同厂商的模型：

- DeepSeek: `https://api.deepseek.com`
- 通义千问: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- OpenAI: 默认值，不用写

所以学一次 SDK，所有兼容厂商都能用，不需要学各家的原生 SDK。

## SDK 调用结构

`client.chat.completions.create()` 的多层调用不是链式调用，而是嵌套对象的属性访问：

```
client              → OpenAI 实例（类比 new HttpClient()）
  .chat             → 子对象，对话相关的 API 分组
    .completions    → 子对象，补全相关
      .create()     → 真正发 HTTP 请求的方法
```

SDK 还有其他模块如 `client.embeddings`（向量化）、`client.images`（图片）等，后续课程会用到。
