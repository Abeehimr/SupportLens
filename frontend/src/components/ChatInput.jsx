export default function ChatInput({ message, setMessage, onSend, loading }) {
  return (
    <div className="chat-input">
      <input
        value={message}
        onChange={e => setMessage(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && onSend()}
        placeholder="Type your support question..."
        disabled={loading}
      />
      <button onClick={onSend} disabled={loading || !message.trim()}>
        {loading ? 'Sending...' : 'Send'}
      </button>
    </div>
  )
}
