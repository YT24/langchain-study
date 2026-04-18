from schemas.tool_decision import ToolDecision


def test_tool_decision_requires_tool_name_when_need_tool_true():
    payload = {
        "need_tool": True,
        "tool": None,
        "params": {"userId": "u1"},
        "answer": "",
    }

    try:
        ToolDecision.model_validate(payload)
    except Exception as exc:
        assert "tool" in str(exc)
    else:
        raise AssertionError("expected validation error")
