import { useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function Chat() {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const send = async () => {
    if (!message.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const { data } = await axios.post(`${API}/chat`, { message })
      setResult(data)
    } catch (e) {
      setResult({ error: 'Failed to get response' })
    }
    setLoading(false)
    setMessage('')
  }

  return (
    <div>
      <h2>Chat</h2>
      <div className="chat-input">
        <input
          value={message}
          onChange={e => setMessage(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Type your support question..."
          disabled={loading}
        />
        <button onClick={send} disabled={loading || !message.trim()}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
      {result && !result.error && (
        <div className="chat-result">
          <div className="chat-meta">
            <span className="badge">{result.category}</span>
            <span className="time">{result.response_time_ms}ms</span>
          </div>
          <p>{result.bot_response}</p>
        </div>
      )}
      {result?.error && <p className="error">{result.error}</p>}
    </div>
  )
}
