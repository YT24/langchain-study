ORDER_STATUS_ALIASES = {
    "待处理": "pending",
    "处理中": "processing",
    "已发货": "shipped",
    "已送达": "delivered",
    "已取消": "cancelled",
}


def normalize_tool_params(params: dict, tool) -> dict:
    if not hasattr(tool, "input_schema") or not tool.input_schema:
        return params

    schema_fields = getattr(tool.input_schema, "model_fields", {}) or {}
    schema_field_names = set(schema_fields.keys())
    normalized = {}

    for key, value in params.items():
        if key in schema_field_names:
            normalized[key] = value
            continue

        compact_key = key.replace("_", "")
        matched_key = next(
            (
                schema_key
                for schema_key in schema_field_names
                if schema_key.lower().replace("_", "") == compact_key.lower()
            ),
            key,
        )
        normalized[matched_key] = value

    status = normalized.get("status")
    if status in ORDER_STATUS_ALIASES:
        normalized["status"] = ORDER_STATUS_ALIASES[status]

    return normalized


def validate_required_params(params: dict, tool) -> list[str]:
    if not hasattr(tool, "input_schema") or not tool.input_schema:
        return []

    missing = []
    schema_fields = getattr(tool.input_schema, "model_fields", {}) or {}
    for field_name, field in schema_fields.items():
        is_required = getattr(field, "is_required", None)
        required = is_required() if callable(is_required) else False
        if required and params.get(field_name) in (None, ""):
            missing.append(field_name)
    return missing
