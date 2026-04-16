import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../services/api'

export default function LoginPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!username || !password) {
      setError('请输入用户名和密码')
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await login({ username, password, rememberMe })
      if (res.success) {
        localStorage.setItem('token', res.data.token)
        localStorage.setItem('user', JSON.stringify({
          userId: res.data.userId,
          username: res.data.username,
          nickname: res.data.nickname,
          role: res.data.role
        }))
        navigate('/chat')
      } else {
        setError(res.message || '登录失败')
      }
    } catch (err) {
      setError(err.response?.data?.message || '网络错误，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">🤖</div>
          <h1 className="login-title">智能 Agent 系统</h1>
          <p className="login-subtitle">登录您的账户</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && <div className="login-error">{error}</div>}

          <div className="form-group">
            <label className="form-label">用户名</label>
            <input
              type="text"
              className="form-input"
              placeholder="请输入用户名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label className="form-label">密码</label>
            <div className="password-input-wrapper">
              <input
                type="password"
                className="form-input"
                placeholder="请输入密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
              <button type="button" className="password-toggle">👁</button>
            </div>
          </div>

          <div className="form-group form-group-inline">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <span>记住我</span>
            </label>
          </div>

          <button type="submit" className="login-button" disabled={loading}>
            {loading ? '登录中...' : '登 录'}
          </button>
        </form>

        <div className="login-footer">
          <p>还没有账户？<a href="/register">注册账号</a></p>
        </div>
      </div>

      <style>{`
        .login-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
          padding: 20px;
        }

        .login-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 24px;
          padding: 48px 40px;
          width: 100%;
          max-width: 420px;
          backdrop-filter: blur(20px);
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .login-header {
          text-align: center;
          margin-bottom: 40px;
        }

        .login-logo {
          font-size: 64px;
          margin-bottom: 16px;
          animation: float 3s ease-in-out infinite;
        }

        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }

        .login-title {
          font-size: 28px;
          font-weight: 700;
          color: #fff;
          margin: 0 0 8px;
          font-family: 'SF Pro Display', -apple-system, sans-serif;
        }

        .login-subtitle {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.5);
          margin: 0;
        }

        .login-form {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .login-error {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: 8px;
          padding: 12px 16px;
          color: #ef4444;
          font-size: 14px;
          text-align: center;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .form-group-inline {
          flex-direction: row;
          align-items: center;
          justify-content: space-between;
        }

        .form-label {
          font-size: 14px;
          font-weight: 500;
          color: rgba(255, 255, 255, 0.8);
        }

        .form-input {
          width: 100%;
          padding: 14px 16px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          color: #fff;
          font-size: 15px;
          transition: all 0.3s ease;
          box-sizing: border-box;
        }

        .form-input::placeholder {
          color: rgba(255, 255, 255, 0.3);
        }

        .form-input:focus {
          outline: none;
          border-color: rgba(99, 102, 241, 0.5);
          background: rgba(255, 255, 255, 0.08);
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .password-input-wrapper {
          position: relative;
        }

        .password-input-wrapper .form-input {
          padding-right: 48px;
        }

        .password-toggle {
          position: absolute;
          right: 12px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          cursor: pointer;
          font-size: 18px;
          opacity: 0.5;
          transition: opacity 0.3s;
        }

        .password-toggle:hover {
          opacity: 1;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          color: rgba(255, 255, 255, 0.6);
          font-size: 14px;
        }

        .checkbox-label input[type="checkbox"] {
          width: 18px;
          height: 18px;
          accent-color: #6366f1;
        }

        .login-button {
          width: 100%;
          padding: 16px;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          border: none;
          border-radius: 12px;
          color: #fff;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          margin-top: 8px;
        }

        .login-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 40px -10px rgba(99, 102, 241, 0.5);
        }

        .login-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .login-footer {
          margin-top: 32px;
          text-align: center;
          color: rgba(255, 255, 255, 0.5);
          font-size: 14px;
        }

        .login-footer a {
          color: #6366f1;
          text-decoration: none;
          font-weight: 500;
        }

        .login-footer a:hover {
          text-decoration: underline;
        }
      `}</style>
    </div>
  )
}
