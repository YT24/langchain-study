# 结果渲染：本地表格 + LLM 一句话总结

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 工具结果输出改为「本地表格始终经过 LLM 做一句话前置总结」，保留表格结构，增加自然语言说明。

**Architecture:** 修改 `orchestrator.py` 的工具结果处理逻辑，去掉本地渲染短路，始终调用 `_polish_result`；同时更新其 prompt 使 LLM 只生成 1 句话前置说明，不重复表格内容。

**Tech Stack:** Python, LangChain, Flask, pytest

---

## 文件清单

| 文件 | 改动类型 |
|------|---------|
| `agent/chains/orchestrator.py:563-570` | 修改 — 去掉短路，始终过 LLM |
| `agent/chains/orchestrator.py:444-476` (`_polish_result`) | 修改 — 更新 prompt |
| `agent/tests/chains/test_result_rendering.py` | 修改 — 增加回归测试 |

---

### Task 1: 更新 `_polish_result` prompt 为「一句话前置说明」

**Files:**
- Modify: `agent/chains/orchestrator.py:444-476`

- [ ] **Step 1: 确认当前 `_polish_result` 实现**

确认 `_polish_result` 当前使用的 prompt 内容（`agent/chains/orchestrator.py` 内 `_polish_result` 方法）。

- [ ] **Step 2: 更新 prompt 模板**

将 `_polish_result` 中的 prompt 从原「格式化原始数据为 Markdown」改为：

```
后端已返回以下查询结果：

{tool_result}

请用 1 句话简要说明查询到了什么（条数、关键摘要）。
直接返回这段话，不要重复表格内容，不要额外解释。

最终返回格式：`{LLM一句话}\n\n{tool_result}`（拼接 LLM 总结与原始表格）
```

修改位置在 `orchestrator.py` 中 `_polish_result` 方法内的 `template` 变量。

- [ ] **Step 3: 验证语法**

```bash
python -m py_compile agent/chains/orchestrator.py
```
Expected: 无输出（语法正确）

---

### Task 2: 去掉短路逻辑，始终调用 LLM 总结

**Files:**
- Modify: `agent/chains/orchestrator.py:563-570`

- [ ] **Step 1: 确认当前代码**

当前逻辑：
```python
rendered_result = render_tool_result(tool_result, user_input)
if rendered_result:
    logger.info("【结果渲染】使用本地渲染结果")
    response = rendered_result
else:
    logger.info("【结果润色】开始润色工具返回结果...")
    response = self._polish_result(tool_result, user_input)
```

- [ ] **Step 2: 替换为始终过 LLM**

```python
rendered_result = render_tool_result(tool_result, user_input)
logger.info("【结果渲染】本地表格生成完成")
logger.info("【结果润色】开始 LLM 一句话总结...")
response = self._polish_result(rendered_result, user_input)
```

- [ ] **Step 3: 验证语法**

```bash
python -m py_compile agent/chains/orchestrator.py
```
Expected: 无输出（语法正确）

---

### Task 3: 增加回归测试

**Files:**
- Modify: `agent/tests/chains/test_result_rendering.py`

- [ ] **Step 1: 确认现有测试**

现有测试覆盖 `render_tool_result` 的表格和字典输出格式。

- [ ] **Step 2: 增加新测试**

在 `test_result_rendering.py` 末尾增加：

```python
def test_render_tool_result_always_produces_table_for_list_of_dicts():
    """验证 render_tool_result 始终输出原始表格，不被 LLM 污染"""
    tool_result = '[{"orderNo": "O1", "status": "shipped", "totalAmount": 299.0}]'
    output = render_tool_result(tool_result, "查询订单")
    # 表格结构必须保留
    assert "| orderNo | status | totalAmount |" in output
    assert "| O1 | shipped | 299.0 |" in output
    # 不包含 LLM 自然语言总结（那是 polish_result 的职责）
    assert not output.startswith("已为您")
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest agent/tests/chains/test_result_rendering.py -v
```
Expected: `test_render_tool_result_formats_list_as_markdown_table PASSED` + 新测试 PASSED

---

### Task 4: 端到端验证

- [ ] **Step 1: 运行完整回归**

```bash
pytest agent/tests/chains agent/tests/memory agent/tests/rag agent/tests/tools -v
```
Expected: 全部 PASSED

- [ ] **Step 2: 从仓库根验证导入**

```bash
cd /Users/yangte/PycharmProjects/langchain-study && python -c "import agent.chains.orchestrator; print('ok')"
```
Expected: `ok`

---

### Task 5: 提交

```bash
git add agent/chains/orchestrator.py agent/tests/chains/test_result_rendering.py
git commit -m "feat(agent): always pass rendered table to LLM for one-sentence summary"
```
