import React, { useState } from 'react'
import ChatInterface from './ChatInterface'
import ToolManagement from './ToolManagement'

export default function Layout() {
  const [currentPage, setCurrentPage] = useState('agent')

  const pages = {
    agent: {
      title: 'Agent 问答',
      subtitle: '与 AI 助手对话，获取你想要的信息',
      icon: '💬'
    },
    tools: {
      title: 'Tool 管理',
      subtitle: '配置和管理 AI Agent 可用的工具',
      icon: '⚙️'
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
              <span className="nav-label">Agent 问答</span>
              <span className="nav-indicator"></span>
            </div>

            <div
              className={`nav-item ${currentPage === 'tools' ? 'active' : ''}`}
              onClick={() => setCurrentPage('tools')}
            >
              <span className="nav-icon">⚙️</span>
              <span className="nav-label">Tool 管理</span>
              <span className="nav-indicator"></span>
            </div>
          </nav>
        </aside>

        {/* 右侧内容 */}
        <main className="main-content">
          <header className="page-header">
            <h1 className="page-title">
              <span style={{ marginRight: '12px' }}>{current.icon}</span>
              {current.title}
            </h1>
            <p className="page-subtitle">{current.subtitle}</p>
          </header>

          <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {currentPage === 'agent' && <ChatInterface />}
            {currentPage === 'tools' && <ToolManagement />}
          </div>
        </main>
      </div>
    </div>
  )
}
