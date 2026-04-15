import React, { useState, useEffect } from 'react'
import ChatInterface from './ChatInterface'
import ToolManagement from './ToolManagement'

export default function Layout() {
  const [currentPage, setCurrentPage] = useState('agent')
  const [user, setUser] = useState(null)

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  const pages = {
    agent: {
      title: 'AI 对话',
      subtitle: '与 AI 助手对话，获取你想要的信息',
      icon: '💬'
    },
    tools: {
      title: '工具管理',
      subtitle: '配置和管理 AI Agent 可用的工具',
      icon: '🛠'
    }
  }

  const current = pages[currentPage]

  return (
    <div className="app-container">
      <div className="layout">
        {/* 左侧菜单 */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <div className="logo">
              <div className="logo-icon">⬡</div>
              <span>Agent Hub</span>
            </div>
          </div>

          <nav className="sidebar-nav">
            <div
              className={`nav-item ${currentPage === 'agent' ? 'active' : ''}`}
              onClick={() => setCurrentPage('agent')}
            >
              <span className="nav-icon">💬</span>
              <span className="nav-label">AI 对话</span>
              <span className="nav-indicator"></span>
            </div>

            <div
              className={`nav-item ${currentPage === 'tools' ? 'active' : ''}`}
              onClick={() => setCurrentPage('tools')}
            >
              <span className="nav-icon">🛠</span>
              <span className="nav-label">工具管理</span>
              <span className="nav-indicator"></span>
            </div>
          </nav>
        </aside>

        {/* 右侧内容 */}
        <main className="main-content">
          <header className="page-header">
            <div className="header-left">
              <h1 className="page-title">
                <span style={{ marginRight: '12px' }}>{current.icon}</span>
                {current.title}
              </h1>
              <p className="page-subtitle">{current.subtitle}</p>
            </div>
            <div className="header-right">
              <div className="user-info">
                <span className="user-avatar">{user?.nickname?.[0] || 'U'}</span>
                <span className="user-name">{user?.nickname || user?.username || '用户'}</span>
              </div>
              <button className="logout-btn" onClick={handleLogout}>
                退出
              </button>
            </div>
          </header>

          <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {currentPage === 'agent' && <ChatInterface />}
            {currentPage === 'tools' && <ToolManagement />}
          </div>
        </main>
      </div>

      <style>{`
        .header-right {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .user-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          font-weight: 600;
          font-size: 14px;
        }

        .user-name {
          color: rgba(255, 255, 255, 0.9);
          font-size: 14px;
          font-weight: 500;
        }

        .logout-btn {
          padding: 8px 16px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: rgba(255, 255, 255, 0.7);
          font-size: 13px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .logout-btn:hover {
          background: rgba(239, 68, 68, 0.1);
          border-color: rgba(239, 68, 68, 0.3);
          color: #ef4444;
        }
      `}</style>
    </div>
  )
}
