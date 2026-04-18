from chains.orchestrator import AgentOrchestrator


class Memory:
    def get_history(self, user_id=None):
        return "无"


class TrackingOrchestrator(AgentOrchestrator):
    def __init__(self):
        super().__init__(None, None, None, Memory())
        self.captured_user_id = None

    def _search_all_rag(self, query, user_id=None):
        self.captured_user_id = user_id
        return {"tools": [], "knowledge": "", "error": None}


def test_get_rag_context_passes_user_id_to_search_all_rag():
    orchestrator = TrackingOrchestrator()
    orchestrator._get_rag_context("查订单", user_id="u-123")
    assert orchestrator.captured_user_id == "u-123"
