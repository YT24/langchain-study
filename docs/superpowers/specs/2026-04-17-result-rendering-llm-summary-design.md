# 结果渲染：本地表格 + LLM 一句话总结

## 目标

工具结果输出从「仅本地表格渲染」调整为「本地表格 + LLM 一句话前置说明」。

- 保留现有本地表格结构（Markdown 表格）
- 在表格前增加一句简短自然语言总结
- 始终经过 LLM，不走短路逻辑

## 设计

### 改动位置
- `agent/chains/orchestrator.py:563-570`

### 当前逻辑

```python
rendered_result = render_tool_result(tool_result, user_input)
if rendered_result:
    response = rendered_result          # 直接返回表格
else:
    response = self._polish_result(...)
```

### 改动后逻辑

```python
rendered_result = render_tool_result(tool_result, user_input)
logger.info("【结果渲染】本地表格生成完成")
response = self._polish_result(rendered_result, user_input)  # 始终过 LLM
```

### `_polish_result` Prompt 调整

原 prompt：将原始数据格式化为 Markdown。

新 prompt：

```
后端已返回以下查询结果：

{tool_result}

请用 1 句话简要说明查询到了什么（条数、关键摘要）。
直接返回这段话，不要重复表格内容，不要额外解释。
```

### 行为变化

| 场景 | 当前（仅本地表格） | 改动后（LLM 一句话 + 表格） |
|------|------------------|--------------------------|
| 查到 2 条订单 | `[表格: 2行]` | "已为您查到 2 条订单"\n\n`[表格: 2行]` |
| 查到 1 条订单 | `[表格: 1行]` | "已为您查到 1 条订单"\n\n`[表格: 1行]` |
| 无数据 | "未查询到数据" | "未查询到数据"（保持不变） |

## 测试

在 `agent/tests/chains/test_result_rendering.py` 增加测试，验证 `render_tool_result` 仍然输出原始表格格式（确保 LLM 输入不被污染）。

## 文件清单

- `agent/chains/orchestrator.py` — 去掉短路逻辑，始终调用 `_polish_result`
- `agent/chains/orchestrator.py` — 更新 `_polish_result` prompt
- `agent/tests/chains/test_result_rendering.py` — 增加回归测试
