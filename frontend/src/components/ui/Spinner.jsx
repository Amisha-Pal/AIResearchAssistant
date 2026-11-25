import { LoaderCircle } from 'lucide-react'

export function Spinner({ size = 18, label }) {
  return (
    <span className="spinner" role="status" aria-label={label || 'Loading'}>
      <LoaderCircle size={size} className="spin" aria-hidden="true" />
      {label && <span>{label}</span>}
    </span>
  )
}

export function FullPageLoader() {
  return (
    <div className="full-page-loader">
      <Spinner size={28} label="Loading…" />
    </div>
  )
}
