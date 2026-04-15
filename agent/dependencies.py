import time
from config import get_settings
from chains.intent_chain import create_intent_chain
from chains.query_chain import create_query_chain
from chains.chat_chain import create_chat_chain
from chains.orchestrator import AgentOrchestrator
from memory.conversation_memory import ConversationMemoryManager
from tools import create_all_tools


def create_chat_model():
    """创建 Chat 模型（DeepSeek 兼容 OpenAI API）"""
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=f"{settings.deepseek_base_url}/v1",
        temperature=0.7
    )


def initialize_dependencies():
    """初始化所有依赖并返回编排器"""
    t0 = time.time()
    settings = get_settings()
    print(f"[初始化] config 加载: {time.time()-t0:.2f}s")

    t1 = time.time()
    llm = create_chat_model()
    print(f"[初始化] LLM 创建: {time.time()-t1:.2f}s (累计: {time.time()-t0:.2f}s)")

    t2 = time.time()
    memory_manager = ConversationMemoryManager(max_token_limit=settings.max_token_limit)
    print(f"[初始化] Memory: {time.time()-t2:.2f}s (累计: {time.time()-t0:.2f}s)")

    t3 = time.time()
    tools = create_all_tools(settings.backend_url)
    print(f"[初始化] Tools: {time.time()-t3:.2f}s (累计: {time.time()-t0:.2f}s)")
    print(f"[初始化] 加载了 {len(tools)} 个工具: {[t.name for t in tools]}")

    t4 = time.time()
    intent_chain = create_intent_chain(llm)
    print(f"[初始化] intent_chain: {time.time()-t4:.2f}s (累计: {time.time()-t0:.2f}s)")

    t5 = time.time()
    query_chain = create_query_chain(llm, tools, memory_manager.memory)
    print(f"[初始化] query_chain: {time.time()-t5:.2f}s (累计: {time.time()-t0:.2f}s)")

    t6 = time.time()
    chat_chain = create_chat_chain(llm)
    print(f"[初始化] chat_chain: {time.time()-t6:.2f}s (累计: {time.time()-t0:.2f}s)")

    t7 = time.time()
    orchestrator = AgentOrchestrator(
        intent_chain=intent_chain,
        query_chain=query_chain,
        chat_chain=chat_chain,
        memory_manager=memory_manager,
        llm=llm
    )
    orchestrator.set_tools(tools)
    print(f"[初始化] Orchestrator: {time.time()-t7:.2f}s (累计: {time.time()-t0:.2f}s)")

    return orchestrator
