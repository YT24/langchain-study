from chains.orchestrator import AgentOrchestrator
from langchain_core.runnables import RunnableLambda


class IntentChain:
    def invoke(self, payload):
        class Result:
            intent = "query"
            reason = "test"
        return Result()


class QueryChain:
    def invoke(self, payload):
        return {
            "need_tool": True,
            "tool": "query_orders",
            "params": {"userId": "u1"},
            "answer": "",
        }


class ChatChain:
    def invoke(self, payload):
        return "chat"


class MemoryManager:
    def __init__(self):
        self.user_messages = []
        self.ai_messages = []

    def get_history(self, user_id=None):
        return "无"

    def add_user_message(self, message, user_id=None):
        self.user_messages.append((message, user_id))

    def add_ai_message(self, message, user_id=None):
        self.ai_messages.append((message, user_id))

    def increment_turn(self, user_id=None):
        return 0


class Tool:
    name = "query_orders"
    description = "查询订单"
    input_schema = None

    def invoke(self, params):
        return '[{"orderNo": "O1", "status": "shipped"}]'


def test_query_path_executes_tool_renders_locally_and_updates_memory():
    memory = MemoryManager()
    mock_llm = RunnableLambda(lambda x: "已为您查到 1 条订单")
    orchestrator = AgentOrchestrator(IntentChain(), QueryChain(), ChatChain(), memory, llm=mock_llm)
    orchestrator.set_tools([Tool()])

    response = orchestrator.process("帮我查订单", user_id="u1")

    # Response includes the LLM one-sentence summary
    assert "已为您查到" in response
    assert memory.user_messages == [("帮我查订单", "u1")]
    assert memory.ai_messages == [(response, "u1")]
