# Agent 执行流程加固 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提升 agent 查询执行链路的正确性、稳定性、性能和可维护性，减少误判、误调用和上下文丢失问题。

**Architecture:** 在保留现有 Flask + Orchestrator 主体结构的前提下，按“结构化决策、参数校验、稳定工具执行、分层记忆、受控日志”五个方向增量改造。优先修复 query 决策与记忆策略中的高风险点，再补齐性能与初始化改进，避免一次性大重构带来额外不确定性。

**Tech Stack:** Python 3.10+, Flask 3.x, LangChain, Pydantic v2, requests, ChromaDB, sentence-transformers, pytest

---

## 文件结构

```
agent/
├── server.py                         # Flask 接口入口；请求参数和日志入口
├── dependencies.py                  # 依赖初始化、分阶段加载入口
├── settings.py                      # 运行时配置读取
│
├── chains/
│   ├── intent_chain.py              # 意图识别链
│   ├── query_chain.py               # 查询决策链
│   ├── chat_chain.py                # 闲聊链
│   ├── orchestrator.py              # 主执行流程、RAG、工具编排、记忆更新
│   └── validators.py                # 新建：query 决策与工具参数校验逻辑
│
├── schemas/
│   ├── intent.py                    # 意图结构
│   └── tool_decision.py             # 新建：query 决策结构化 schema
│
├── prompts/
│   └── __init__.py                  # Prompt 装配入口
│
├── config/
│   ├── prompts.yml                  # prompt 模板
│   ├── settings.yml                 # 运行配置
│   ├── rag.yml                      # RAG/Memory 配置
│   └── tools.yml                    # 工具匹配配置
│
├── memory/
│   ├── conversation_memory.py       # 短期记忆和轮次管理
│   └── memory_rag.py                # 长期记忆存储与检索
│
├── rag/
│   ├── embeddings.py                # embedding provider 管理
│   ├── tool_rag.py                  # 工具检索
│   └── knowledge_rag.py             # 知识检索
│
├── tools/
│   ├── __init__.py                  # 工具装配入口
│   ├── dynamic_loader.py            # 动态工具加载
│   ├── order_tool.py                # fallback 订单工具
│   ├── user_tool.py                 # fallback 用户工具
│   └── inventory_tool.py            # fallback 库存工具
│
└── tests/
    ├── chains/
    │   ├── test_orchestrator_intent_fallback.py
    │   ├── test_query_chain_decision.py
    │   └── test_orchestrator_tool_validation.py
    ├── memory/
    │   └── test_conversation_memory.py
    ├── rag/
    │   └── test_embedding_manager.py
    └── tools/
        └── test_dynamic_loader.py
```

### 模块边界说明

- `agent/schemas/tool_decision.py` 只负责定义 query 决策输出结构，不能掺杂业务逻辑。
- `agent/chains/validators.py` 负责参数校验、参数纠偏、缺参判断和工具执行前的统一校验，避免把校验逻辑继续堆进 `orchestrator.py`。
- `agent/memory/conversation_memory.py` 负责 recent history 与 turn count 管理；长期摘要触发策略与滑动窗口裁剪从这里落地。
- `agent/tools/dynamic_loader.py` 只负责把后端工具定义转成可执行工具，不负责匹配和决策。
- `agent/tests/*` 以链路风险点拆分，不用建大而全的集成测试目录；每个测试文件只验证一类行为。

---

## Task 1: 固化 query 决策输出为结构化 schema

**Files:**
- Create: `agent/schemas/tool_decision.py`
- Modify: `agent/chains/query_chain.py`
- Modify: `agent/chains/orchestrator.py:440-461`
- Test: `agent/tests/chains/test_query_chain_decision.py`

- [ ] **Step 1: Write the failing test**

