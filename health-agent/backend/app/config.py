"""应用配置模块。

通过环境变量加载配置，并使用 pydantic-settings 完成校验和类型转换。
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- 应用 ----------
    app_name: str = "health-agent-api"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # ---------- 数据库 ----------
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/health_agent"
    database_echo: bool = False
    # Supabase 免费版/基础版连接池限制为 15，保守配置：pool_size=5, max_overflow=5（峰值10）
    # 留余量给 Supabase Studio 等其他客户端
    database_pool_size: int = 5
    database_max_overflow: int = 5

    # ---------- Supabase ----------
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_jwt_algorithm: str = "HS256"
    supabase_jwt_audience: str = "authenticated"

    # ---------- DashScope（LLM）----------
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"
    llm_timeout: int = 30
    llm_max_retries: int = 3

    # ---------- Embedding ----------
    embedding_model: str = "text-embedding-v3"
    embedding_dimensions: int = 1024

    # ---------- LangGraph Checkpointer ----------
    # 控制 chat graph 是否挂 Postgres checkpointer（支持 interrupt 暂停/恢复）。
    # - 为空时：从 database_url 自动推导 psycopg DSN（去掉 +asyncpg）。
    # - 显式设置时：用该 DSN（例如 Supabase 走 5432 session-mode 直连端口）。
    checkpointer_dsn: str = ""
    # 关闭后 graph 用 MemorySaver（进程内，重启即丢），适合本地无 Postgres 的快速测试。
    checkpointer_enabled: bool = True
    checkpointer_pool_max_size: int = 3

    # ---------- 日志 ----------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ---------- 校验器 ----------
    @field_validator("app_cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, v: object) -> object:
        # 支持环境变量用逗号分隔多个 origin
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回缓存的 Settings 实例（进程内单例）。"""
    return Settings()


settings = get_settings()
