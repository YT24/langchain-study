import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

export const sendMessage = async (message) => {
  const response = await api.post('/chat', { message })
  return response.data
}