```python
# agent/tests/chains/test_query_chain_decision.py
from agent.schemas.tool_decision import ToolDecision


def test_tool_decision_requires_tool_name_when_need_tool_true():
    payload = {
        "need_tool": True,
        "tool": None,
        "params": {"userId": "u1"},
        "answer": ""
    }

    try:
        ToolDecision.model_validate(payload)
    except Exception as exc:
        assert "tool" in str(exc)
    else:
        raise AssertionError("expected validation error")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_query_chain_decision.py::test_tool_decision_requires_tool_name_when_need_tool_true -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agent.schemas.tool_decision'`

- [ ] **Step 3: Write minimal schema implementation**

```python
# agent/schemas/tool_decision.py
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, model_validator


class ToolDecision(BaseModel):
    need_tool: bool = Field(default=False)
    tool: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    answer: str = ""

    @model_validator(mode="after")
    def validate_tool_requirements(self):
        if self.need_tool and not self.tool:
            raise ValueError("tool is required when need_tool is true")
        return self
```

- [ ] **Step 4: Update query chain to use structured parsing**

```python
# agent/chains/query_chain.py
from langchain_core.output_parsers import JsonOutputParser
from schemas.tool_decision import ToolDecision

parser = JsonOutputParser(pydantic_object=ToolDecision)
prompt = PromptTemplate.from_template(QUERY_TEMPLATE).partial(
    tool_descriptions=tool_descriptions,
    format_instructions=parser.get_format_instructions(),
)
chain = prompt | llm | parser
```

- [ ] **Step 5: Update orchestrator to consume structured decision**

```python
# agent/chains/orchestrator.py
parsed = raw_response if isinstance(raw_response, dict) else self._parse_llm_json(str(raw_response))
decision = ToolDecision.model_validate(parsed) if parsed else None
```

- [ ] **Step 6: Run tests to verify parsing passes**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_query_chain_decision.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/schemas/tool_decision.py agent/chains/query_chain.py agent/chains/orchestrator.py agent/tests/chains/test_query_chain_decision.py
git commit -m "fix(agent): enforce structured query decisions"
```

---

## Task 2: 修复意图识别兜底策略，避免误入 query 流程

**Files:**
- Modify: `agent/chains/orchestrator.py:409-421`
- Modify: `agent/config/prompts.yml:4-19`
- Test: `agent/tests/chains/test_orchestrator_intent_fallback.py`

- [ ] **Step 1: Write the failing test**

```python
# agent/tests/chains/test_orchestrator_intent_fallback.py
from chains.orchestrator import AgentOrchestrator


class BrokenIntentChain:
    def invoke(self, payload):
        return "not-json"


class DummyChain:
    def invoke(self, payload):
        return "ignored"


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
    response = orchestrator.process("你好")
    assert "无法理解" in response
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_orchestrator_intent_fallback.py::test_broken_intent_does_not_fall_back_to_query -v`
Expected: FAIL because current implementation falls into query path

- [ ] **Step 3: Implement fallback classification logic**

```python
# agent/chains/orchestrator.py
intent_type = "unknown"
if intent_obj:
    intent_type = intent_obj.intent
else:
    if any(token in user_input for token in ["你好", "hello", "hi"]):
        intent_type = "chat"
    logger.warning("【意图识别】解析失败，使用兜底分类: %s", intent_type)
```

- [ ] **Step 4: Tighten prompt wording to reduce invalid output**

```yaml
# agent/config/prompts.yml
intent:
  template: |
    ...
    严格只返回合法 JSON，不要输出 markdown、代码块、解释文字。
```

- [ ] **Step 5: Run tests to verify fallback behavior passes**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_orchestrator_intent_fallback.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/chains/orchestrator.py agent/config/prompts.yml agent/tests/chains/test_orchestrator_intent_fallback.py
git commit -m "fix(agent): harden intent fallback routing"
```

---

## Task 3: 新增工具参数校验与纠偏层

**Files:**
- Create: `agent/chains/validators.py`
- Modify: `agent/chains/orchestrator.py:311-355`
- Test: `agent/tests/chains/test_orchestrator_tool_validation.py`

- [ ] **Step 1: Write the failing test**

