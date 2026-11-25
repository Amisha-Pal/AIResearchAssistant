import { LoaderCircle } from 'lucide-react'

export function Button({ loading = false, variant = 'primary', children, disabled, className = '', ...props }) {
  return (
    <button
      className={`btn btn-${variant} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && <LoaderCircle size={16} className="spin" aria-hidden="true" />}
      <span>{children}</span>
    </button>
  )
}
