import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

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
      const response = await api.get('/tools')
      if (response.data.success) {
        setTools(response.data.data || [])
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
      const action = tool.enabled ? 'disable' : 'enable'
      await api.post(`/tools/${tool.id}/${action}`)
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
              <th>操作</th>
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
                <td className="tool-name">{tool.name}</td>
                <td className="tool-description">{tool.description}</td>
                <td>
                  <span className="tool-action">{tool.actions || '-'}</span>
                </td>
                <td>
                  <span className={`tool-status ${tool.enabled ? 'enabled' : 'disabled'}`}>
                    {tool.enabled ? '已启用' : '已禁用'}
                  </span>
                </td>
                <td>
                  <button
                    className={`toggle-button ${tool.enabled ? 'disable' : 'enable'}`}
                    onClick={() => toggleEnabled(tool)}
                  >
                    {tool.enabled ? '禁用' : '启用'}
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
