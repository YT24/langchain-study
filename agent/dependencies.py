from langchain_community.chat_models import ChatOpenAI
from config import get_settings
from chains.intent_chain import create_intent_chain
from chains.query_chain import create_query_chain
from chains.chat_chain import create_chat_chain
from chains.orchestrator import AgentOrchestrator
from memory.conversation_memory import ConversationMemoryManager
from tools import create_all_tools


def create_chat_model():
    """创建 Chat 模型（支持 DeepSeek 或 OpenAI 兼容接口）"""
    settings = get_settings()

    # 优先使用 langchain-deepseek
    try:
        from langchain_deepseek import ChatDeepSeek
        return ChatDeepSeek(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=0.7
        )
    except ImportError:
        # 降级到 ChatOpenAI（兼容 DeepSeek API）
        return ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=f"{settings.deepseek_base_url}/v1",
            temperature=0.7
        )


def initialize_dependencies():
    """初始化所有依赖并返回编排器"""
    settings = get_settings()

    # 1. 初始化 LLM
    llm = create_chat_model()

    # 2. 初始化 Memory
    memory_manager = ConversationMemoryManager(max_token_limit=settings.max_token_limit)

    # 3. 初始化 Tools
    tools = create_all_tools(settings.backend_url)

    # 4. 初始化 Chains
    intent_chain = create_intent_chain(llm)
    query_chain = create_query_chain(llm, tools, memory_manager.memory)
    chat_chain = create_chat_chain(llm)

    # 5. 创建 Orchestrator
    orchestrator = AgentOrchestrator(
        intent_chain=intent_chain,
        query_chain=query_chain,
        chat_chain=chat_chain,
        memory_manager=memory_manager
    )

    return orchestrator
