from app.agents.chat.graph import build_chat_agent

graph = build_chat_agent()

# 打印 ASCII 结构
print(graph.get_graph().draw_ascii())

# 展开子图（xray=True 会把 diet 子图内部节点也画出来）
print(graph.get_graph(xray=True).draw_ascii())

# 生成 Mermaid（可贴到 markdown 渲染）
print(graph.get_graph(xray=True).draw_mermaid())

# 生成 PNG
graph.get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")