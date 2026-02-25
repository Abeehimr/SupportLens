import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

const CATEGORIES = ['Billing', 'Refund', 'Account Access', 'Cancellation', 'General Inquiry']

export default function Dashboard() {
  const [traces, setTraces] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [filter, setFilter] = useState('')
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    const params = filter ? `?category=${encodeURIComponent(filter)}` : ''
    axios.get(`${API}/traces${params}`).then(r => setTraces(r.data))
    axios.get(`${API}/analytics`).then(r => setAnalytics(r.data))
  }, [filter])

  return (
    <div>
      <h2>Dashboard</h2>

      {analytics && (
        <div className="analytics">
          <div className="stat-card">
            <div className="stat-value">{analytics.total}</div>
            <div className="stat-label">Total Traces</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{analytics.avg_response_time_ms}ms</div>
            <div className="stat-label">Avg Response Time</div>
          </div>
          {Object.entries(analytics.categories).map(([cat, data]) => (
            <div className="stat-card" key={cat}>
              <div className="stat-value">{data.count} <small>({data.percentage}%)</small></div>
              <div className="stat-label">{cat}</div>
            </div>
          ))}
        </div>
      )}

      <div className="filter-row">
        <label>Filter by category:</label>
        <select value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="">All</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

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
              <tr className="clickable" onClick={() => setExpanded(expanded === t.id ? null : t.id)}>
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
      {traces.length === 0 && <p style={{ marginTop: '1rem', color: '#888' }}>No traces yet.</p>}
    </div>
  )
}
