import { useState } from 'react'
import { sendMessage } from '../api'
import ChatInput from '../components/ChatInput'
import ChatResult from '../components/ChatResult'

export default function Chat() {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const send = async () => {
    if (!message.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const data = await sendMessage(message)
      setResult(data)
    } catch {
      setResult({ error: 'Failed to get response' })
    }
    setLoading(false)
    setMessage('')
  }

  return (
    <div>
      <h2>Chat</h2>
      <ChatInput
        message={message}
        setMessage={setMessage}
        onSend={send}
        loading={loading}
      />
      <ChatResult result={result} />
    </div>
  )
}
