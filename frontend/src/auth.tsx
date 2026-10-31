import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, getToken, setToken } from './api'

export type Role = 'admin' | 'staff' | 'customer'

interface Me { id: string; full_name: string | null; email: string; role: Role }
interface User { name: string; first: string; email: string }

interface Auth {
  role: Role | null
  user: User | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => void
}

const Ctx = createContext<Auth>(null as unknown as Auth)
export const useAuth = () => useContext(Ctx)

const toUser = (m: Me): User => {
  const name = m.full_name || m.email.split('@')[0]
  return { name, first: name.split(' ')[0], email: m.email }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null)
  const [loading, setLoading] = useState(!!getToken())

  // Restore the session from the stored token
  useEffect(() => {
    if (!getToken()) return
    api<Me>('/auth/me')
      .then(setMe)
      .catch(() => setToken(null))
      .finally(() => setLoading(false))
  }, [])

  const signIn = async (email: string, password: string) => {
    const { access_token } = await api<{ access_token: string }>('/auth/login', {
      body: { email, password }, auth: false,
    })
    setToken(access_token)
    setMe(await api<Me>('/auth/me'))
  }

  const signOut = () => {
    setToken(null)
    setMe(null)
  }

  return (
    <Ctx.Provider value={{ role: me?.role ?? null, user: me ? toUser(me) : null, loading, signIn, signOut }}>
      {children}
    </Ctx.Provider>
  )
}
