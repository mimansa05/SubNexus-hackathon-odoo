import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Mail } from 'lucide-react'
import { useAuth } from '../auth'
import { api, ApiError } from '../api'
import AuthCard from '../AuthCard'

export default function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [busy, setBusy] = useState(false)
  const [unverified, setUnverified] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(''); setInfo(''); setUnverified(false); setBusy(true)
    try {
      await signIn(email.trim(), password)
      navigate('/')
    } catch (err) {
      const ex = err as ApiError
      setError(ex.message)
      setUnverified(ex.status === 403 && /confirm your email/i.test(ex.message))
    } finally {
      setBusy(false)
    }
  }

  const resend = async () => {
    try {
      await api('/auth/resend-verification', { body: { email: email.trim() }, auth: false })
      setError(''); setUnverified(false)
      setInfo('A new confirmation email is on its way.')
    } catch (err) {
      setError((err as ApiError).message)
    }
  }

  return (
    <AuthCard title={<>Welcome <em>back</em></>}>
      <p className="auth-sub">Sign in to your workspace</p>
      <form className="auth-form" onSubmit={submit}>
        <label>Email
          <input type="email" required autoComplete="username" placeholder="you@company.com"
            value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>Password
          <input type="password" required autoComplete="current-password" placeholder="••••••••"
            value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error && <div className="msg bad" role="alert">{error}</div>}
        {info && <div className="msg good">{info}</div>}
        {unverified && <button type="button" className="btn" onClick={resend}><Mail size={13} /> Resend confirmation email</button>}
        <button className="btn dark" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
      </form>
      <p className="auth-foot">
        New customer? <Link to="/signup">Create an account</Link>
        <br /><small>Staff and admin accounts are created by an administrator.</small>
      </p>
    </AuthCard>
  )
}
