import { api } from './client'

const publicCall = { skipAuth: true, skipRefresh: true }

export const authApi = {
  register: (payload) => api.post('/auth/register/', payload, publicCall).then((r) => r.data),
  login: (username, password) =>
    api.post('/auth/login/', { username, password }, publicCall).then((r) => r.data),
  logout: () => api.post('/auth/logout/', {}),
  me: () => api.get('/auth/me/').then((r) => r.data),
  updateProfile: (changes) => api.patch('/auth/me/', changes).then((r) => r.data),
  changePassword: (payload) => api.post('/auth/password/change/', payload).then((r) => r.data),
  requestPasswordReset: (email) =>
    api.post('/auth/password/reset/', { email }, publicCall).then((r) => r.data),
  confirmPasswordReset: (payload) =>
    api.post('/auth/password/reset/confirm/', payload, publicCall).then((r) => r.data),
}
