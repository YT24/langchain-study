import logging

from flask import Flask, request, jsonify

from dependencies import initialize_dependencies

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化全局编排器
logger.info("正在初始化 Agent...")
orchestrator = initialize_dependencies()
logger.info("Agent 初始化完成")


@app.route('/api/chat', methods=['POST'])
def chat():
    """处理用户对话请求"""
    data = request.json
    message = data.get('message', '')
    user_id = data.get('userId', None)

    if not message:
        return jsonify({'success': False, 'message': '消息不能为空'}), 400

    try:
        logger.info(f"【收到请求】用户ID: {user_id}, 消息: {message[:100]}")
        response = orchestrator.process(message, user_id=user_id)
        logger.info(f"【返回响应】类型: {type(response).__name__}, 内容: {str(response)[:100]}")
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        logger.error(f"【处理失败】错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/tools/reload', methods=['POST'])
def reload_tools():
    """重新加载工具"""
    try:
        from config import get_settings
        from tools import reload_tools as reload_tools_func

        settings = get_settings()
        new_tools = reload_tools_func(settings.backend_url)

        # 更新 orchestrator 的工具
        orchestrator.set_tools(new_tools)

        # 重新索引 ToolRAG
        if hasattr(orchestrator, '_tool_rag') and orchestrator._tool_rag:
            orchestrator._tool_rag.reload(new_tools)
            logger.info(f"【ToolRAG】已重新索引 {len(new_tools)} 个工具")

        return jsonify({
            'success': True,
            'message': f'工具已重新加载，共 {len(new_tools)} 个'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'type': 'LangChain Agent'
    })


if __name__ == '__main__':
    from config import get_settings
    settings = get_settings()
    app.run(
        host='0.0.0.0',
        port=settings.agent_port,
        debug=False
    )
