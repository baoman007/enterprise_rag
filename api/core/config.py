#!/usr/bin/env python3
"""
系统配置
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """系统配置"""

    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/medical_rag"

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # 向量数据库配置
    VECTOR_DB_PATH: str = "./data/vector_db"

    # 嵌入模型配置
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_DEVICE: str = "cpu"

    # 大语言模型配置
    LLM_MODEL: str = "qwen2.5-7b-instruct"
    LLM_API_KEY: str = ""

    # RAG配置
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.2

    # 安全配置
    ENABLE_ANONYMIZATION: bool = True
    DATA_ENCRYPTION: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
