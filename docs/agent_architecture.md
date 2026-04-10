# AI Agent 架构设计文档

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interface                               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent Core Engine                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │   Router     │→ │  RAG Retriever│→ │   Context Builder       │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
│         │                  │                       │                │
│         ▼                  ▼                       ▼                │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                    LLM (DeepSeek)                             │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ Tool Executor│→ │   Memory     │→ │  Response Generator      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
           │                                    │
           ▼                                    ▼
┌──────────────────────┐           ┌──────────────────────────────┐
│    Vector Store       │           │      Tool Backend (Java)    │
│  (ChromaDB/Qdrant)    │           │   Order/User/Inventory      │
└──────────────────────┘           └──────────────────────────────┘
```

## 2. 核心组件设计

### 2.1 Router (意图路由)

**功能**：
- 判断用户意图：查询、统计、闲聊、未知
- 决定是否需要调用工具
- 路由到不同的处理流程

**Prompt 设计**：
```
你是一个意图分类器。用户输入后，判断用户的意图：

可选意图：
1. query - 需要查询数据的场景
2. statistic - 需要统计汇总的场景
3. chat - 一般对话或闲聊
4. unknown - 无法理解或不在能力范围内

用户输入：{user_input}

返回格式：
{"intent": "query|statistic|chat|unknown", "reason": "判断理由"}
```

### 2.2 RAG Retriever (向量检索)

**存储内容**：
1. **工具描述** (Tool Embeddings)
   - 工具名称、描述、参数
   - 使用场景、示例

2. **业务知识库** (Knowledge Base)
   - 订单状态说明
   - 用户等级规则
   - 常见问题解答

3. **用户记忆** (User Memory)
   - 用户偏好
   - 历史交互摘要

**检索流程**：
```
用户问题 → Embedding → Vector DB Search → Top-K Results → 加入Prompt
```

### 2.3 Memory Manager (记忆管理)

**三层记忆架构**：

```
┌─────────────────────────────────────────────────────────────┐
│                    Long-term Memory (向量库)                  │
│  - 用户偏好、习惯                                          │
│  - 历史交互摘要                                            │
│  - 重要事实                                                │
└─────────────────────────────────────────────────────────────┘
                              ↑
                              │ 定期总结/重要信息写入
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Short-term Memory (Redis/内存)            │
│  - 当前会话历史                                            │
│  - 最近 N 轮对话                                           │
│  - 工具调用记录                                            │
└─────────────────────────────────────────────────────────────┘
                              ↑
                              │ 实时更新
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Working Memory                           │
│  - 当前上下文                                              │
│  - 待确认参数                                              │
│  - 中间状态                                                │
└─────────────────────────────────────────────────────────────┘
```

**记忆操作**：
- `add_message(role, content)` - 添加消息
- `search_memory(query)` - 检索记忆
- `summarize_and_store()` - 总结并存储
- `get_recent_context(k)` - 获取最近K轮对话

### 2.4 Context Builder (上下文构建)

**Prompt 结构**：
```
# 系统提示
你是一个专业的业务助手。

# 可用工具
{retrieved_tools}

# 相关知识
{retrieved_knowledge}

# 用户记忆
{user_memory}

# 当前会话
{conversation_history}

# 用户问题
{user_input}

# 回答要求
1. 如果需要调用工具，返回JSON格式
2. 如果是闲聊，直接回答
3. 优先使用检索到的知识
```

### 2.5 Tool Executor (工具执行器)

**功能**：
- 解析 LLM 输出的工具调用
- 执行工具调用
- 处理异常和超时
- 记录调用日志

**执行流程**：
```
1. 解析工具调用 JSON
2. 参数验证和转换
3. 调用 Tool Backend
4. 处理响应
5. 记录日志到数据库
6. 返回结果
```

### 2.6 Response Generator (响应生成器)

**功能**：
- 将工具结果转换为自然语言
- 支持 Markdown 格式化
- 多工具结果聚合

## 3. 向量数据库设计

### 3.1 Collections

| Collection | 用途 | Schema |
|-----------|------|--------|
| `tools` | 工具描述 | `id, name, description, actions, examples` |
| `knowledge` | 业务知识 | `id, category, question, answer` |
| `user_memory` | 用户记忆 | `user_id, memory_type, content, embedding` |
| `conversations` | 会话历史 | `session_id, messages, summary` |

### 3.2 索引策略

```python
# Tool Embeddings
tool_embedding = {
    "id": "order_tool_query_list",
    "tool": "OrderTool",
    "action": "query_order_list",
    "description": "查询用户订单列表，支持金额、日期过滤",
    "params": ["userId", "status", "minAmount", "maxAmount", "startDate", "endDate"],
    "examples": [
        "帮我查U001的订单",
        "查询2026年3月的订单",
        "金额大于500的订单"
    ],
    "embedding": embed("查询用户订单，支持多种过滤条件...")
}

