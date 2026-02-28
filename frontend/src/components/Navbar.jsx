import { NavLink } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav>
      <NavLink to="/">Chat</NavLink>
      <NavLink to="/dashboard">Dashboard</NavLink>
    </nav>
  )
}
