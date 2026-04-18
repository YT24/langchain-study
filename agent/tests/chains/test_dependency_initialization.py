from dependencies import initialize_dependencies
from settings import reset_settings_cache


def test_initialize_dependencies_returns_orchestrator_when_rag_disabled(monkeypatch):
    monkeypatch.setenv("DISABLE_RAG", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    reset_settings_cache()

    orchestrator = initialize_dependencies()

    assert orchestrator is not None
    assert orchestrator._tool_rag is None
    assert orchestrator._knowledge_rag is None
    assert orchestrator._memory_rag is None

    monkeypatch.delenv("DISABLE_RAG", raising=False)
    reset_settings_cache()
