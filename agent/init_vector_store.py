#!/usr/bin/env python3
"""
初始化向量库脚本
运行此脚本初始化工具和知识库到向量数据库
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.rag.vector_store import VectorStore
from agent.rag.tool_rag import init_tool_rag_from_backend
from agent.rag.knowledge_rag import KnowledgeRAG


def main():
    print("=" * 50)
    print("Agent 向量库初始化")
    print("=" * 50)

    # 初始化向量存储
    vector_store = VectorStore(persist_directory="./vector_store")
    print("[1/3] 向量存储初始化完成")

    # 初始化工具 RAG
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8080")
    try:
        tool_rag = init_tool_rag_from_backend(vector_store, backend_url)
        print(f"[2/3] 工具 RAG 初始化完成 (后端: {backend_url})")
    except Exception as e:
        print(f"[2/3] 工具 RAG 初始化失败: {e}")
        print("       将使用默认工具描述")

    # 初始化知识库
    knowledge_rag = KnowledgeRAG(vector_store)
    try:
        knowledge_rag.init_default_knowledge()
        print("[3/3] 业务知识库初始化完成")
    except Exception as e:
        print(f"[3/3] 业务知识库初始化失败: {e}")

    print("=" * 50)
    print("初始化完成！向量库保存在 ./vector_store 目录")
    print("=" * 50)


if __name__ == "__main__":
    main()
