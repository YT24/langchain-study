import React, { useState, useEffect, useRef } from 'react'
import { getTools, enableTool, disableTool } from '../services/api'

export default function ToolManagement() {
  const [tools, setTools] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const mountedRef = useRef(false)

  useEffect(() => {
    if (mountedRef.current) return
    mountedRef.current = true
    fetchTools()
  }, [])

  const fetchTools = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await getTools()
      if (response.success) {
        setTools(response.data || [])
      } else {
        setError('加载失败')
      }
    } catch (e) {
      setError('加载失败: ' + (e.message || '网络错误'))
    } finally {
      setLoading(false)
    }
  }

  const toggleEnabled = async (tool) => {
    try {
      if (tool.status === 1) {
        await disableTool(tool.id)
      } else {
        await enableTool(tool.id)
      }
      fetchTools()
    } catch (e) {
      alert('操作失败')
    }
  }

  return (
    <div className="tool-container">
      <div className="tool-header">
        <div className="tool-count">
          共 <span>{tools.length}</span> 个工具
        </div>
        <button
          className="refresh-button"
          onClick={fetchTools}
          disabled={loading}
        >
          <span className="refresh-icon">↻</span>
          {loading ? '刷新中...' : '刷新列表'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <span>⚠️</span>
          {error}
        </div>
      )}

      {tools.length > 0 ? (
        <table className="tool-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>描述</th>
              <th>版本</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {tools.map(tool => (
              <tr key={tool.id}>
                <td>
                  <span className="tool-id">{tool.id}</span>
                </td>
                <td className="tool-name">{tool.displayName || tool.name}</td>
                <td className="tool-description">{tool.description}</td>
                <td>
                  <span className="tool-action">{tool.version || '1.0'}</span>
                </td>
                <td>
                  <span className={`tool-status ${tool.status === 1 ? 'enabled' : 'disabled'}`}>
                    {tool.status === 1 ? '已启用' : '已禁用'}
                  </span>
                </td>
                <td>
                  <button
                    className={`toggle-button ${tool.status === 1 ? 'disable' : 'enable'}`}
                    onClick={() => toggleEnabled(tool)}
                  >
                    {tool.status === 1 ? '禁用' : '启用'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : !loading && !error ? (
        <div className="empty-state">
          <div className="empty-state-icon">📦</div>
          <p>暂无工具数据</p>
        </div>
      ) : null}
    </div>
  )
}
