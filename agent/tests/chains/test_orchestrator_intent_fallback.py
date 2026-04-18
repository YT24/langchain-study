from chains.orchestrator import AgentOrchestrator


class BrokenIntentChain:
    def invoke(self, payload):
        return "not-json"


class DummyChain:
    def invoke(self, payload):
        return "ignored"


class DictIntentChain:
    def invoke(self, payload):
        return {"intent": "query", "reason": "用户明确要求查询"}


class DummyMemory:
    def get_history(self, user_id=None):
        return "无"

    def add_user_message(self, message, user_id=None):
        pass

    def add_ai_message(self, message, user_id=None):
        pass

    def increment_turn(self, user_id=None):
        return 0


def test_broken_intent_does_not_fall_back_to_query():
    orchestrator = AgentOrchestrator(BrokenIntentChain(), DummyChain(), DummyChain(), DummyMemory())
    response = orchestrator.process("随便看看")
    assert "无法理解" in response


def test_dict_intent_routes_to_query_flow():
    orchestrator = AgentOrchestrator(DictIntentChain(), DummyChain(), DummyChain(), DummyMemory())
    response = orchestrator.process("查一下 U001 的订单")
    assert response == "ignored"
