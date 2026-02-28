import axios from 'axios'

// In production (served by nginx) the API is reverse-proxied on /api,
// so we use a relative path.  During local dev, VITE_API_BASE can be set
// to e.g. "http://localhost:8000".
const API_BASE = import.meta.env.VITE_API_BASE || '/api'

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
