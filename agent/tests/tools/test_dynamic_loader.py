from tools.dynamic_loader import DynamicToolLoader


def test_create_tool_returns_callable_without_exec_generated_source():
    loader = DynamicToolLoader("http://localhost:8080")
    tool = loader._create_tool(
        {
            "name": "query_order_list",
            "displayName": "查询订单",
            "description": "查询用户订单列表",
            "endpoint": "/tools/order/query",
            "httpMethod": "POST",
            "params": [{"name": "userId", "required": True}],
        }
    )

    assert tool.name == "query_order_list"
    assert tool.func is not None
