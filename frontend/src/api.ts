import axios from 'axios'

const apiUrl = import.meta.env.VITE_API_URL || '/api'
export const api = axios.create({ baseURL: apiUrl })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cleanloop_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export function errorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((d) => d.msg ?? String(d)).join('; ')
    return err.message
  }
  return String(err)
}
