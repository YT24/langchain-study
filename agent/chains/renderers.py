import json
from typing import Any


def _loads_json(tool_result: str):
    try:
        return json.loads(tool_result)
    except Exception:
        return None


def _render_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "未查询到数据。"

    headers = list(rows[0].keys())
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = []

    for row in rows:
        body_lines.append(
            "| " + " | ".join(str(row.get(header, "")) for header in headers) + " |"
        )

    return "\n".join([header_line, separator_line, *body_lines])


def _render_dict(data: dict[str, Any]) -> str:
    lines = []
    for key, value in data.items():
        lines.append(f"- **{key}**: {value}")
    return "\n".join(lines)


def render_tool_result(tool_result: str, user_question: str) -> str:
    data = _loads_json(tool_result)
    if data is None:
        return ""

    title = f"查询结果：{user_question}"

    if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
        return f"{title}\n\n{_render_table(data)}"

    if isinstance(data, dict):
        if isinstance(data.get("data"), list) and data["data"] and all(isinstance(item, dict) for item in data["data"]):
            return f"{title}\n\n{_render_table(data['data'])}"
        return f"{title}\n\n{_render_dict(data)}"

    if isinstance(data, list):
        lines = [title, ""]
        lines.extend(f"- {item}" for item in data)
        return "\n".join(lines)

    return f"{title}\n\n{data}"
