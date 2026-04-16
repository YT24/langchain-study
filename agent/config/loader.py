"""配置加载器 - 从 YAML 文件读取配置"""
import os
import yaml
from typing import Any, Dict, Optional
from functools import lru_cache


class ConfigLoader:
    """YAML 配置加载器"""

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__))
        self.config_dir = config_dir
        self._cache: Dict[str, Any] = {}

    def _resolve_env_var(self, value: str) -> str:
        """解析环境变量引用 ${VAR_NAME}"""
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            return os.environ.get(var_name, "")
        return value

    def _resolve_env_vars(self, obj: Any) -> Any:
        """递归解析对象中的环境变量"""
        if isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._resolve_env_var(obj)
        return obj

    def load(self, filename: str) -> Dict[str, Any]:
        """加载 YAML 配置文件"""
        if filename in self._cache:
            return self._cache[filename]

        filepath = os.path.join(self.config_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"配置文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 解析环境变量
        config = self._resolve_env_vars(config)
        self._cache[filename] = config

        return config

    def get(self, filename: str, *keys: str, default: Any = None) -> Any:
        """获取配置值，支持嵌套键访问

        Example:
            loader.get('settings.yml', 'deepseek', 'model')
        """
        config = self.load(filename)

        for key in keys:
            if isinstance(config, dict):
                config = config.get(key)
                if config is None:
                    return default
            else:
                return default

        return config if config is not None else default


# 全局单例
_loader: Optional[ConfigLoader] = None


def get_loader() -> ConfigLoader:
    """获取全局配置加载器"""
    global _loader
    if _loader is None:
        _loader = ConfigLoader()
    return _loader


# 便捷函数
def get(filename: str, *keys: str, default: Any = None) -> Any:
    """获取配置值"""
    return get_loader().get(filename, *keys, default=default)
