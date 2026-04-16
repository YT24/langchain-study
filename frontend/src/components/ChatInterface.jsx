import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { sendMessage } from '../services/api'

export default function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const userId = user.userId
      const result = await sendMessage(userMessage, userId)
      if (result.success) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: result.response || '处理完成，无返回内容'
        }])
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: '处理失败: ' + (result.message || '未知错误')
        }])
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message || '网络错误，请稍后重试'
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '错误: ' + errorMsg
      }])
      console.error('Chat error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-container">
      {messages.length === 0 ? (
        <div className="chat-empty">
          <div className="empty-icon">🤖</div>
          <h2 className="empty-title">开始与 Agent 对话</h2>
          <p className="empty-text">
            输入您的问题，AI Agent 会尽力为您解答。例如：&quot;帮我查一下用户 U001 的订单&quot;
          </p>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'assistant' ? '⬡' : '👤'}
              </div>
              <div className="message-bubble">
                <div className="markdown-content">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <div className="message-avatar">⬡</div>
              <div className="message-bubble">
                <div className="loading-indicator">
                  <div className="loading-dots">
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                  </div>
                  <span className="loading-text">思考中...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入您的问题..."
            rows={1}
          />
          <button
            className="send-button"
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  )
}
