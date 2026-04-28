import json
import logging
import os
from typing import Optional
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

# 工具启用/禁用状态持久化文件
_STATUS_FILE = os.path.join(os.path.dirname(__file__), "..", ".tool_status.json")


class ToolRegistry:
    """工具注册中心 — 管理所有 @tool 装饰的本地工具"""

    def __init__(self):
        self._tools: dict[str, StructuredTool] = {}
        self._metadata: list[dict] = []
        self._status: dict[str, bool] = self._load_status()

    def _load_status(self) -> dict[str, bool]:
        try:
            if os.path.exists(_STATUS_FILE):
                with open(_STATUS_FILE, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_status(self):
        try:
            with open(_STATUS_FILE, "w") as f:
                json.dump(self._status, f)
        except Exception as e:
            logger.warning(f"保存工具状态失败: {e}")

    def register(
        self,
        tool: StructuredTool,
        category: str = "业务工具",
        icon: str = "box",
        display_name: str = None,
        version: str = "1.0"
    ):
        """注册一个工具"""
        self._tools[tool.name] = tool

        params = []
        if hasattr(tool, "input_schema") and tool.input_schema:
            try:
                fields = tool.input_schema.model_fields
                for name, field in fields.items():
                    params.append({
                        "name": name,
                        "type": field.annotation.__name__ if hasattr(field.annotation, "__name__") else str(field.annotation),
                        "required": field.is_required(),
                        "description": field.description or ""
                    })
            except Exception:
                pass

        self._metadata.append({
            "name": tool.name,
            "displayName": display_name or tool.name,
            "description": tool.description or "",
            "category": category,
            "categoryId": hash(category) % 1000,
            "icon": icon,
            "version": version,
            "status": 1 if self._status.get(tool.name, True) else 0,
            "params": params,
        })
        logger.info(f"【ToolRegistry】注册工具: {tool.name}")

    def get_all(self) -> list[StructuredTool]:
        """获取所有启用的工具"""
        return [t for name, t in self._tools.items()
                if self._status.get(name, True)]

    def get_by_name(self, name: str) -> Optional[StructuredTool]:
        return self._tools.get(name)

    def get_metadata(self) -> list[dict]:
        """获取工具元数据（供前端展示）"""
        for meta in self._metadata:
            meta["status"] = 1 if self._status.get(meta["name"], True) else 0
        return self._metadata

    def enable(self, name: str):
        if name in self._tools:
            self._status[name] = True
            self._save_status()

    def disable(self, name: str):
        if name in self._tools:
            self._status[name] = False
            self._save_status()

    def __len__(self):
        return len(self.get_all())


_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
