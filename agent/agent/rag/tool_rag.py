"""
Tool RAG - 工具向量化和检索
"""
import json
from typing import List, Dict, Any, Optional
from .vector_store import VectorStore


class ToolRAG:
    """工具检索增强"""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.collection_name = "tools"

    def index_tools(self, tools: List[Dict]):
        """将工具索引到向量库"""
        texts = []
        metadatas = []
        ids = []

        for tool in tools:
            tool_name = tool.get("name", "")
            tool_desc = tool.get("description", "")
            actions = tool.get("actions", [])

            if isinstance(actions, str):
                try:
                    actions = json.loads(actions)
                except:
                    actions = []

            for action in actions:
                action_name = action.get("name", "")
                action_desc = action.get("description", "")
                params = action.get("params", {})

                if isinstance(params, str):
                    try:
                        params = json.loads(params)
                    except:
                        params = {}

                # 构建完整文本
                text = f"""
工具名称：{tool_name}
工具描述：{tool_desc}
操作名称：{action_name}
操作描述：{action_desc}
参数要求：{json.dumps(params, ensure_ascii=False)}
"""
                texts.append(text.strip())
                metadatas.append({
                    "tool_name": tool_name,
                    "action_name": action_name,
                    "params": list(params.keys()) if isinstance(params, dict) else []
                })
                ids.append(f"{tool_name}_{action_name}")

        # 添加到向量库
        self.vector_store.add_texts(
            collection=self.collection_name,
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """根据用户问题检索相关工具"""
        results = self.vector_store.search(
            collection=self.collection_name,
            query=query,
            top_k=top_k
        )
        return results

    def build_tool_description_from_rag(self, query: str, top_k: int = 5) -> str:
        """从 RAG 检索构建工具描述"""
        results = self.retrieve(query, top_k)

        if not results:
            return ""

        tool_groups = {}
        for r in results:
            meta = r["metadata"]
            tool_name = meta["tool_name"]
            if tool_name not in tool_groups:
                tool_groups[tool_name] = []
            tool_groups[tool_name].append(meta)

        lines = []
        for tool_name, actions in tool_groups.items():
            lines.append(f"\n{tool_name}:")
            for action in actions:
                params_str = ", ".join(action["params"]) if action["params"] else "无"
                lines.append(f"   - {action['action_name']} (参数: {params_str})")

        return "\n可用工具：" + "".join(lines)


def init_tool_rag_from_backend(vector_store: VectorStore, backend_url: str = "http://localhost:8080") -> ToolRAG:
    """从后端加载工具并初始化 RAG"""
    import requests

    tool_rag = ToolRAG(vector_store)

    try:
        response = requests.get(f"{backend_url}/api/tools", timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            tools = result.get("data", [])
            tool_rag.index_tools(tools)
            print(f"已索引 {len(tools)} 个工具到向量库")
        else:
            print("从后端获取工具失败，使用默认工具")

    except Exception as e:
        print(f"从后端加载工具失败: {e}")

    return tool_rag
