import { useEffect, useRef, useState } from 'react'
import { Bot, Check, CircleDashed, Send, Wrench, X } from 'lucide-react'
import { Card, Pill } from '../ui'
import { api } from '../api'

/* Front-end orchestrator demo. Routing and plans are simulated; the churn tool calls the real backend model. */

type AgentName = 'Lifecycle' | 'Billing' | 'Payment' | 'Revenue'

const AGENTS: { name: AgentName; scope: string }[] = [
  { name: 'Lifecycle', scope: 'Renewals · expiry · pause' },
  { name: 'Billing', scope: 'Invoices · tax · discounts' },
  { name: 'Payment', scope: 'Collections · reconciliation' },
  { name: 'Revenue', scope: 'Churn · forecast · MRR' },
]

interface Step { agent: AgentName; tool: string; args: string; result: () => Promise<string> | string }
interface Plan {
  route: string
  steps: Step[]
  answer: string
  evidence: string
  approval?: string
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

const churnCall = async () => {
  try {
    const r = await api<{ churn_percentage: number; risk_level: string }>('/churn/predict', {
      body: {
        tenure_months: 4, monthly_charges: 890, payment_failures_90d: 3, days_since_last_payment: 62, support_tickets_90d: 5,
        usage_sessions_30d: 2, plan_type: 'Premium', discount_used: 0, renewal_count: 0, auto_renew: 0, late_payment_count: 4,
      },
    })
    return `Northwind Labs → ${r.churn_percentage.toFixed(1)}% (${r.risk_level} risk)`
  } catch {
    return 'Northwind Labs → model unavailable, used rule-based score 86 (High)'
  }
}

const PLANS: { match: RegExp; plan: Plan }[] = [
  {
    match: /expir|renew|pause|lifecycle/i,
    plan: {
      route: 'Lifecycle Agent',
      steps: [
        { agent: 'Lifecycle', tool: 'subscriptions.list_expiring', args: 'days=30', result: () => '4 subscriptions expire in the next 30 days' },
        { agent: 'Lifecycle', tool: 'subscriptions.check_renewal_rules', args: 'ids=[SUB-1043, SUB-1045, …]', result: () => '3 eligible for auto-renewal, 1 needs manual renewal' },
      ],
      answer: '4 subscriptions expire this month. 3 will auto-renew; SUB-1048 (Orbit Studio) has already expired and needs a manual renewal.',
      evidence: 'subscriptions: SUB-1043, SUB-1045, SUB-1046, SUB-1048 · plan renewal rules',
      approval: 'Send renewal reminder to Orbit Studio',
    },
  },
  {
    match: /invoice|bill|tax|discount/i,
    plan: {
      route: 'Billing Agent',
      steps: [
        { agent: 'Billing', tool: 'billing.list_due_cycles', args: 'date=today', result: () => '2 subscriptions due for billing' },
        { agent: 'Billing', tool: 'billing.check_duplicates', args: 'cycle_keys=[…]', result: () => 'No duplicate invoices found' },
      ],
      answer: 'Two subscriptions are due for billing today (SUB-1042, SUB-1046). Totals come from the billing service. No duplicates exist, so it is safe to generate both invoices.',
      evidence: 'billing cycles · invoices INV-0190, INV-0192',
      approval: 'Generate 2 invoices for due renewals',
    },
  },
  {
    match: /payment|bank|unmatch|reconcil|northwind/i,
    plan: {
      route: 'Payment Agent',
      steps: [
        { agent: 'Payment', tool: 'bank.find_unmatched', args: 'status=unmatched,partial', result: () => '2 unmatched bank credits, 1 partial match' },
        { agent: 'Payment', tool: 'reconciliation.suggest_match', args: 'txn=BTX-903', result: () => 'BTX-903 → INV-0189 (64% confidence, partial)' },
      ],
      answer: 'BTX-903 ($900, IMPS NORTHWIND LABS) is a partial payment against INV-0189 ($1,780). $880 remains outstanding, and PAY-5519 (AutoPay) failed on 28 Oct.',
      evidence: 'bank txn BTX-903 · invoice INV-0189 · payment PAY-5519',
      approval: 'Send payment reminder to Northwind Labs',
    },
  },
  {
    match: /churn|risk|revenue|dip|forecast|mrr|why/i,
    plan: {
      route: 'Revenue Agent → Billing, Payment',
      steps: [
        { agent: 'Revenue', tool: 'revenue.compare_periods', args: 'metric=collected, months=3', result: () => 'Outstanding rose to $7,800 (+44% vs Sep)' },
        { agent: 'Payment', tool: 'payments.failed_summary', args: 'days=30', result: () => '1 failed AutoPay, 2 overdue invoices ($2,670)' },
        { agent: 'Revenue', tool: 'churn.predict', args: 'customer=CUS-1004', result: churnCall },
      ],
      answer: 'Collected revenue is up, but outstanding balances rose 44%. Two overdue invoices and a failed AutoPay (Northwind Labs, Delta Freight) drive most of it, and Northwind is the highest churn risk.',
      evidence: 'revenue by month · overdue invoices INV-0189, INV-0191 · churn model output',
      approval: 'Create retention follow-up task for Northwind Labs',
    },
  },
]

const FALLBACK: Plan = {
  route: 'Orchestrator',
  steps: [{ agent: 'Revenue', tool: 'orchestrator.classify_intent', args: 'text=…', result: () => 'Intent unclear' }],
  answer: 'I could not map that to Lifecycle, Billing, Payment or Revenue. Try asking about expiring subscriptions, invoices, unmatched payments or churn risk.',
  evidence: 'No tools were run',
}

type Status = 'idle' | 'running' | 'done'
interface Turn {
  q: string
  plan: Plan
  done: { tool: string; args: string; agent: AgentName; out: string }[]
  finished: boolean
  decision?: 'approved' | 'rejected'
}

const PROMPTS = ['Which subscriptions expire this month?', 'Why are payments from Northwind unmatched?', 'Why did revenue dip and who might churn?']

export default function Assistant() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [text, setText] = useState('')
  const [active, setActive] = useState<AgentName[]>([])
  const [log, setLog] = useState<string[]>([])
  const bottom = useRef<HTMLDivElement>(null)
  const busy = turns.some((t) => !t.finished)

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) }, [turns])

  const status = (a: AgentName): Status => (active.includes(a) ? 'running' : turns.some((t) => t.done.some((d) => d.agent === a)) ? 'done' : 'idle')

  const patch = (i: number, p: (t: Turn) => Turn) => setTurns((ts) => ts.map((t, k) => (k === i ? p(t) : t)))

  const ask = async (q: string) => {
    if (!q.trim() || busy) return
    setText('')
    const plan = PLANS.find((p) => p.match.test(q))?.plan ?? FALLBACK
    const i = turns.length
    setTurns((ts) => [...ts, { q, plan, done: [], finished: false }])
    setLog((l) => [`Orchestrator routed "${q.slice(0, 40)}" to ${plan.route}`, ...l])

    for (const s of plan.steps) {
      setActive([s.agent])
      await sleep(700)
      const out = await s.result()
      patch(i, (t) => ({ ...t, done: [...t.done, { tool: s.tool, args: s.args, agent: s.agent, out }] }))
      setLog((l) => [`${s.agent} Agent called ${s.tool}`, ...l])
    }
    setActive([])
    patch(i, (t) => ({ ...t, finished: true }))
  }

  const decide = (i: number, d: 'approved' | 'rejected') => {
    patch(i, (t) => ({ ...t, decision: d }))
    setLog((l) => [`Human ${d}: ${turns[i].plan.approval}`, ...l])
  }

  const pending = turns.filter((t) => t.finished && t.plan.approval && !t.decision)

  return (
    <div className="stack">
      <div className="page-head">
        <div><h2>AI Assistant</h2><p>The orchestrator plans the task, routes it to specialist agents and asks you before sensitive actions</p></div>
      </div>

      <div className="agent-layout">
        <Card>
          <div className="chat">
            {turns.length === 0 && (
              <div className="suggest">{PROMPTS.map((p) => <button key={p} className="btn" onClick={() => ask(p)}>{p}</button>)}</div>
            )}
            {turns.map((t, i) => (
              <div className="chat" key={i}>
                <div className="bubble me">{t.q}</div>
                <div className="bubble ai">
                  <span><Pill>AI</Pill> Plan: <b>{t.plan.route}</b></span>
                  <ol className="trace">
                    {t.done.map((d, k) => (
                      <li key={k}>
                        <Check size={13} className="ok" />
                        <div><code><Wrench size={11} /> {d.tool}({d.args})</code><span>{d.out}</span></div>
                      </li>
                    ))}
                    {!t.finished && <li><CircleDashed size={13} className="spin" /><div><span className="muted">Working…</span></div></li>}
                  </ol>
                  {t.finished && (
                    <>
                      <span>{t.plan.answer}</span>
                      <span className="evidence">Evidence: {t.plan.evidence}</span>
                      {t.plan.approval && (
                        <div className="approval">
                          <span>Approval required: {t.plan.approval}</span>
                          {t.decision ? <Pill>{t.decision === 'approved' ? 'Approved' : 'Cancelled'}</Pill> : (
                            <span style={{ display: 'flex', gap: 6 }}>
                              <button className="btn sm good" onClick={() => decide(i, 'approved')}><Check size={12} /> Approve</button>
                              <button className="btn sm bad" onClick={() => decide(i, 'rejected')}><X size={12} /></button>
                            </span>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}
            <div ref={bottom} />
            <form className="composer" onSubmit={(e) => { e.preventDefault(); ask(text) }}>
              <input value={text} onChange={(e) => setText(e.target.value)} disabled={busy}
                placeholder="Ask about renewals, invoices, payments, churn or revenue…" />
              <button className="btn dark" type="submit" disabled={busy}><Send size={13} /> Ask</button>
            </form>
          </div>
        </Card>

        <div className="stack">
          <Card title="Agents" action={<Bot size={16} className="muted" />}>
            <div className="rows">
              {AGENTS.map((a) => (
                <div className="row" key={a.name}>
                  <div><span>{a.name} Agent</span><small>{a.scope}</small></div>
                  <span className={`state ${status(a.name)}`}>{status(a.name) === 'running' ? 'Working' : status(a.name) === 'done' ? 'Done' : 'Idle'}</span>
                </div>
              ))}
            </div>
          </Card>
          <Card title={`Pending approvals${pending.length ? ` (${pending.length})` : ''}`}>
            {pending.length === 0 ? <p className="muted">Nothing waiting for you.</p> : (
              <div className="rows">{pending.map((t) => <div className="row" key={t.q}><span>{t.plan.approval}</span></div>)}</div>
            )}
          </Card>
          <Card title="Activity log">
            {log.length === 0 ? <p className="muted">Agent activity appears here.</p> : (
              <div className="log">{log.slice(0, 8).map((l, i) => <small key={i}>{l}</small>)}</div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
