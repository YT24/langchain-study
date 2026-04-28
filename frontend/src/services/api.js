import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

// 请求拦截器 - 添加 Token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ========== 认证 ==========
export const login = (data) => api.post('/auth/login', data)
export const register = (data) => api.post('/auth/register', data)
export const getCurrentUser = () => api.get('/auth/me')

// ========== 工具管理 ==========
export const getTools = () => api.get('/admin/tools')
export const getToolById = (id) => api.get(`/admin/tools/${id}`)
export const createTool = (data) => api.post('/admin/tools', data)
export const updateTool = (id, data) => api.put(`/admin/tools/${id}`, data)
export const deleteTool = (id) => api.delete(`/admin/tools/${id}`)
export const enableTool = (name) => api.post(`/admin/tools/${encodeURIComponent(name)}/enable`)
export const disableTool = (name) => api.post(`/admin/tools/${encodeURIComponent(name)}/disable`)

// ========== 工具分类 ==========
export const getCategories = () => api.get('/admin/tools/categories')
export const createCategory = (data) => api.post('/admin/tools/categories', data)
export const updateCategory = (id, data) => api.put(`/admin/tools/categories/${id}`, data)
export const deleteCategory = (id) => api.delete(`/admin/tools/categories/${id}`)

// ========== 工具动作 ==========
export const getToolActions = (toolId) => api.get(`/admin/tools/${toolId}/actions`)
export const createAction = (data) => api.post('/admin/tools/actions', data)
export const updateAction = (id, data) => api.put(`/admin/tools/actions/${id}`, data)
export const deleteAction = (id) => api.delete(`/admin/tools/actions/${id}`)

// ========== AI 对话 ==========
export const sendChatMessage = (message, userId) => api.post('/chat', { message, userId })
export const sendMessage = sendChatMessage

export default api
