export default function StatsGrid({ analytics }) {
  if (!analytics) return null

  return (
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
          <div className="stat-value">
            {data.count} <small>({data.percentage}%)</small>
          </div>
          <div className="stat-label">{cat}</div>
        </div>
      ))}
    </div>
  )
}