```python
# agent/tests/chains/test_orchestrator_tool_validation.py
from chains.validators import normalize_tool_params


class InputSchema:
    model_fields = {"userId": object(), "status": object()}


class ToolStub:
    input_schema = InputSchema


def test_normalize_tool_params_maps_human_status_to_backend_value():
    params = {"user_id": "u1", "status": "已发货"}
    normalized = normalize_tool_params(params, ToolStub())
    assert normalized == {"userId": "u1", "status": "shipped"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_orchestrator_tool_validation.py::test_normalize_tool_params_maps_human_status_to_backend_value -v`
Expected: FAIL with `ModuleNotFoundError` or assertion failure

- [ ] **Step 3: Implement validator helpers**

```python
# agent/chains/validators.py
ORDER_STATUS_ALIASES = {
    "待处理": "pending",
    "处理中": "processing",
    "已发货": "shipped",
    "已送达": "delivered",
    "已取消": "cancelled",
}


def normalize_tool_params(params: dict, tool) -> dict:
    ...
    if normalized.get("status") in ORDER_STATUS_ALIASES:
        normalized["status"] = ORDER_STATUS_ALIASES[normalized["status"]]
    return normalized
```

- [ ] **Step 4: Wire validator into orchestrator execution**

```python
# agent/chains/orchestrator.py
from chains.validators import normalize_tool_params, validate_required_params
...
params = normalize_tool_params(params, tool)
missing = validate_required_params(params, tool)
if missing:
    return f"缺少必要参数: {', '.join(missing)}"
```

- [ ] **Step 5: Add missing-parameter regression test**

```python
def test_validate_required_params_returns_missing_fields():
    ...
    assert validate_required_params({}, ToolWithRequiredUserId()) == ["userId"]
```

- [ ] **Step 6: Run tests to verify validator behavior**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_orchestrator_tool_validation.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/chains/validators.py agent/chains/orchestrator.py agent/tests/chains/test_orchestrator_tool_validation.py
git commit -m "fix(agent): validate and normalize tool params"
```

---

## Task 4: 修复 RAG user_id 透传并统一请求级缓存语义

**Files:**
- Modify: `agent/chains/orchestrator.py:84-145`
- Test: `agent/tests/chains/test_orchestrator_rag_context.py`

- [ ] **Step 1: Write the failing test**

```python
# agent/tests/chains/test_orchestrator_rag_context.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_orchestrator_rag_context.py::test_get_rag_context_passes_user_id_to_search_all_rag -v`
Expected: FAIL because current code passes `None`

- [ ] **Step 3: Fix user_id propagation and cache comments**

```python
# agent/chains/orchestrator.py
rag_result = self._search_all_rag(query, user_id)
```

Also update the docstring so it accurately describes whether MemoryRAG is included in `_search_all_rag`.

- [ ] **Step 4: Run tests to verify pass**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_orchestrator_rag_context.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/chains/orchestrator.py agent/tests/chains/test_orchestrator_rag_context.py
git commit -m "fix(agent): preserve user context in rag cache"
```

---

## Task 5: 调整短期/长期记忆策略为滑动窗口而非整段清空

**Files:**
- Modify: `agent/memory/conversation_memory.py`
- Modify: `agent/chains/orchestrator.py:481-505`
- Modify: `agent/config/rag.yml`
- Test: `agent/tests/memory/test_conversation_memory.py`

- [ ] **Step 1: Write the failing test**

```python
# agent/tests/memory/test_conversation_memory.py
from memory.conversation_memory import ConversationMemoryManager


def test_clear_before_recent_keeps_latest_messages():
    manager = ConversationMemoryManager(max_token_limit=2000)
    for idx in range(6):
        manager.add_user_message(f"u{idx}", "u1")
        manager.add_ai_message(f"a{idx}", "u1")

    manager.trim_history(user_id="u1", keep_last_pairs=2)
    history = manager.get_history("u1")

    assert "u5" in history
    assert "u4" in history
    assert "u0" not in history
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/memory/test_conversation_memory.py::test_clear_before_recent_keeps_latest_messages -v`
Expected: FAIL with missing method or wrong behavior

- [ ] **Step 3: Implement sliding-window trimming in memory manager**

```python
# agent/memory/conversation_memory.py
from langchain_core.messages import BaseMessage


