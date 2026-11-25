import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { FullPageLoader } from '../components/ui/Spinner'
import { useAuth } from './useAuth'

export function ProtectedRoute() {
  const { status, loggedOut } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <FullPageLoader />
  if (status !== 'authenticated') {
    return <Navigate to="/login" replace state={loggedOut ? undefined : { from: location }} />
  }
  return <Outlet />
}

export function PublicOnlyRoute() {
  const { status } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <FullPageLoader />
  if (status === 'authenticated') return <Navigate to={location.state?.from?.pathname || '/dashboard'} replace />
  return <Outlet />
}
