import { Link } from 'react-router-dom'

import { AuthLayout } from '../components/layout/AuthLayout'

export default function NotFoundPage() {
  return (
    <AuthLayout title="Page not found" subtitle="The page you are looking for doesn't exist.">
      <Link to="/" className="btn btn-primary btn-block">
        Go home
      </Link>
    </AuthLayout>
  )
}
