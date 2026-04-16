from functools import lru_cache
import os

from config.loader import get as get_config


def _setup_hf_cache():
    """设置 HuggingFace 模型缓存路径"""
    hf_home = os.environ.get("HF_HOME")
    if not hf_home:
        hf_cache = os.path.join(os.path.dirname(__file__), ".hf_cache")
        os.environ["HF_HOME"] = hf_cache


_setup_hf_cache()


class Settings:
    """从 YAML 配置文件读取的设置"""

    def __init__(self):
        self._load_config()

    def _load_config(self):
        """加载所有配置"""
        base_dir = os.path.dirname(__file__)

        # DeepSeek
        self.deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.deepseek_base_url = get_config("settings.yml", "deepseek", "base_url", default="https://api.deepseek.com")
        self.deepseek_model = get_config("settings.yml", "deepseek", "model", default="deepseek-chat")
        self.deepseek_temperature = get_config("settings.yml", "deepseek", "temperature", default=0.7)

        # Backend
        self.backend_url = get_config("settings.yml", "backend", "url", default="http://localhost:8080")
        self.backend_timeout = get_config("settings.yml", "backend", "timeout", default=30)

        # Agent
        self.agent_port = get_config("settings.yml", "agent", "port", default=5001)

        # Memory
        self.max_token_limit = get_config("settings.yml", "memory", "max_token_limit", default=2000)

        # RAG / Vector DB
        self.embedding_model = get_config("rag.yml", "embedding", "model", default="BAAI/bge-small-zh-v1.5")
        self.embedding_dimension = get_config("rag.yml", "embedding", "dimension", default=512)
        self.chroma_persist_directory = os.path.join(base_dir, get_config("rag.yml", "chroma", "persist_directory", default=".chroma"))
        self.rag_similarity_threshold = get_config("rag.yml", "retrieval", "tool_similarity_threshold", default=0.5)
        self.rag_tool_match_threshold = get_config("rag.yml", "retrieval", "tool_match_threshold", default=0.4)
        self.rag_top_k_tools = get_config("rag.yml", "retrieval", "tool_top_k", default=3)
        self.rag_top_k_knowledge = get_config("rag.yml", "retrieval", "knowledge_top_k", default=3)

        # Tools
        self.http_timeout = get_config("tools.yml", "http", "timeout", default=30)


@lru_cache
def get_settings() -> Settings:
    return Settings()
