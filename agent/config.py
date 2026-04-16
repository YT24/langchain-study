from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # DeepSeek
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Backend
    backend_url: str = "http://localhost:8080"

    # Agent
    agent_port: int = 5001

    # Memory
    max_token_limit: int = 2000

    # RAG / Vector DB
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    chroma_persist_directory: str = os.path.join(os.path.dirname(__file__), ".chroma")
    rag_similarity_threshold: float = 0.5
    rag_top_k_tools: int = 3
    rag_top_k_knowledge: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
