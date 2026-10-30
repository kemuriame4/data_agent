from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "data_agent"
    mysql_password: str = "change_me"
    mysql_database: str = "data_agent"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "product_embeddings"

    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200

    redis_host: str = "localhost"
    redis_port: int = 6379

    openai_api_key: str = ""
    openai_base_url: str = "https://api.moonshot.cn/v1"
    openai_model: str = "kimi-k3"
    llm_temperature: float = 1.0

    embedding_model: str = "BAAI/bge-m3"
    clip_model: str = "openai/clip-vit-base-patch32"

    secret_key: str = "super-secret-key"
    access_token_expire_minutes: int = 60

    max_sql_results: int = 1000
    sql_timeout_seconds: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
