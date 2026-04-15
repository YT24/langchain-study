"""
Flask Server - API 服务
"""
import os
from flask import Flask, request, jsonify
from agent.core.agent import AgentCore, ReActAgent

app = Flask(__name__)

# 初始化 Agent
# USE_REACT = os.getenv("USE_REACT", "false").lower() == "true"

# if USE_REACT:
#     agent = ReActAgent()
#     print("使用 ReAct Agent")
# else:
#     agent = AgentCore()
#     print("使用标准 Agent")
agent = ReActAgent()
print("使用 ReAct Agent")

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    user_id = data.get('userId', None)
    session_id = data.get('sessionId', None)

    if not message:
        return jsonify({'success': False, 'message': '消息不能为空'}), 400

    try:
        response = agent.chat(message, user_id=user_id, session_id=session_id)
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/tools/reload', methods=['POST'])
def reload_tools():
    """重新加载工具描述和工具状态"""
    try:
        from agent.rag.tool_rag import init_tool_rag_from_backend
        agent.tool_rag = init_tool_rag_from_backend(agent.backend_url)
        agent.tool_executor.reload()
        enabled = list(agent.tool_executor.tools.keys())
        return jsonify({'success': True, 'message': '工具已重新加载', 'enabled_tools': enabled})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'agent_type': 'ReAct',
        'session_count': len(agent.memory_manager.short_term) if hasattr(agent.memory_manager, 'short_term') else 0
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
