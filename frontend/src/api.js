import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const api = axios.create({ baseURL: API_BASE })

export function sendMessage(message) {
  return api.post('/chat', { message }).then(r => r.data)
}

export function fetchTraces(category = '') {
  const params = category ? { category } : {}
  return api.get('/traces', { params }).then(r => r.data)
}

export function fetchAnalytics() {
  return api.get('/analytics').then(r => r.data)
}

export default api
