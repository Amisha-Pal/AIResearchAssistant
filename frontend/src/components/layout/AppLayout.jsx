import { BrainCircuit, LayoutDashboard, LogOut, Menu, UserRound, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../../auth/useAuth'
import { Button } from '../ui/Button'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/profile', label: 'Profile', icon: UserRound },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)

  async function handleLogout() {
    setLoggingOut(true)
    await logout()
    navigate('/login', { replace: true })
  }

  const displayName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username

  return (
    <div className="app-shell">
      <header className="topbar">
        <span className="brand">
          <BrainCircuit size={24} aria-hidden="true" />
          <span>AI Research Assistant</span>
        </span>
        <button
          type="button"
          className="icon-btn menu-toggle"
          onClick={() => setMenuOpen((open) => !open)}
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
          aria-controls="sidebar"
        >
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </header>

      <aside id="sidebar" className={`sidebar ${menuOpen ? 'open' : ''}`}>
        <span className="brand sidebar-brand">
          <BrainCircuit size={24} aria-hidden="true" />
          <span>AI Research Assistant</span>
        </span>
        <nav aria-label="Main">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className="nav-link" onClick={() => setMenuOpen(false)}>
              <Icon size={18} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-chip" title={user?.email}>
            <span className="avatar" aria-hidden="true">
              {(displayName || '?').charAt(0).toUpperCase()}
            </span>
            <span className="user-chip-text">
              <strong>{displayName}</strong>
              <small>{user?.email}</small>
            </span>
          </div>
          <Button variant="ghost" onClick={handleLogout} loading={loggingOut} className="btn-block">
            <LogOut size={16} aria-hidden="true" /> Log out
          </Button>
        </div>
      </aside>
      {menuOpen && <div className="backdrop" onClick={() => setMenuOpen(false)} aria-hidden="true" />}

      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
