import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { MailCheck } from 'lucide-react'
import { api, ApiError } from '../api'
import AuthCard from '../AuthCard'

const POLICY = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z0-9]).{8,}$/

export default function Signup() {
  const [form, setForm] = useState({ full_name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [busy, setBusy] = useState(false)
  const [sentTo, setSentTo] = useState('')
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
      await api('/auth/register', { body: { ...form, email: form.email.trim() }, auth: false })
      setSentTo(form.email.trim())
    } catch (err) {
      setError((err as ApiError).message)
    } finally {
      setBusy(false)
    }
  }

  const resend = async () => {
    setInfo('')
    try {
      await api('/auth/resend-verification', { body: { email: sentTo }, auth: false })
      setInfo('Sent again. Check your inbox and spam folder.')
    } catch (err) {
      setError((err as ApiError).message)
    }
  }

  if (sentTo) {
    return (
      <AuthCard title="Check your email">
        <div className="sent"><MailCheck size={30} /></div>
        <p className="auth-sub center">
          We sent a confirmation link to <b>{sentTo}</b>. Open it to activate your account, then sign in.
        </p>
        {info && <div className="msg good">{info}</div>}
        {error && <div className="msg bad">{error}</div>}
        <button className="btn" onClick={resend}>Resend email</button>
        <Link className="btn dark" to="/login">Back to sign in</Link>
      </AuthCard>
    )
  }

  return (
    <AuthCard title={<>Create <em>account</em></>}>
      <p className="auth-sub">Customer sign-up. We'll email you a link to confirm your address.</p>
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
