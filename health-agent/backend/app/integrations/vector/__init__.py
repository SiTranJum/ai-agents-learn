"""向量数据库集成入口。"""

from app.integrations.vector.pgvector_client import PgVectorClient, VectorSearchResult

__all__ = ["PgVectorClient", "VectorSearchResult"]

