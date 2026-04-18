from chains.orchestrator import AgentOrchestrator


class Memory:
    def get_history(self, user_id=None):
        return "无"


class EmbeddingManagerStub:
    def __init__(self):
        self.calls = []

    def embed_query(self, query):
        self.calls.append(query)
        return [0.1, 0.2]


class ToolRagStub:
    def __init__(self, embedding_manager):
        self.embedding_manager = embedding_manager
        self.received_embeddings = []

    def search_by_embedding(self, query_embedding, top_k=3):
        self.received_embeddings.append((query_embedding, top_k))
        return []


class KnowledgeRagStub:
    def __init__(self, embedding_manager):
        self.embedding_manager = embedding_manager
        self.received_embeddings = []

    def get_relevant_knowledge(self, query, threshold=0.3, query_embedding=None):
        self.received_embeddings.append((query, threshold, query_embedding))
        return ""


class MemoryRagStub:
    def __init__(self, embedding_manager):
        self.embedding_manager = embedding_manager
        self.received_embeddings = []

    def search_by_embedding(self, query_embedding, user_id, top_k=3):
        self.received_embeddings.append((query_embedding, user_id, top_k))
        return []


class TrackingOrchestrator(AgentOrchestrator):
    def __init__(self, embedding_manager):
        super().__init__(None, None, None, Memory())
        self.set_tool_rag(ToolRagStub(embedding_manager))
        self.set_knowledge_rag(KnowledgeRagStub(embedding_manager))
        self.set_memory_rag(MemoryRagStub(embedding_manager))


def test_search_all_rag_reuses_single_query_embedding():
    embedding_manager = EmbeddingManagerStub()
    orchestrator = TrackingOrchestrator(embedding_manager)

    orchestrator._search_all_rag("查订单", user_id="u1")

    assert embedding_manager.calls == ["查订单"]
    assert orchestrator._tool_rag.received_embeddings == [([0.1, 0.2], 3)]
    assert orchestrator._knowledge_rag.received_embeddings == [("查订单", 0.5, [0.1, 0.2])]


def test_get_rag_context_reuses_single_query_embedding_for_memory_rag():
    embedding_manager = EmbeddingManagerStub()
    orchestrator = TrackingOrchestrator(embedding_manager)

    orchestrator._get_rag_context("查订单", user_id="u1")

    assert embedding_manager.calls == ["查订单"]
    assert orchestrator._memory_rag.received_embeddings == [([0.1, 0.2], "u1", 3)]
