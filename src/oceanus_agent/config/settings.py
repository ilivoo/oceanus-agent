"""Application settings using Pydantic Settings."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MySQLSettings(BaseSettings):
    """MySQL database configuration."""
    model_config = SettingsConfigDict(env_prefix="MYSQL_")

    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "oceanus_agent"

    @property
    def url(self) -> str:
        """Get async MySQL connection URL."""
        return f"mysql+aiomysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def sync_url(self) -> str:
        """Get sync MySQL connection URL."""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class MilvusSettings(BaseSettings):
    """Milvus vector database configuration."""
    model_config = SettingsConfigDict(env_prefix="MILVUS_")

    host: str = "localhost"
    port: int = 19530
    token: Optional[str] = None

    # Collection names
    cases_collection: str = "flink_cases"
    docs_collection: str = "flink_docs"

    # Vector dimension (OpenAI text-embedding-3-small)
    vector_dim: int = 1536

    @property
    def uri(self) -> str:
        """Get Milvus connection URI."""
        return f"http://{self.host}:{self.port}"


class OpenAISettings(BaseSettings):
    """OpenAI API configuration."""
    model_config = SettingsConfigDict(env_prefix="OPENAI_")

    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # Request settings
    temperature: float = 0.1
    max_tokens: int = 2000
    timeout: int = 60


class LangSmithSettings(BaseSettings):
    """LangSmith tracing configuration."""
    model_config = SettingsConfigDict(env_prefix="LANGCHAIN_")

    tracing_v2: bool = Field(default=True, alias="LANGCHAIN_TRACING_V2")
    api_key: str = Field(default="", alias="LANGCHAIN_API_KEY")
    project: str = Field(default="oceanus-agent", alias="LANGCHAIN_PROJECT")
    endpoint: str = Field(
        default="https://api.smith.langchain.com",
        alias="LANGCHAIN_ENDPOINT"
    )


class SchedulerSettings(BaseSettings):
    """Scheduler configuration."""
    model_config = SettingsConfigDict(env_prefix="SCHEDULER_")

    interval_seconds: int = 60
    batch_size: int = 10


class KnowledgeSettings(BaseSettings):
    """Knowledge accumulation configuration."""
    model_config = SettingsConfigDict(env_prefix="KNOWLEDGE_")

    confidence_threshold: float = 0.8
    max_similar_cases: int = 3
    max_doc_snippets: int = 3


class AppSettings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(env_prefix="APP_")

    env: str = "development"
    debug: bool = False
    log_level: str = "INFO"


class Settings(BaseSettings):
    """Global application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app: AppSettings = Field(default_factory=AppSettings)
    mysql: MySQLSettings = Field(default_factory=MySQLSettings)
    milvus: MilvusSettings = Field(default_factory=MilvusSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    langsmith: LangSmithSettings = Field(default_factory=LangSmithSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    knowledge: KnowledgeSettings = Field(default_factory=KnowledgeSettings)


# Global settings instance
settings = Settings()
