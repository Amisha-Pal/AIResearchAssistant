import axios from 'axios'

const apiOrigin = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

// The access token lives only in memory. The refresh token is an httpOnly cookie
// set by the backend, so page scripts can never read it.
let accessToken = null
let sessionExpiredHandler = () => {}
let refreshPromise = null

export const tokenStore = {
  get: () => accessToken,
  set: (token) => {
    accessToken = token
  },
  clear: () => {
    accessToken = null
  },
}

export function setSessionExpiredHandler(handler) {
  sessionExpiredHandler = handler
}

export const api = axios.create({
  baseURL: `${apiOrigin}/api/v1`,
  withCredentials: true,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  if (accessToken && !config.skipAuth) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

function tokenUserId(token) {
  try {
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return String(JSON.parse(atob(payload)).user_id)
  } catch {
    return null
  }
}

/**
 * Exchange the refresh cookie for a new access token. Concurrent callers share one request.
 * Rejects if the cookie now belongs to a different account (e.g. after signing in as someone
 * else in another tab), so requests made for one user are never replayed as another.
 */
export function refreshAccessToken() {
  if (!refreshPromise) {
    const expectedUserId = accessToken ? tokenUserId(accessToken) : null
    refreshPromise = api
      .post('/auth/refresh/', {}, { skipAuth: true, skipRefresh: true })
      .then(({ data }) => {
        if (expectedUserId && tokenUserId(data.access) !== expectedUserId) {
          throw new Error('The session now belongs to a different account.')
        }
        accessToken = data.access
        return data.access
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error
    const canRetry = config && !config.skipRefresh && !config._retried && accessToken
    if (response?.status !== 401 || !canRetry) {
      throw error
    }
    config._retried = true
    try {
      await refreshAccessToken()
    } catch {
      accessToken = null
      sessionExpiredHandler()
      throw error
    }
    config.headers.Authorization = `Bearer ${accessToken}`
    return api(config)
  },
)
