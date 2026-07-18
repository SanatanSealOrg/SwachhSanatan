import { create } from 'zustand'
import { api } from './api'

interface AuthState {
  token: string | null
  userId: string | null
  userType: string | null
  wardId: string | null
  email: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, userType: string) => Promise<void>
  logout: () => void
  loadProfile: () => Promise<void>
}

export const useAuth = create<AuthState>((set, get) => ({
  token: localStorage.getItem('cleanloop_token'),
  userId: localStorage.getItem('cleanloop_user_id'),
  userType: localStorage.getItem('cleanloop_user_type'),
  wardId: localStorage.getItem('cleanloop_ward_id'),
  email: localStorage.getItem('cleanloop_email'),

  login: async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    localStorage.setItem('cleanloop_token', data.access_token)
    localStorage.setItem('cleanloop_user_id', data.user_id)
    localStorage.setItem('cleanloop_email', email)
    set({ token: data.access_token, userId: data.user_id, email })
    await get().loadProfile()
  },

  register: async (email, password, userType) => {
    const { data } = await api.post('/auth/register', {
      email,
      password,
      user_type: userType,
    })
    localStorage.setItem('cleanloop_token', data.access_token)
    localStorage.setItem('cleanloop_user_id', data.user_id)
    localStorage.setItem('cleanloop_email', email)
    set({ token: data.access_token, userId: data.user_id, email })
    await get().loadProfile()
  },

  logout: () => {
    for (const k of [
      'cleanloop_token',
      'cleanloop_user_id',
      'cleanloop_user_type',
      'cleanloop_ward_id',
      'cleanloop_email',
    ])
      localStorage.removeItem(k)
    set({ token: null, userId: null, userType: null, wardId: null, email: null })
  },

  loadProfile: async () => {
    const { data } = await api.get('/auth/me')
    const user = data.user ?? data
    const userType = user.user_type ?? null
    const wardId = user.ward_id ?? null
    if (userType) localStorage.setItem('cleanloop_user_type', userType)
    if (wardId) localStorage.setItem('cleanloop_ward_id', wardId)
    set({ userType, wardId })
  },
}))
