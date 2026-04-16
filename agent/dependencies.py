import time
from settings import get_settings
from chains.intent_chain import create_intent_chain
from chains.query_chain import create_query_chain
from chains.chat_chain import create_chat_chain
from chains.orchestrator import AgentOrchestrator
from memory.conversation_memory import ConversationMemoryManager
from memory.memory_rag import MemoryRAG
from tools import create_all_tools
from rag import get_embedding_model, ToolRAG, KnowledgeRAG


def create_chat_model():
    """创建 Chat 模型（DeepSeek 兼容 OpenAI API）"""
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=f"{settings.deepseek_base_url}/v1",
        temperature=settings.deepseek_temperature
    )


def initialize_dependencies():
    """初始化所有依赖并返回编排器"""
    t0 = time.time()
    settings = get_settings()
    print(f"[初始化] config 加载: {time.time()-t0:.2f}s")

    # 1. LLM
    t1 = time.time()
    llm = create_chat_model()
    print(f"[初始化] LLM 创建: {time.time()-t1:.2f}s (累计: {time.time()-t0:.2f}s)")

    # 2. Memory
    t2 = time.time()
    memory_manager = ConversationMemoryManager(max_token_limit=settings.max_token_limit)
    print(f"[初始化] Memory: {time.time()-t2:.2f}s (累计: {time.time()-t0:.2f}s)")

    # 3. Tools
    t3 = time.time()
    tools = create_all_tools(settings.backend_url)
    print(f"[初始化] Tools: {time.time()-t3:.2f}s (累计: {time.time()-t0:.2f}s)")
    print(f"[初始化] 加载了 {len(tools)} 个工具: {[t.name for t in tools]}")

    # 4. RAG - Embedding 模型
    t_rag0 = time.time()
    embedding_manager = get_embedding_model()
    print(f"[初始化] Embedding: {time.time()-t_rag0:.2f}s (累计: {time.time()-t0:.2f}s)")

    # 5. RAG - Tool向量检索
    t_rag1 = time.time()
    tool_rag = ToolRAG(
        embedding_manager=embedding_manager,
        persist_directory=settings.chroma_persist_directory
    )
    tool_rag.load_tools(tools)
    print(f"[初始化] ToolRAG: {time.time()-t_rag1:.2f}s (累计: {time.time()-t0:.2f}s)")

    # 6. RAG - Knowledge向量检索
    t_rag2 = time.time()
    knowledge_rag = KnowledgeRAG(
        embedding_manager=embedding_manager,
        persist_directory=settings.chroma_persist_directory
    )
    knowledge_rag.load_knowledge()
    print(f"[初始化] KnowledgeRAG: {time.time()-t_rag2:.2f}s (累计: {time.time()-t0:.2f}s)")

    # 7. MemoryRAG - 长期记忆向量检索
    t_rag3 = time.time()
    memory_rag = MemoryRAG(
        embedding_manager=embedding_manager,
        persist_directory=settings.chroma_persist_directory
    )
    print(f"[初始化] MemoryRAG: {time.time()-t_rag3:.2f}s (累计: {time.time()-t0:.2f}s)")

    # 8. Chains
    t4 = time.time()
    intent_chain = create_intent_chain(llm)
    print(f"[初始化] intent_chain: {time.time()-t4:.2f}s (累计: {time.time()-t0:.2f}s)")

    t5 = time.time()
    query_chain = create_query_chain(llm, tools, tool_rag, knowledge_rag)
    print(f"[初始化] query_chain: {time.time()-t5:.2f}s (累计: {time.time()-t0:.2f}s)")

    t6 = time.time()
    chat_chain = create_chat_chain(llm)
    print(f"[初始化] chat_chain: {time.time()-t6:.2f}s (累计: {time.time()-t0:.2f}s)")

    # 9. Orchestrator
    t7 = time.time()
    orchestrator = AgentOrchestrator(
        intent_chain=intent_chain,
        query_chain=query_chain,
        chat_chain=chat_chain,
        memory_manager=memory_manager,
        llm=llm
    )
    orchestrator.set_tools(tools)
    orchestrator.set_tool_rag(tool_rag)
    orchestrator.set_knowledge_rag(knowledge_rag)
    orchestrator.set_memory_rag(memory_rag)
    memory_manager.set_memory_rag(memory_rag)
    print(f"[初始化] Orchestrator: {time.time()-t7:.2f}s (累计: {time.time()-t0:.2f}s)")

    print(f"\n【初始化完成】总耗时: {time.time()-t0:.2f}s")
    print(f"  - 工具数: {len(tools)}")
    print(f"  - Embedding模型: {settings.embedding_model}")
    print(f"  - ChromaDB路径: {settings.chroma_persist_directory}")
    print(f"  - MemoryRAG阈值: {settings.memory_summary_threshold} 轮")

    return orchestrator
