from chains.validators import normalize_tool_params, validate_required_params


class FieldStub:
    def __init__(self, required=False):
        self.is_required = lambda: required


class InputSchema:
    model_fields = {"userId": FieldStub(required=True), "status": FieldStub(required=False)}


class ToolStub:
    input_schema = InputSchema


def test_normalize_tool_params_maps_human_status_to_backend_value():
    params = {"user_id": "u1", "status": "已发货"}
    normalized = normalize_tool_params(params, ToolStub())
    assert normalized == {"userId": "u1", "status": "shipped"}


def test_validate_required_params_returns_missing_fields():
    missing = validate_required_params({}, ToolStub())
    assert missing == ["userId"]