def trim_history(self, user_id: Optional[str] = None, keep_last_pairs: int = 2) -> None:
    memory = self._get_memory(user_id)
    messages = memory.chat_memory.messages
    keep_count = keep_last_pairs * 2
    if len(messages) > keep_count:
        memory.chat_memory.messages = messages[-keep_count:]
```

- [ ] **Step 4: Replace hard clear with trim in orchestrator**

```python
# agent/chains/orchestrator.py
self.memory_manager.trim_history(user_id, keep_last_pairs=settings.memory_recent_pairs)
self.memory_manager.reset_turn_count(user_id)
```

- [ ] **Step 5: Add config knob for recent history window**

```yaml
# agent/config/rag.yml
memory:
  summary_threshold: 5
  similarity_threshold: 0.5
  top_k: 3
  recent_pairs: 2
```

- [ ] **Step 6: Run tests to verify memory behavior**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/memory/test_conversation_memory.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/memory/conversation_memory.py agent/chains/orchestrator.py agent/config/rag.yml agent/tests/memory/test_conversation_memory.py
git commit -m "fix(agent): retain recent context after memory summarization"
```

---

## Task 6: 去掉动态工具加载中的 exec，改为闭包工厂

**Files:**
- Modify: `agent/tools/dynamic_loader.py`
- Test: `agent/tests/tools/test_dynamic_loader.py`

- [ ] **Step 1: Write the failing test**

```python
# agent/tests/tools/test_dynamic_loader.py
from tools.dynamic_loader import DynamicToolLoader


def test_create_tool_returns_callable_without_exec_generated_source():
    loader = DynamicToolLoader("http://localhost:8080")
    tool = loader._create_tool({
        "name": "query_order_list",
        "displayName": "查询订单",
        "description": "查询用户订单列表",
        "endpoint": "/tools/order/query",
        "httpMethod": "POST",
        "params": [{"name": "userId", "required": True}],
    })

    assert tool.name == "query_order_list"
    assert tool.func is not None
```

- [ ] **Step 2: Run test to verify current behavior is unprotected**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/tools/test_dynamic_loader.py::test_create_tool_returns_callable_without_exec_generated_source -v`
Expected: PASS or FAIL depending on current shape; treat this step as baseline capture before refactor

- [ ] **Step 3: Replace exec with a closure factory**

```python
# agent/tools/dynamic_loader.py

def _build_tool_func(self, *, name, endpoint, http_method, http_timeout, param_names):
    def _tool(**kwargs):
        req_params = {k: v for k, v in kwargs.items() if v is not None and k in param_names}
        url = f"{self.base_url}{endpoint}"
        payload = {"action": name, "params": req_params}
        ...
        return json.dumps(data, ensure_ascii=False)
    return _tool
```

- [ ] **Step 4: Preserve required/optional schema support when building StructuredTool**

Document in code comments how required parameters are reflected in the callable signature or wrapper schema.

- [ ] **Step 5: Run tests to verify refactor preserves behavior**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/tools/test_dynamic_loader.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/tools/dynamic_loader.py agent/tests/tools/test_dynamic_loader.py
git commit -m "refactor(agent): replace exec in dynamic tool loader"
```

---

## Task 7: 收敛敏感日志输出并统一日志级别

**Files:**
- Modify: `agent/server.py`
- Modify: `agent/chains/orchestrator.py`
- Modify: `agent/tools/dynamic_loader.py`
- Modify: `agent/settings.py`
- Test: `agent/tests/chains/test_logging_redaction.py`

- [ ] **Step 1: Write the failing test**

```python
# agent/tests/chains/test_logging_redaction.py
from chains.orchestrator import redact_for_log


def test_redact_for_log_masks_user_id_and_large_payloads():
    text = "userId=u123456 orderNo=ORD0001 amount=999"
    redacted = redact_for_log(text)
    assert "u123456" not in redacted
    assert "ORD0001" not in redacted
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_logging_redaction.py::test_redact_for_log_masks_user_id_and_large_payloads -v`
Expected: FAIL with missing helper

