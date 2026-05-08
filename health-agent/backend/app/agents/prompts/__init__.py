"""Agent Prompt 模板包。

后续每个业务 Agent 的长 prompt 都应拆到本包内, 节点代码只负责调用
``build_messages(...)`` 等小函数, 避免把大段提示词写死在 graph/nodes 中。
"""

