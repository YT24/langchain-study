from pydantic_settings import BaseSettings
from functools import lru_cache


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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
