import { useState, type FormEvent } from 'react'
import { Sparkles } from 'lucide-react'
import ListPage from '../ListPage'
import { Card, Pill } from '../ui'
import { api, ApiError } from '../api'
import { churn, money } from '../data'

/** Matches ChurnPredictionRequest in backend/app/schemas/churn.py */
interface Features {
  tenure_months: number
  monthly_charges: number
  payment_failures_90d: number
  days_since_last_payment: number
  support_tickets_90d: number
  usage_sessions_30d: number
  plan_type: 'Basic' | 'Standard' | 'Premium'
  discount_used: 0 | 1
  renewal_count: number
  auto_renew: 0 | 1
  late_payment_count: number
}

interface Result {
  churn_probability: number
  churn_percentage: number
  risk_level: 'Low' | 'Medium' | 'High'
  recommendation: string
  model_version: string
}

const NUMERIC: { key: keyof Features; label: string; min?: number }[] = [
  { key: 'tenure_months', label: 'Tenure (months)', min: 1 },
  { key: 'monthly_charges', label: 'Monthly charges ($)', min: 1 },
  { key: 'payment_failures_90d', label: 'Payment failures (90d)' },
  { key: 'days_since_last_payment', label: 'Days since last payment' },
  { key: 'late_payment_count', label: 'Late payments' },
  { key: 'support_tickets_90d', label: 'Support tickets (90d)' },
  { key: 'usage_sessions_30d', label: 'Usage sessions (30d)' },
  { key: 'renewal_count', label: 'Renewals so far' },
]

const SAMPLES: Record<string, Features> = {
  'At-risk customer': {
    tenure_months: 4, monthly_charges: 890, payment_failures_90d: 3, days_since_last_payment: 62, support_tickets_90d: 5,
    usage_sessions_30d: 2, plan_type: 'Premium', discount_used: 0, renewal_count: 0, auto_renew: 0, late_payment_count: 4,
  },
  'Loyal customer': {
    tenure_months: 36, monthly_charges: 199, payment_failures_90d: 0, days_since_last_payment: 8, support_tickets_90d: 0,
    usage_sessions_30d: 48, plan_type: 'Standard', discount_used: 1, renewal_count: 3, auto_renew: 1, late_payment_count: 0,
  },
}

const TONE = { Low: 'teal', Medium: 'orange', High: 'purple' } as const

function Predictor() {
  const [f, setF] = useState<Features>(SAMPLES['At-risk customer'])
  const [res, setRes] = useState<Result | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(''); setBusy(true)
    try {
      setRes(await api<Result>('/churn/predict', { body: f }))
    } catch (err) {
      setRes(null)
      setError((err as ApiError).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card title="Predict churn" action={
      <div className="tabs">
        {Object.keys(SAMPLES).map((k) => <button key={k} onClick={() => { setF(SAMPLES[k]); setRes(null) }}>{k}</button>)}
      </div>
    }>
      <form className="predict" onSubmit={submit}>
        <div className="predict-fields">
          {NUMERIC.map(({ key, label, min }) => (
            <label key={key}>{label}
              <input type="number" required min={min ?? 0} step={key === 'monthly_charges' ? '0.01' : '1'}
                value={f[key] as number} onChange={(e) => setF({ ...f, [key]: Number(e.target.value) })} />
            </label>
          ))}
          <label>Plan
            <select value={f.plan_type} onChange={(e) => setF({ ...f, plan_type: e.target.value as Features['plan_type'] })}>
              <option>Basic</option><option>Standard</option><option>Premium</option>
            </select>
          </label>
          <label className="check"><input type="checkbox" checked={!!f.auto_renew} onChange={(e) => setF({ ...f, auto_renew: e.target.checked ? 1 : 0 })} /> Auto-renew on</label>
          <label className="check"><input type="checkbox" checked={!!f.discount_used} onChange={(e) => setF({ ...f, discount_used: e.target.checked ? 1 : 0 })} /> Discount used</label>
        </div>

        <div className="predict-out">
          {res ? (
            <>
              <span className="eyebrow">Churn probability</span>
              <div className="big">{res.churn_percentage.toFixed(1)}%</div>
              <div className={`track ${TONE[res.risk_level]}`}><i style={{ width: `${res.churn_percentage}%` }} /></div>
              <div><Pill>{res.risk_level}</Pill></div>
              <p>{res.recommendation}</p>
              <small className="muted">Model: {res.model_version}</small>
            </>
          ) : (
            <div className="muted predict-empty"><Sparkles size={20} /><span>Enter customer signals and run the model.</span></div>
          )}
          {error && <div className="msg bad" role="alert">{error}</div>}
          <button className="btn dark" type="submit" disabled={busy}>{busy ? 'Predicting…' : 'Predict churn'}</button>
        </div>
      </form>
    </Card>
  )
}

export default function Insights() {
  return (
    <div className="stack">
      <div className="page-head">
        <div><h2>Churn prediction</h2><p>Random-forest model on payment, usage and renewal signals</p></div>
      </div>
      <Predictor />
      <ListPage
        statusKey="level" rows={churn}
        columns={[
          { key: 'customer', label: 'At-risk customers' },
          {
            key: 'score', label: 'Risk score',
            render: (r) => (
              <div className="conf">
                <div className={`track ${r.score > 65 ? 'purple' : r.score > 35 ? 'orange' : 'teal'}`}><i style={{ width: `${r.score}%` }} /></div>
                <small>{r.score}</small>
              </div>
            ),
          },
          { key: 'level', label: 'Level', render: (r) => <Pill>{r.level}</Pill> },
          { key: 'factors', label: 'Why', render: (r) => <div className="chips">{r.factors.map((x) => <span className="chip" key={x}>{x}</span>)}</div> },
          { key: 'atRisk', label: 'Revenue at risk', align: 'right', render: (r) => money(r.atRisk) },
          { key: 'action', label: 'Recommended' },
        ]}
      />
    </div>
  )
}
