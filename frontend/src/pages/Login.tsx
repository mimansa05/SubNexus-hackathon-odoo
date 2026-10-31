import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { ApiError } from '../api'
import AuthCard from '../AuthCard'

export default function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(''); setBusy(true)
    try {
      await signIn(email.trim(), password)
      navigate('/')
    } catch (err) {
      setError((err as ApiError).message)
      setBusy(false)
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
        <button className="btn dark" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
      </form>
      <p className="auth-foot">
        New customer? <Link to="/signup">Create an account</Link>
        <br /><small>Staff and admin accounts are created by an administrator.</small>
      </p>
    </AuthCard>
  )
}
