"""饮食分支 subgraph 导出。

diet 不再作为独立 Agent，而是全局 ``chat_graph`` 的一个子分支。
"""

from app.agents.diet.subgraph import build_diet_subgraph

__all__ = ["build_diet_subgraph"]
