import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api'
import { useAuth } from '../auth'
import AuthCard from '../AuthCard'

const POLICY = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z0-9]).{8,}$/

export default function Signup() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ full_name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    if (!POLICY.test(form.password)) {
      setError('Password needs at least 8 characters with an uppercase letter, a lowercase letter and a special character.')
      return
    }
    setBusy(true)
    try {
      const email = form.email.trim()
      await api('/auth/register', { body: { ...form, email }, auth: false })
      await signIn(email, form.password) // account is active immediately
      navigate('/')
    } catch (err) {
      setError((err as ApiError).message)
      setBusy(false)
    }
  }

  return (
    <AuthCard title={<>Create <em>account</em></>}>
      <p className="auth-sub">Customer sign-up. You'll be signed in right away.</p>
      <form className="auth-form" onSubmit={submit}>
        <label>Full name<input required minLength={2} autoComplete="name" value={form.full_name} onChange={set('full_name')} /></label>
        <label>Email<input type="email" required autoComplete="email" value={form.email} onChange={set('email')} /></label>
        <label>Password
          <input type="password" required autoComplete="new-password" value={form.password} onChange={set('password')} />
          <small>8+ characters, with upper and lower case and a special character.</small>
        </label>
        {error && <div className="msg bad" role="alert">{error}</div>}
        <button className="btn dark" type="submit" disabled={busy}>{busy ? 'Creating…' : 'Create account'}</button>
      </form>
      <p className="auth-foot">Already have an account? <Link to="/login">Sign in</Link></p>
    </AuthCard>
  )
}