- [ ] **Step 3: Implement redaction helpers and config flag**

```python
# agent/settings.py
self.verbose_agent_logs = get_config("settings.yml", "agent", "verbose_logs", default=False)
```

```python
# agent/chains/orchestrator.py

def redact_for_log(text: str) -> str:
    ...
```

- [ ] **Step 4: Replace raw payload logging with redacted summaries**

Examples to update:
- `server.py` request/response preview logs
- `orchestrator.py` history/raw_response/final_response logs
- `dynamic_loader.py` tool result logs

- [ ] **Step 5: Run tests to verify redaction behavior**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_logging_redaction.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/server.py agent/chains/orchestrator.py agent/tools/dynamic_loader.py agent/settings.py agent/tests/chains/test_logging_redaction.py
git commit -m "fix(agent): redact sensitive execution logs"
```

---

## Task 8: 减少重复 embedding 并显式化 provider 降级策略

**Files:**
- Modify: `agent/rag/embeddings.py`
- Modify: `agent/rag/tool_rag.py`
- Modify: `agent/rag/knowledge_rag.py`
- Modify: `agent/memory/memory_rag.py`
- Modify: `agent/chains/orchestrator.py`
- Modify: `agent/config/settings.yml`
- Test: `agent/tests/rag/test_embedding_manager.py`

- [ ] **Step 1: Write the failing test**

```python
# agent/tests/rag/test_embedding_manager.py
from rag.embeddings import EmbeddingManager


def test_embed_query_reuses_explicit_provider_configuration(monkeypatch):
    manager = EmbeddingManager(model_name="fake-model")
    calls = []

    def fake_embed(texts):
        calls.append(texts)
        return [[0.1, 0.2] for _ in texts]

    manager._embedding_fn = fake_embed
    result = manager.embed_query("hello")

    assert result == [0.1, 0.2]
    assert calls == [["hello"]]
```

- [ ] **Step 2: Run test to verify baseline behavior**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/rag/test_embedding_manager.py::test_embed_query_reuses_explicit_provider_configuration -v`
Expected: PASS or FAIL; use as baseline and extend file with new provider tests

- [ ] **Step 3: Add provider configuration and explicit startup validation**

```python
# agent/rag/embeddings.py
class EmbeddingManager:
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL, provider: str = "local"):
        self.provider = provider
```

Add explicit branches for `local` and `openai_compatible`, and raise a clear error for unsupported providers instead of silently misusing DeepSeek credentials.

- [ ] **Step 4: Add search-by-embedding methods to RAG components**

```python
# agent/rag/tool_rag.py

def search_by_embedding(self, query_embedding, top_k=3):
    ...
```

Repeat for knowledge and memory RAG so orchestrator can compute query embedding once and reuse it.

- [ ] **Step 5: Update orchestrator to compute query embedding once per request**

```python
# agent/chains/orchestrator.py
query_embedding = self._embedding_manager.embed_query(query)
```

- [ ] **Step 6: Run tests to verify provider behavior and embedding reuse**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/rag/test_embedding_manager.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/rag/embeddings.py agent/rag/tool_rag.py agent/rag/knowledge_rag.py agent/memory/memory_rag.py agent/chains/orchestrator.py agent/config/settings.yml agent/tests/rag/test_embedding_manager.py
git commit -m "perf(agent): reuse embeddings and harden provider config"
```

---

## Task 9: 用本地模板渲染替代默认二次 LLM 润色

**Files:**
- Create: `agent/chains/renderers.py`
- Modify: `agent/chains/orchestrator.py:366-398`
- Test: `agent/tests/chains/test_result_rendering.py`

- [ ] **Step 1: Write the failing test**

```python
# agent/tests/chains/test_result_rendering.py
from chains.renderers import render_tool_result


