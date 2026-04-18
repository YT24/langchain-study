import logging
import time
from dataclasses import dataclass
from typing import Optional

from agent.chains.chat_chain import create_chat_chain
from agent.chains.intent_chain import create_intent_chain
from agent.chains.orchestrator import AgentOrchestrator
from agent.chains.query_chain import create_query_chain
from agent.memory.conversation_memory import ConversationMemoryManager
from agent.memory.memory_rag import MemoryRAG
from agent.rag import KnowledgeRAG, ToolRAG, get_embedding_model
from agent.settings import get_settings
from agent.tools import create_all_tools

logger = logging.getLogger(__name__)


@dataclass
class CoreDependencies:
    llm: object
    memory_manager: ConversationMemoryManager
    tools: list
    intent_chain: object
    query_chain: object
    chat_chain: object


@dataclass
class OptionalDependencies:
    tool_rag: Optional[ToolRAG] = None
    knowledge_rag: Optional[KnowledgeRAG] = None
    memory_rag: Optional[MemoryRAG] = None


def create_chat_model():
    """创建 Chat 模型（DeepSeek 兼容 OpenAI API）"""
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=f"{settings.deepseek_base_url}/v1",
        temperature=settings.deepseek_temperature,
    )


def build_core_dependencies(settings) -> CoreDependencies:
    llm = create_chat_model()
    memory_manager = ConversationMemoryManager(max_token_limit=settings.max_token_limit)
    tools = create_all_tools(settings.backend_url)
    intent_chain = create_intent_chain(llm)
    query_chain = create_query_chain(llm, tools)
    chat_chain = create_chat_chain(llm)
    return CoreDependencies(
        llm=llm,
        memory_manager=memory_manager,
        tools=tools,
        intent_chain=intent_chain,
        query_chain=query_chain,
        chat_chain=chat_chain,
    )


def build_optional_dependencies(settings, tools) -> OptionalDependencies:
    if settings.disable_rag:
        logger.warning("【初始化】RAG 已通过 DISABLE_RAG 关闭")
        return OptionalDependencies()

    embedding_manager = get_embedding_model()

    tool_rag = ToolRAG(
        embedding_manager=embedding_manager,
        persist_directory=settings.chroma_persist_directory,
    )
    tool_rag.load_tools(tools)

    knowledge_rag = KnowledgeRAG(
        embedding_manager=embedding_manager,
        persist_directory=settings.chroma_persist_directory,
    )
    knowledge_rag.load_knowledge()

    memory_rag = MemoryRAG(
        embedding_manager=embedding_manager,
        persist_directory=settings.chroma_persist_directory,
    )

    return OptionalDependencies(
        tool_rag=tool_rag,
        knowledge_rag=knowledge_rag,
        memory_rag=memory_rag,
    )


def initialize_dependencies():
    """初始化所有依赖并返回编排器"""
    t0 = time.time()
    settings = get_settings()

    core = build_core_dependencies(settings)
    optional = build_optional_dependencies(settings, core.tools)

    orchestrator = AgentOrchestrator(
        intent_chain=core.intent_chain,
        query_chain=core.query_chain,
        chat_chain=core.chat_chain,
        memory_manager=core.memory_manager,
        llm=core.llm,
    )
    orchestrator.set_tools(core.tools)

    if optional.tool_rag:
        orchestrator.set_tool_rag(optional.tool_rag)
    if optional.knowledge_rag:
        orchestrator.set_knowledge_rag(optional.knowledge_rag)
    if optional.memory_rag:
        orchestrator.set_memory_rag(optional.memory_rag)
        core.memory_manager.set_memory_rag(optional.memory_rag)

    logger.info(
        "【初始化完成】耗时 %.2fs, 工具数=%s, RAG=%s",
        time.time() - t0,
        len(core.tools),
        "off" if settings.disable_rag else "on",
    )
    return orchestrator
