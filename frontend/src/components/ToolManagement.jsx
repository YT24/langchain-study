import React, { useState, useEffect, useRef } from 'react'
import { getTools, getCategories, enableTool, disableTool } from '../services/api'

export default function ToolManagement() {
  const [tools, setTools] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const mountedRef = useRef(false)

  const [searchKeyword, setSearchKeyword] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [expandedTool, setExpandedTool] = useState(null)

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

  const filteredTools = tools.filter(tool => {
    const matchKeyword = !searchKeyword ||
      (tool.name || '').toLowerCase().includes(searchKeyword.toLowerCase()) ||
      (tool.displayName || '').toLowerCase().includes(searchKeyword.toLowerCase())
    const matchCategory = !selectedCategory || tool.categoryId === Number(selectedCategory)
    return matchKeyword && matchCategory
  })

  const toggleExpandTool = (tool) => {
    setExpandedTool(expandedTool === tool.name ? null : tool.name)
  }

  const toggleToolStatus = async (tool) => {
    try {
      if (tool.status === 1) {
        await disableTool(tool.name)
      } else {
        await enableTool(tool.name)
      }
      fetchData()
    } catch (e) {
      alert('操作失败')
    }
  }

  return (
    <div className="tool-container">
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
        <div className="tool-hint">
          工具由代码定义，修改请编辑 agent/tools/*.py
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span>⚠️</span> {error}
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {filteredTools.length > 0 ? (
        <div className="tool-list">
          {filteredTools.map(tool => (
            <div key={tool.name} className={`tool-card ${tool.status === 0 ? 'disabled' : ''} ${expandedTool === tool.name ? 'expanded' : ''}`}>
              <div className="tool-card-main" onClick={() => toggleExpandTool(tool)}>
                <div className="tool-card-header">
                  <span className="expand-icon">{expandedTool === tool.name ? '▼' : '▶'}</span>
                  <span className="tool-icon">{tool.icon || '📦'}</span>
                  <div className="tool-info">
                    <h3>{tool.displayName || tool.name}</h3>
                    <span className="tool-name">{tool.name}</span>
                  </div>
                  <span className={`status-badge ${tool.status === 1 ? 'enabled' : 'disabled'}`}>
                    {tool.status === 1 ? '已启用' : '已禁用'}
                  </span>
                </div>
                <div className="tool-card-actions" onClick={e => e.stopPropagation()}>
                  <button className="btn-icon" onClick={() => toggleToolStatus(tool)} title={tool.status === 1 ? '禁用' : '启用'}>
                    {tool.status === 1 ? '⏸' : '▶'}
                  </button>
                </div>
              </div>

              {expandedTool === tool.name && (
                <div className="tool-actions-panel">
                  <div className="actions-header">
                    <h4>参数列表 ({tool.params?.length || 0})</h4>
                  </div>
                  {tool.params?.length > 0 ? (
                    <div className="actions-list">
                      {tool.params.map((param, idx) => (
                        <div key={idx} className="action-item">
                          <div className="action-info">
                            <div className="action-header-row">
                              <span className="action-name">{param.name}</span>
                              <span className={`method-badge ${param.required ? 'POST' : 'GET'}`}>
                                {param.required ? '必填' : '可选'}
                              </span>
                              <span className="param-type">{param.type}</span>
                            </div>
                            <span className="action-desc">{param.description || '暂无描述'}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="actions-empty">无参数</div>
                  )}
                  {tool.description && (
                    <div className="tool-description">
                      <strong>描述：</strong>{tool.description}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : !loading ? (
        <div className="empty-state">
          <div className="empty-state-icon">📦</div>
          <p>{searchKeyword || selectedCategory ? '没有匹配的工具' : '暂无已注册的工具'}</p>
        </div>
      ) : null}

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

        .tool-hint {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.35);
          font-style: italic;
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

        .tool-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .tool-card {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          overflow: hidden;
          transition: all 0.3s ease;
        }

        .tool-card:hover {
          border-color: rgba(99, 102, 241, 0.3);
        }

        .tool-card.disabled {
          opacity: 0.6;
        }

        .tool-card.expanded {
          border-color: rgba(99, 102, 241, 0.5);
        }

        .tool-card-main {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px;
          cursor: pointer;
        }

        .tool-card-header {
          display: flex;
          align-items: center;
          gap: 12px;
          flex: 1;
        }

        .expand-icon {
          color: rgba(255, 255, 255, 0.4);
          font-size: 12px;
          width: 16px;
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
          font-size: 14px;
        }

        .btn-icon:hover {
          background: rgba(255, 255, 255, 0.1);
        }

        .tool-actions-panel {
          background: rgba(0, 0, 0, 0.2);
          border-top: 1px solid rgba(255, 255, 255, 0.08);
          padding: 16px;
        }

        .actions-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .actions-header h4 {
          margin: 0;
          font-size: 14px;
          color: rgba(255, 255, 255, 0.7);
        }

        .actions-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .action-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .action-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
          flex: 1;
        }

        .action-header-row {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .action-name {
          font-weight: 500;
          color: #fff;
          font-family: monospace;
        }

        .action-desc {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.4);
        }

        .param-type {
          font-size: 11px;
          color: rgba(168, 85, 247, 0.8);
          background: rgba(168, 85, 247, 0.15);
          padding: 2px 6px;
          border-radius: 4px;
          font-family: monospace;
        }

        .method-badge {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
          font-family: monospace;
        }

        .method-badge.POST {
          background: rgba(239, 68, 68, 0.2);
          color: #ef4444;
        }

        .method-badge.GET {
          background: rgba(59, 130, 246, 0.2);
          color: #3b82f6;
        }

        .actions-empty {
          text-align: center;
          padding: 20px;
          color: rgba(255, 255, 255, 0.4);
          font-size: 13px;
        }

        .tool-description {
          margin-top: 12px;
          padding: 10px 12px;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 8px;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.5);
        }

        .tool-description strong {
          color: rgba(255, 255, 255, 0.7);
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
          margin: 0;
        }
      `}</style>
    </div>
  )
}