# User Memory
user_memory = {
    "id": "memory_u001_preference",
    "user_id": "U001",
    "memory_type": "preference",
    "content": "用户U001经常查询订单金额大于300的记录",
    "importance": 0.8,
    "created_at": "2026-04-10"
}
```

## 4. 多轮对话设计

### 4.1 对话状态机

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │ 用户输入
                           ▼
                    ┌─────────────┐
              ┌───→│   WAIT_    │←─┐
              │     │   PARAM    │  │ 参数不完整
              │     └──────┬──────┘  │
              │            │ 参数完整  │
              │            ▼          │
              │     ┌─────────────┐   │
              │     │  EXECUTING │───┤
              │     └──────┬──────┘   │
              │            │          │
              │     ┌──────┴──────┐   │
              │     │   WAIT_    │   │
              │     │   CONFIRM  │───┘
              │     └──────┬──────┘
              │            │ 用户确认
              │            ▼
              │     ┌─────────────┐
              │     │   COMPLETE  │
              │     └──────┬──────┘
              │            │
              └────────────┘
```

### 4.2 对话示例：参数缺失补充

```
用户：帮我查一下U001的订单
Agent：好的，您想查询U001的什么状态的订单？（待支付/已支付/已完成/已取消）

用户：已完成的
Agent：[执行查询] 找到了2笔已完成订单...
```

### 4.3 Memory 更新策略

```python
class MemoryManager:
    def __init__(self):
        self.short_term = []  # 最近对话
        self.long_term = VectorStore()  # 持久化记忆

    def add_turn(self, user_msg, agent_msg, tool_calls=None):
        # 1. 添加到短期记忆
        self.short_term.append({
            "user": user_msg,
            "agent": agent_msg,
            "tool_calls": tool_calls,
            "timestamp": now()
        })

        # 2. 超过阈值时总结并写入长期记忆
        if len(self.short_term) >= 5:
            summary = self.summarize(self.short_term)
            self.long_term.add(summary)
            self.short_term = []

        # 3. 提取重要信息写入用户记忆
        facts = self.extract_facts(user_msg, agent_msg)
        for fact in facts:
            self.long_term.add_fact(fact)

    def get_context(self, user_input):
        # 1. 检索相关长期记忆
        relevant_memories = self.long_term.search(user_input, top_k=3)

        # 2. 获取短期记忆
        recent = self.short_term[-3:]  # 最近3轮

        return {
            "memories": relevant_memories,
            "recent": recent
        }
```

## 5. RAG 增强

### 5.1 Tool RAG

```python
class ToolRAG:
    def __init__(self, vector_store):
        self.store = vector_store

    def index_tools(self, tools):
        """将工具索引到向量库"""
        for tool in tools:
            for action in tool["actions"]:
                self.store.add(
                    collection="tools",
                    id=f"{tool['name']}_{action['name']}",
                    vector=embed(action["description"]),
                    text=f"""
                    工具名称：{tool['name']}
                    功能：{tool['description']}
                    Action：{action['name']}
                    描述：{action['description']}
                    参数：{action['params']}
                    """
                )

    def retrieve(self, query, top_k=3):
        """根据用户问题检索相关工具"""
        query_vector = embed(query)
        results = self.store.search("tools", query_vector, top_k)
        return results
```

### 5.2 Knowledge RAG

```python
# 知识库内容
knowledge_base = [
    {
        "category": "订单状态",
        "q": "订单状态有哪些",
        "a": "订单状态包括：pending(待支付)、paid(已支付)、shipped(已发货)、completed(已完成)、cancelled(已取消)"
    },
    {
        "category": "会员等级",
        "q": "会员等级有什么区别",
        "a": "会员等级：normal(普通)、silver(银卡)、gold(金卡)、vip(VIP)，等级越高享受更多优惠"
    }
]
```

## 6. 完整对话流程

```python
async def chat(user_input: str, user_id: str):
    # 1. 意图识别
    intent = router.classify(user_input)

    # 2. 获取上下文
    context = memory.get_context(user_input)

    # 3. RAG 检索
    relevant_tools = tool_rag.retrieve(user_input)
    relevant_knowledge = knowledge_rag.retrieve(user_input)

    # 4. 构建 Prompt
    prompt = context_builder.build(
        user_input=user_input,
        intent=intent,
        tools=relevant_tools,
        knowledge=relevant_knowledge,
        memory=context,
        history=memory.short_term
    )

    # 5. LLM 处理
    response = await llm.chat(prompt)

    # 6. 解析响应
    if response.requires_tool_call():
        result = await tool_executor.execute(response.tool_calls)
        # 继续 LLM 生成最终响应
        final_response = await llm.chat(prompt, tool_results=result)
    else:
        final_response = response

    # 7. 更新记忆
    memory.add_turn(user_input, final_response)

    return final_response
```

## 7. 技术选型

| 组件 | 推荐方案 | 说明 |
|------|---------|------|
| 向量库 | ChromaDB / Qdrant | 轻量级/生产级 |
| LLM | DeepSeek | 成本低，效果好 |
| 短期记忆 | Redis / 内存 | 高速访问 |
| 长期记忆 | 向量库 | 持久化+检索 |
| 框架 | LangChain / 自研 | 灵活控制 |
| 后端 | Java Spring Boot | 工具执行 |

## 8. 后续优化方向

1. **Function Calling**：使用 OpenAI Function Calling 格式，提高工具调用准确性
2. **ReAct**：引入 Reasoning + Acting 模式，处理复杂查询
3. **Agent Workflow**：支持多 Agent 协作
4. **监控告警**：调用链路追踪、性能监控
