import { CATEGORIES } from '../constants'

export default function CategoryFilter({ value, onChange }) {
  return (
    <div className="filter-row">
      <label>Filter by category:</label>
      <select value={value} onChange={e => onChange(e.target.value)}>
        <option value="">All</option>
        {CATEGORIES.map(c => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
    </div>
  )
}
