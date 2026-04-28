import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { register } from '../services/api'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!username.trim()) {
      setError('请输入用户名')
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await register({ username: username.trim() })
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
        setError(res.message || '注册失败')
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
          <div className="login-logo">🚀</div>
          <h1 className="login-title">输入用户名</h1>
          <p className="login-subtitle">开始使用智能 Agent 系统</p>
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

          <button type="submit" className="login-button" disabled={loading}>
            {loading ? '进入中...' : '进 入'}
          </button>
        </form>

        <div className="login-footer">
          <p>已有账户？<a href="/login">立即进入</a></p>
        </div>
      </div>
    </div>
  )
}
