from chains.renderers import render_tool_result


def test_render_tool_result_formats_list_as_markdown_table():
    tool_result = '[{"orderNo": "O1", "status": "shipped"}]'
    output = render_tool_result(tool_result, "查询订单")
    assert "| orderNo | status |" in output


def test_render_tool_result_formats_dict_as_bullets():
    tool_result = '{"orderNo": "O1", "status": "shipped"}'
    output = render_tool_result(tool_result, "查询订单详情")
    assert "- **orderNo**: O1" in output


def test_render_tool_result_always_produces_table_for_list_of_dicts():
    """验证 render_tool_result 始终输出原始表格，不被 LLM 污染"""
    tool_result = '[{"orderNo": "O1", "status": "shipped", "totalAmount": 299.0}]'
    output = render_tool_result(tool_result, "查询订单")
    # 表格结构必须保留
    assert "| orderNo | status | totalAmount |" in output
    assert "| O1 | shipped | 299.0 |" in output
    # 不包含 LLM 自然语言总结（那是 polish_result 的职责）
    assert not output.startswith("已为您")
