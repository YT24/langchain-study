import logging

from flask import Flask, request, jsonify

from dependencies import initialize_dependencies

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
    datefmt='%H:%M:%S'
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = Flask(__name__)

logger.info("正在初始化 Agent...")
orchestrator = initialize_dependencies()
logger.info("初始化完成 Agent...")


# ============================================================
# 认证 API（简化版 — 仅用户名登录，无密码）
# ============================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'success': False, 'message': '用户名不能为空'}), 400

    return jsonify({
        'success': True,
        'data': {
            'token': 'simple-auth-token',
            'userId': username,
            'username': username,
            'nickname': username,
            'role': 'user'
        }
    })


@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'success': False, 'message': '用户名不能为空'}), 400

    return jsonify({
        'success': True,
        'data': {
            'token': 'simple-auth-token',
            'userId': username,
            'username': username,
            'nickname': username,
            'role': 'user'
        }
    })


@app.route('/api/auth/me', methods=['GET'])
def me():
    auth = request.headers.get('Authorization', '')
    return jsonify({
        'success': True,
        'data': {
            'userId': auth.replace('Bearer ', '').strip() or 'anonymous',
            'username': 'anonymous',
            'nickname': 'anonymous',
            'role': 'user'
        }
    })


# ============================================================
# 工具管理 API（只读查看 + 启用/禁用）
# ============================================================

@app.route('/api/admin/tools', methods=['GET'])
def admin_get_tools():
    from tools.registry import get_registry
    registry = get_registry()
    metadata = registry.get_metadata()
    return jsonify({'success': True, 'data': metadata})


# 注意：categories 路由必须在 <name> 之前注册，否则 "categories" 会被 <name> 捕获
@app.route('/api/admin/tools/categories', methods=['GET'])
def admin_get_categories():
    categories = [
        {'id': 1, 'name': '订单管理', 'code': 'order', 'icon': 'shopping-cart', 'description': '订单相关工具'},
        {'id': 2, 'name': '用户管理', 'code': 'user', 'icon': 'user', 'description': '用户相关工具'},
        {'id': 3, 'name': '库存管理', 'code': 'inventory', 'icon': 'package', 'description': '库存相关工具'},
    ]
    return jsonify({'success': True, 'data': categories})


@app.route('/api/admin/tools/<name>', methods=['GET'])
def admin_get_tool(name):
    from tools.registry import get_registry
    registry = get_registry()
    for meta in registry.get_metadata():
        if meta['name'] == name:
            return jsonify({'success': True, 'data': meta})
    return jsonify({'success': False, 'message': f'工具不存在: {name}'}), 404


@app.route('/api/admin/tools/<name>/enable', methods=['POST'])
def admin_enable_tool(name):
    from tools.registry import get_registry
    registry = get_registry()
    registry.enable(name)
    return jsonify({'success': True, 'message': f'工具 {name} 已启用'})


@app.route('/api/admin/tools/<name>/disable', methods=['POST'])
def admin_disable_tool(name):
    from tools.registry import get_registry
    registry = get_registry()
    registry.disable(name)
    return jsonify({'success': True, 'message': f'工具 {name} 已禁用'})


# 以下为前端 ToolManagement 不支持操作的端点（返回友好提示）
@app.route('/api/admin/tools', methods=['POST'])
@app.route('/api/admin/tools/<int:_id>', methods=['PUT', 'DELETE'])
@app.route('/api/admin/tools/actions', methods=['POST'])
@app.route('/api/admin/tools/actions/<int:_id>', methods=['PUT', 'DELETE'])
@app.route('/api/admin/tools/categories', methods=['POST'])
@app.route('/api/admin/tools/categories/<int:_id>', methods=['PUT', 'DELETE'])
def admin_not_supported(_id=None):
    return jsonify({
        'success': False,
        'message': '工具已改为代码定义，不支持此操作。请修改 agent/tools/ 下的 Python 文件。'
    }), 400


# ============================================================
# 对话 API
# ============================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    user_id = data.get('userId', None)

    if not message:
        return jsonify({'success': False, 'message': '消息不能为空'}), 400

    try:
        logger.info(f"【收到请求】用户ID: {user_id}")
        logger.info(f"【收到请求】消息: {message[:100]}")
        response = orchestrator.process(message, user_id=user_id)
        logger.info(f"【返回响应】类型: {type(response).__name__}")
        logger.info(f"【返回响应】内容: {str(response)[:100]}")
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        logger.error(f"【处理失败】错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/tools/reload', methods=['POST'])
def reload_tools():
    try:
        from tools import create_all_tools
        new_tools = create_all_tools()
        orchestrator.set_tools(new_tools)
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
    return jsonify({
        'status': 'ok',
        'type': 'LangChain Agent (独立模式)'
    })


if __name__ == '__main__':
    from settings import get_settings
    settings = get_settings()
    app.run(
        host='0.0.0.0',
        port=settings.agent_port,
        debug=False
    )
