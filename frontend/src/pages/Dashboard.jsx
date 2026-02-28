import { useState, useEffect } from 'react'
import { fetchTraces, fetchAnalytics } from '../api'
import StatsGrid from '../components/StatsGrid'
import CategoryFilter from '../components/CategoryFilter'
import TracesTable from '../components/TracesTable'

export default function Dashboard() {
  const [traces, setTraces] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    fetchTraces(filter).then(setTraces)
    fetchAnalytics().then(setAnalytics)
  }, [filter])

  return (
    <div>
      <h2>Dashboard</h2>
      <StatsGrid analytics={analytics} />
      <CategoryFilter value={filter} onChange={setFilter} />
      <TracesTable traces={traces} />
    </div>
  )
}
