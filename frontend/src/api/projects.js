import { api } from './client'

export const projectsApi = {
  list: (params = {}) => api.get('/projects/', { params }).then((r) => r.data),
}
