import { FolderOpen, ShieldCheck, UserRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { parseApiError } from '../api/errors'
import { projectsApi } from '../api/projects'
import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { Spinner } from '../components/ui/Spinner'

function RecentProjects() {
  const [state, setState] = useState({ status: 'loading', data: null, error: '' })
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    projectsApi
      .list({ page_size: 5, ordering: '-updated_at' })
      .then((data) => !cancelled && setState({ status: 'ready', data, error: '' }))
      .catch((error) => !cancelled && setState({ status: 'error', data: null, error: parseApiError(error).message }))
    return () => {
      cancelled = true
    }
  }, [reloadKey])

  const retry = () => {
    setState({ status: 'loading', data: null, error: '' })
    setReloadKey((k) => k + 1)
  }

  return (
    <section className="card" aria-labelledby="projects-heading">
      <header className="card-header">
        <FolderOpen size={20} aria-hidden="true" />
        <h2 id="projects-heading">Research projects</h2>
        {state.status === 'ready' && <span className="badge">{state.data.count}</span>}
      </header>
      {state.status === 'loading' && <Spinner label="Loading projects…" />}
      {state.status === 'error' && (
        <div className="form">
          <Alert type="error">{state.error}</Alert>
          <Button variant="ghost" onClick={retry}>
            Try again
          </Button>
        </div>
      )}
      {state.status === 'ready' &&
        (state.data.results.length === 0 ? (
          <p className="empty">
            No research projects yet. Creating projects and uploading papers comes in the next phase of the app.
          </p>
        ) : (
          <ul className="list">
            {state.data.results.map((project) => (
              <li key={project.id}>
                <strong>{project.title}</strong>
                <span className={`status status-${project.status}`}>{project.status}</span>
                <small className="muted">Updated {new Date(project.updated_at).toLocaleDateString()}</small>
              </li>
            ))}
          </ul>
        ))}
    </section>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const name = user.first_name || user.username
  const interests = user.research_interests || []

  return (
    <div className="page">
      <header className="page-header">
        <h1>Welcome, {name}</h1>
        <p className="muted">Your private research workspace.</p>
      </header>
      <div className="page-grid">
        <RecentProjects />
        <section className="card" aria-labelledby="account-heading">
          <header className="card-header">
            <UserRound size={20} aria-hidden="true" />
            <h2 id="account-heading">Account</h2>
          </header>
          <dl className="details">
            <dt>Email</dt>
            <dd>{user.email}</dd>
            <dt>Affiliation</dt>
            <dd>{user.affiliation || <span className="muted">Not set</span>}</dd>
            <dt>Research interests</dt>
            <dd>
              {interests.length ? (
                <span className="tags">
                  {interests.map((interest) => (
                    <span key={interest} className="tag">
                      {interest}
                    </span>
                  ))}
                </span>
              ) : (
                <span className="muted">Not set</span>
              )}
            </dd>
          </dl>
          <p className="secure-note">
            <ShieldCheck size={16} aria-hidden="true" /> Signed in securely. Sessions refresh automatically.
          </p>
          <Link to="/profile" className="btn btn-ghost">
            Edit profile
          </Link>
        </section>
      </div>
    </div>
  )
}