def test_render_tool_result_formats_list_as_markdown_table():
    tool_result = '[{"orderNo": "O1", "status": "shipped"}]'
    output = render_tool_result(tool_result, "查询订单")
    assert "| orderNo | status |" in output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_result_rendering.py::test_render_tool_result_formats_list_as_markdown_table -v`
Expected: FAIL with missing module

- [ ] **Step 3: Implement local renderers for list/detail/statistics shapes**

```python
# agent/chains/renderers.py
import json


def render_tool_result(tool_result: str, user_question: str) -> str:
    ...
```

- [ ] **Step 4: Update orchestrator to prefer local renderer and fallback to LLM only when needed**

```python
# agent/chains/orchestrator.py
rendered = render_tool_result(tool_result, user_input)
response = rendered if rendered else self._polish_result(tool_result, user_input)
```

- [ ] **Step 5: Run tests to verify rendering behavior**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_result_rendering.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/chains/renderers.py agent/chains/orchestrator.py agent/tests/chains/test_result_rendering.py
git commit -m "perf(agent): prefer local rendering for tool results"
```

---

## Task 10: 分阶段初始化与回归验证

**Files:**
- Modify: `agent/dependencies.py`
- Modify: `agent/server.py`
- Test: `agent/tests/chains/test_dependency_initialization.py`
- Test: `agent/tests/chains/test_end_to_end_query_path.py`

- [ ] **Step 1: Write the failing initialization test**

```python
# agent/tests/chains/test_dependency_initialization.py
from dependencies import initialize_dependencies


def test_initialize_dependencies_returns_orchestrator_when_rag_disabled(monkeypatch):
    monkeypatch.setenv("DISABLE_RAG", "1")
    orchestrator = initialize_dependencies()
    assert orchestrator is not None
```

- [ ] **Step 2: Run test to verify current code lacks staged initialization**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_dependency_initialization.py::test_initialize_dependencies_returns_orchestrator_when_rag_disabled -v`
Expected: FAIL or require code change to support staged init flag

- [ ] **Step 3: Refactor dependency initialization into core and optional modules**

```python
# agent/dependencies.py
core = build_core_dependencies()
optional = build_optional_dependencies(settings)
```

Core must include LLM, memory manager, chains, and tool registry; optional modules include RAG and long-term memory.

- [ ] **Step 4: Add end-to-end regression test for query path without external services**

```python
# agent/tests/chains/test_end_to_end_query_path.py
# Stub intent chain, query chain, tool executor, memory manager
# Verify query request -> decision -> tool execute -> local render -> memory update
```

- [ ] **Step 5: Run focused regression suite**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains/test_dependency_initialization.py tests/chains/test_end_to_end_query_path.py -v`
Expected: PASS

- [ ] **Step 6: Run full agent regression suite**

Run: `cd /Users/yangte/PycharmProjects/langchain-study/agent && pytest tests/chains tests/memory tests/rag tests/tools -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/dependencies.py agent/server.py agent/tests/chains/test_dependency_initialization.py agent/tests/chains/test_end_to_end_query_path.py
git commit -m "refactor(agent): stage dependency initialization and add regressions"
```

---

## Implementation Notes

- 所有新测试文件都放在 `agent/tests/` 下，避免混入 `.venv` 中的第三方测试。
- 如果当前仓库还没有 pytest 入口配置，按最小方式补一个 `agent/pytest.ini`，内容只包含 `testpaths = tests`，并在第一次引入测试目录时一起提交。
- 每个任务完成后先跑该任务的 focused tests，再在 Task 10 汇总跑完整回归。
- 修改 `orchestrator.py` 时坚持小步提交；它是当前 blast radius 最大的文件，不要把多个主题改动压进同一个 commit。
- 如果某个改造需要额外配置项，先更新 `agent/config/*.yml` 与 `agent/settings.py`，再写实现，避免隐藏默认值。

---

## Suggested Execution Order

1. Task 1-4：先修 query 正确性和上下文 bug。
2. Task 5-7：修记忆和日志，降低线上风险。
3. Task 8-9：做性能优化，减少延迟与成本。
4. Task 10：统一收敛初始化和回归测试。
