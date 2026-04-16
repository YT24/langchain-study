import React, { useState, useEffect, useRef } from 'react'
import {
  getTools, getCategories, getToolActions,
  createTool, updateTool, deleteTool,
  enableTool, disableTool,
  createCategory, deleteCategory
} from '../services/api'

export default function ToolManagement() {
  const [tools, setTools] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const mountedRef = useRef(false)

  // 搜索和过滤
  const [searchKeyword, setSearchKeyword] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')

  // 模态框状态
  const [showToolModal, setShowToolModal] = useState(false)
  const [showCategoryModal, setShowCategoryModal] = useState(false)
  const [editingTool, setEditingTool] = useState(null)
  const [editingCategory, setEditingCategory] = useState(null)
  const [toolActions, setToolActions] = useState([])

  // 表单数据
  const [toolForm, setToolForm] = useState({
    name: '', displayName: '', description: '', categoryId: '', version: '1.0', icon: 'box'
  })
  const [categoryForm, setCategoryForm] = useState({
    name: '', code: '', icon: 'folder', description: ''
  })

  useEffect(() => {
    if (mountedRef.current) return
    mountedRef.current = true
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const [toolsRes, categoriesRes] = await Promise.all([
        getTools(),
        getCategories()
      ])
      if (toolsRes.success) setTools(toolsRes.data || [])
      if (categoriesRes.success) setCategories(categoriesRes.data || [])
    } catch (e) {
      setError('加载失败: ' + (e.message || '网络错误'))
    } finally {
      setLoading(false)
    }
  }

  // 过滤工具
  const filteredTools = tools.filter(tool => {
    const matchKeyword = !searchKeyword ||
      (tool.name || '').toLowerCase().includes(searchKeyword.toLowerCase()) ||
      (tool.displayName || '').toLowerCase().includes(searchKeyword.toLowerCase())
    const matchCategory = !selectedCategory || tool.categoryId === Number(selectedCategory)
    return matchKeyword && matchCategory
  })

  // 工具表单提交
  const handleToolSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingTool) {
        await updateTool(editingTool.id, toolForm)
      } else {
        await createTool(toolForm)
      }
      setShowToolModal(false)
      resetToolForm()
      fetchData()
    } catch (e) {
      alert(editingTool ? '更新失败' : '创建失败')
    }
  }

  // 删除工具
  const handleDeleteTool = async (tool) => {
    if (!confirm(`确定删除工具 "${tool.displayName || tool.name}" 吗？`)) return
    try {
      await deleteTool(tool.id)
      fetchData()
    } catch (e) {
      alert('删除失败')
    }
  }

  // 切换工具状态
  const toggleToolStatus = async (tool) => {
    try {
      if (tool.status === 1) {
        await disableTool(tool.id)
      } else {
        await enableTool(tool.id)
      }
      fetchData()
    } catch (e) {
      alert('操作失败')
    }
  }

  // 打开工具编辑
  const openToolEdit = async (tool) => {
    setEditingTool(tool)
    setToolForm({
      name: tool.name,
      displayName: tool.displayName,
      description: tool.description,
      categoryId: tool.categoryId,
      version: tool.version,
      icon: tool.icon
    })
    // 获取该工具的动作
    try {
      const res = await getToolActions(tool.id)
      if (res.success) {
        setToolActions(res.data || [])
      }
    } catch (e) {}
    setShowToolModal(true)
  }

  // 新建工具
  const openToolCreate = () => {
    resetToolForm()
    setEditingTool(null)
    setToolActions([])
    setShowToolModal(true)
  }

  const resetToolForm = () => {
    setToolForm({ name: '', displayName: '', description: '', categoryId: '', version: '1.0', icon: 'box' })
    setToolActions([])
  }

  // 分类表单提交
  const handleCategorySubmit = async (e) => {
    e.preventDefault()
    try {
      await createCategory(categoryForm)
      setShowCategoryModal(false)
      setCategoryForm({ name: '', code: '', icon: 'folder', description: '' })
      fetchData()
    } catch (e) {
      alert('创建失败')
    }
  }

  // 删除分类
  const handleDeleteCategory = async (category) => {
    if (!confirm(`确定删除分类 "${category.name}" 吗？`)) return
    try {
      await deleteCategory(category.id)
      fetchData()
    } catch (e) {
      alert('删除失败')
    }
  }

  return (
    <div className="tool-container">
      {/* 顶部操作栏 */}
      <div className="tool-header">
        <div className="tool-filters">
          <input
            type="text"
            className="search-input"
            placeholder="搜索工具名称..."
            value={searchKeyword}
            onChange={e => setSearchKeyword(e.target.value)}
          />
          <select
            className="category-select"
            value={selectedCategory}
            onChange={e => setSelectedCategory(e.target.value)}
          >
            <option value="">全部分类</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
        </div>
        <div className="tool-actions">
          <button className="btn btn-secondary" onClick={() => setShowCategoryModal(true)}>
            + 添加工具分类
          </button>
          <button className="btn btn-primary" onClick={openToolCreate}>
            + 新建工具
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span>⚠️</span> {error}
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {/* 工具列表 */}
      {filteredTools.length > 0 ? (
        <div className="tool-grid">
          {filteredTools.map(tool => (
            <div key={tool.id} className={`tool-card ${tool.status === 0 ? 'disabled' : ''}`}>
              <div className="tool-card-header">
                <span className="tool-icon">{tool.icon || '📦'}</span>
                <div className="tool-info">
                  <h3>{tool.displayName || tool.name}</h3>
                  <span className="tool-name">{tool.name}</span>
                </div>
                <span className={`status-badge ${tool.status === 1 ? 'enabled' : 'disabled'}`}>
                  {tool.status === 1 ? '已启用' : '已禁用'}
                </span>
              </div>
              <p className="tool-desc">{tool.description || '暂无描述'}</p>
              <div className="tool-card-footer">
                <span className="tool-version">v{tool.version || '1.0'}</span>
                <div className="tool-card-actions">
                  <button className="btn-icon" onClick={() => toggleToolStatus(tool)} title={tool.status === 1 ? '禁用' : '启用'}>
                    {tool.status === 1 ? '⏸' : '▶'}
                  </button>
                  <button className="btn-icon" onClick={() => openToolEdit(tool)} title="编辑">✏️</button>
                  <button className="btn-icon danger" onClick={() => handleDeleteTool(tool)} title="删除">🗑</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : !loading ? (
        <div className="empty-state">
          <div className="empty-state-icon">📦</div>
          <p>{searchKeyword || selectedCategory ? '没有匹配的工具' : '暂无工具数据'}</p>
          {!searchKeyword && !selectedCategory && (
            <button className="btn btn-primary" onClick={openToolCreate}>创建第一个工具</button>
          )}
        </div>
      ) : null}

      {/* 工具模态框 */}
      {showToolModal && (
        <div className="modal-overlay" onClick={() => setShowToolModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingTool ? '编辑工具' : '新建工具'}</h2>
              <button className="modal-close" onClick={() => setShowToolModal(false)}>×</button>
            </div>
            <form onSubmit={handleToolSubmit}>
              <div className="form-group">
                <label>工具名称 *</label>
                <input
                  type="text"
                  value={toolForm.name}
                  onChange={e => setToolForm({...toolForm, name: e.target.value})}
                  required
                  placeholder="如: query_order_list"
                  disabled={!!editingTool}
                />
              </div>
              <div className="form-group">
                <label>显示名称 *</label>
                <input
                  type="text"
                  value={toolForm.displayName}
                  onChange={e => setToolForm({...toolForm, displayName: e.target.value})}
                  required
                  placeholder="如: 订单查询"
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  value={toolForm.description}
                  onChange={e => setToolForm({...toolForm, description: e.target.value})}
                  placeholder="工具功能描述"
                  rows={3}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>版本</label>
                  <input
                    type="text"
                    value={toolForm.version}
                    onChange={e => setToolForm({...toolForm, version: e.target.value})}
                    placeholder="1.0"
                  />
                </div>
                <div className="form-group">
                  <label>图标</label>
                  <input
                    type="text"
                    value={toolForm.icon}
                    onChange={e => setToolForm({...toolForm, icon: e.target.value})}
                    placeholder="📦"
                  />
                </div>
              </div>
              <div className="form-group">
                <label>分类</label>
                <select
                  value={toolForm.categoryId}
                  onChange={e => setToolForm({...toolForm, categoryId: e.target.value})}
                >
                  <option value="">未分类</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowToolModal(false)}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingTool ? '保存' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 分类模态框 */}
      {showCategoryModal && (
        <div className="modal-overlay" onClick={() => setShowCategoryModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>添加工具分类</h2>
              <button className="modal-close" onClick={() => setShowCategoryModal(false)}>×</button>
            </div>
            <div className="category-list">
              {categories.map(cat => (
                <div key={cat.id} className="category-item">
                  <span className="category-icon">{cat.icon}</span>
                  <span className="category-name">{cat.name}</span>
                  <span className="category-code">{cat.code}</span>
                  <button
                    className="btn-icon danger"
                    onClick={() => handleDeleteCategory(cat)}
                  >🗑</button>
                </div>
              ))}
            </div>
            <form onSubmit={handleCategorySubmit} className="category-form">
              <div className="form-row">
                <div className="form-group">
                  <label>分类名称 *</label>
                  <input
                    type="text"
                    value={categoryForm.name}
                    onChange={e => setCategoryForm({...categoryForm, name: e.target.value})}
                    required
                    placeholder="如: 订单工具"
                  />
                </div>
                <div className="form-group">
                  <label>编码 *</label>
                  <input
                    type="text"
                    value={categoryForm.code}
                    onChange={e => setCategoryForm({...categoryForm, code: e.target.value})}
                    required
                    placeholder="如: order"
                  />
                </div>
              </div>
              <div className="form-group">
                <label>图标</label>
                <input
                  type="text"
                  value={categoryForm.icon}
                  onChange={e => setCategoryForm({...categoryForm, icon: e.target.value})}
                  placeholder="📦"
                />
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCategoryModal(false)}>
                  关闭
                </button>
                <button type="submit" className="btn btn-primary">
                  添加分类
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <style>{`
        .tool-container {
          padding: 24px;
          height: 100%;
          overflow-y: auto;
        }

        .tool-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          flex-wrap: wrap;
          gap: 12px;
        }

        .tool-filters {
          display: flex;
          gap: 12px;
          flex: 1;
        }

        .search-input {
          flex: 1;
          max-width: 300px;
          padding: 10px 16px;
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
        }

        .search-input::placeholder {
          color: rgba(255, 255, 255, 0.5);
        }

        .category-select {
          padding: 10px 32px 10px 16px;
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          min-width: 150px;
          cursor: pointer;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23a0a0b0' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 12px center;
        }

        .category-select option {
          background: #1a1a2e;
          color: #fff;
          padding: 8px;
        }

        .tool-actions {
          display: flex;
          gap: 12px;
        }

        .btn {
          padding: 10px 20px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
          border: none;
        }

        .btn-primary {
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          color: #fff;
        }

        .btn-primary:hover {
          opacity: 0.9;
          transform: translateY(-1px);
        }

        .btn-secondary {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: rgba(255, 255, 255, 0.8);
        }

        .btn-secondary:hover {
          background: rgba(255, 255, 255, 0.1);
        }

        .tool-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 16px;
        }

        .tool-card {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 16px;
          transition: all 0.3s ease;
        }

        .tool-card:hover {
          border-color: rgba(99, 102, 241, 0.3);
          background: rgba(255, 255, 255, 0.05);
        }

        .tool-card.disabled {
          opacity: 0.5;
        }

        .tool-card-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;
        }

        .tool-icon {
          font-size: 24px;
        }

        .tool-info {
          flex: 1;
        }

        .tool-info h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #fff;
        }

        .tool-name {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.5);
        }

        .status-badge {
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
        }

        .status-badge.enabled {
          background: rgba(34, 197, 94, 0.15);
          color: #22c55e;
        }

        .status-badge.disabled {
          background: rgba(255, 255, 255, 0.05);
          color: rgba(255, 255, 255, 0.5);
        }

        .tool-desc {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.6);
          margin: 0 0 12px;
          line-height: 1.5;
        }

        .tool-card-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-top: 12px;
          border-top: 1px solid rgba(255, 255, 255, 0.05);
        }

        .tool-version {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.4);
        }

        .tool-card-actions {
          display: flex;
          gap: 8px;
        }

        .btn-icon {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          border: none;
          background: rgba(255, 255, 255, 0.05);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }

        .btn-icon:hover {
          background: rgba(255, 255, 255, 0.1);
        }

        .btn-icon.danger:hover {
          background: rgba(239, 68, 68, 0.2);
        }

        .error-message {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          color: #ef4444;
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 16px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .error-message button {
          background: none;
          border: none;
          color: #ef4444;
          font-size: 18px;
          cursor: pointer;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: rgba(255, 255, 255, 0.5);
        }

        .empty-state-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .empty-state p {
          margin: 0 0 20px;
        }

        /* Modal */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.6);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal {
          background: var(--bg-secondary);
          border-radius: 16px;
          width: 90%;
          max-width: 500px;
          max-height: 80vh;
          overflow-y: auto;
          border: 1px solid var(--border-subtle);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px 24px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .modal-header h2 {
          margin: 0;
          font-size: 18px;
          color: #fff;
        }

        .modal-close {
          background: none;
          border: none;
          color: rgba(255, 255, 255, 0.5);
          font-size: 24px;
          cursor: pointer;
        }

        .modal-close:hover {
          color: #fff;
        }

        .modal form {
          padding: 24px;
        }

        .form-group {
          margin-bottom: 16px;
        }

        .form-group label {
          display: block;
          margin-bottom: 6px;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.7);
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 10px 14px;
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          box-sizing: border-box;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: var(--accent-primary);
        }

        .form-group select option {
          background: #1a1a2e;
          color: #fff;
        }

        .form-group input:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .form-row {
          display: flex;
          gap: 12px;
        }

        .form-row .form-group {
          flex: 1;
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          padding-top: 16px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Category list */
        .category-list {
          padding: 0 24px;
          max-height: 200px;
          overflow-y: auto;
        }

        .category-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 0;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .category-icon {
          font-size: 18px;
        }

        .category-name {
          flex: 1;
          color: #fff;
        }

        .category-code {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.4);
          font-family: monospace;
        }

        .category-form {
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          margin-top: 0;
        }
      `}</style>
    </div>
  )
}
