from functools import lru_cache
import os

from agent.config.loader import get as get_config


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
        self.rag_top_k_tools = get_config("rag.yml", "retrieval", "tool_top_k", default=3)
        self.rag_top_k_knowledge = get_config("rag.yml", "retrieval", "knowledge_top_k", default=3)

        # Memory RAG
        self.memory_rag_top_k = get_config("rag.yml", "memory", "top_k", default=3)
        self.memory_summary_threshold = get_config("rag.yml", "memory", "summary_threshold", default=5)
        self.memory_similarity_threshold = get_config("rag.yml", "memory", "similarity_threshold", default=0.5)
        self.memory_recent_pairs = get_config("rag.yml", "memory", "recent_pairs", default=2)

        # Tools
        self.http_timeout = get_config("tools.yml", "http", "timeout", default=30)
        self.tool_match_threshold = get_config("tools.yml", "matching", "rag_threshold", default=0.4)
        self.embedding_provider = get_config("settings.yml", "embedding", "provider", default="local")
        self.embedding_base_url = get_config("settings.yml", "embedding", "base_url", default="")
        self.embedding_api_key = os.environ.get("EMBEDDING_API_KEY", "")
        self.verbose_agent_logs = get_config("settings.yml", "agent", "verbose_logs", default=False)
        self.disable_rag = os.environ.get("DISABLE_RAG", "0") == "1"

        if not self.embedding_base_url:
            self.embedding_base_url = self.deepseek_base_url
        if not self.embedding_api_key:
            self.embedding_api_key = self.deepseek_api_key


def reset_settings_cache() -> None:
    get_settings.cache_clear()


@lru_cache
def get_settings() -> Settings:
    return Settings()
