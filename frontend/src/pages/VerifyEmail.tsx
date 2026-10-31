import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { CheckCircle2, XCircle } from 'lucide-react'
import { api, ApiError } from '../api'
import AuthCard from '../AuthCard'

export default function VerifyEmail() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const [state, setState] = useState<'loading' | 'ok' | 'error'>(token ? 'loading' : 'error')
  const [msg, setMsg] = useState(token ? '' : 'This confirmation link is incomplete.')
  const ran = useRef(false) // StrictMode runs effects twice in dev

  useEffect(() => {
    if (!token || ran.current) return
    ran.current = true
    api('/auth/verify-email', { body: { token }, auth: false })
      .then(() => setState('ok'))
      .catch((e: ApiError) => { setMsg(e.message); setState('error') })
  }, [token])

  return (
    <AuthCard title={state === 'ok' ? 'Email confirmed' : state === 'error' ? 'Link problem' : 'Confirming…'}>
      <div className="sent">
        {state === 'ok' && <CheckCircle2 size={34} color="var(--good)" />}
        {state === 'error' && <XCircle size={34} color="var(--bad)" />}
      </div>
      <p className="auth-sub center">
        {state === 'ok' ? 'Your account is active. You can sign in now.' : state === 'error' ? msg : 'Please wait a moment.'}
      </p>
      <Link className="btn dark" to="/login">Go to sign in</Link>
    </AuthCard>
  )
}
