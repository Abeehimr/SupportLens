export default function ChatResult({ result }) {
  if (!result) return null

  if (result.error) {
    return <p className="error">{result.error}</p>
  }

  return (
    <div className="chat-result">
      <div className="chat-meta">
        <span className="badge">{result.category}</span>
        <span className="time">{result.response_time_ms}ms</span>
      </div>
      <p>{result.bot_response}</p>
    </div>
  )
}
