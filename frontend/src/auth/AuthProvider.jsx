import { useCallback, useEffect, useMemo, useState } from 'react'

import { authApi } from '../api/auth'
import { isServerUnreachable } from '../api/errors'
import { refreshAccessToken, setSessionExpiredHandler, tokenStore } from '../api/client'
import { AuthContext } from './auth-context'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading') // loading | authenticated | anonymous
  const [notice, setNotice] = useState('')

  const startSession = useCallback((data) => {
    tokenStore.set(data.access)
    setUser(data.user)
    setStatus('authenticated')
    setNotice('')
  }, [])

  const endSession = useCallback((message = '') => {
    tokenStore.clear()
    setUser(null)
    setStatus('anonymous')
    setNotice(message)
  }, [])

  useEffect(() => {
    setSessionExpiredHandler(() => endSession('Your session has expired. Please log in again.'))
    let cancelled = false
    // Restore the session from the httpOnly refresh cookie after a page load.
    refreshAccessToken()
      .then(() => authApi.me())
      .then((me) => {
        if (cancelled) return
        setUser(me)
        setStatus('authenticated')
      })
      .catch(() => {
        if (cancelled) return
        tokenStore.clear()
        setStatus('anonymous')
      })
    return () => {
      cancelled = true
    }
  }, [endSession])

  const login = useCallback(
    async (identifier, password) => startSession(await authApi.login(identifier, password)),
    [startSession],
  )

  const register = useCallback(
    async (payload) => startSession(await authApi.register(payload)),
    [startSession],
  )

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch (error) {
      // Only a server-side revocation ends the session; a rejected (4xx) token is already unusable.
      if (isServerUnreachable(error) || error.response.status >= 500) throw error
    }
    endSession()
  }, [endSession])

  const changePassword = useCallback(
    async (payload) => startSession(await authApi.changePassword(payload)),
    [startSession],
  )

  const value = useMemo(
    () => ({
      user,
      status,
      isAuthenticated: status === 'authenticated',
      notice,
      clearNotice: () => setNotice(''),
      login,
      register,
      logout,
      changePassword,
      setUser,
    }),
    [user, status, notice, login, register, logout, changePassword],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
