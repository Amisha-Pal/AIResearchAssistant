import { BrainCircuit } from 'lucide-react'
import { Link } from 'react-router-dom'

export function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <Link to="/" className="brand brand-center">
          <BrainCircuit size={28} aria-hidden="true" />
          <span>AI Research Assistant</span>
        </Link>
        <h1 id="auth-title">{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
        {children}
        {footer && <div className="auth-footer">{footer}</div>}
      </section>
    </main>
  )
}
