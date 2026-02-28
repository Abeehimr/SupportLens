import React, { useState } from 'react'

export default function TracesTable({ traces }) {
  const [expanded, setExpanded] = useState(null)

  const toggle = id => setExpanded(prev => (prev === id ? null : id))

  if (traces.length === 0) {
    return <p style={{ marginTop: '1rem', color: '#888' }}>No traces yet.</p>
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>User Message</th>
          <th>Category</th>
          <th>Response Time</th>
        </tr>
      </thead>
      <tbody>
        {traces.map(t => (
          <React.Fragment key={t.id}>
            <tr className="clickable" onClick={() => toggle(t.id)}>
              <td>{new Date(t.timestamp).toLocaleString()}</td>
              <td>{t.user_message}</td>
              <td><span className="badge">{t.category}</span></td>
              <td>{t.response_time_ms}ms</td>
            </tr>
            {expanded === t.id && (
              <tr className="expanded-row">
                <td colSpan={4}>
                  <div className="expanded-content">
                    <strong>Bot Response:</strong>
                    <p>{t.bot_response}</p>
                  </div>
                </td>
              </tr>
            )}
          </React.Fragment>
        ))}
      </tbody>
    </table>
  )
}
