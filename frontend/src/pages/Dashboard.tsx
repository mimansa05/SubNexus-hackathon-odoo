import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth'
import { Bars, Card, Meter, Pill, SparkBars, Stat, Tabs } from '../ui'
import { churn, compact, invoices, money, mySubscriptions, myInvoices, revenueByMonth, subscriptionStatus } from '../data'

/* Every role gets the same four-slot layout: headline chart, breakdown, recent list, needs-attention. */

const Recent = ({ rows, to }: { rows: typeof invoices; to: string }) => (
  <Card title="Recent invoices" className="span2" action={<Link className="link" to={to}>View all</Link>}>
    <div className="table-wrap">
      <table>
        <thead><tr><th>Invoice</th><th>Customer</th><th>Due</th><th>Amount</th><th>Status</th></tr></thead>
        <tbody>
          {rows.slice(0, 4).map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td><td>{r.customer}</td><td className="muted">{r.due}</td>
              <td>{money(r.amount)}</td><td><Pill>{r.status}</Pill></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </Card>
)

const Attention = ({ title, to, items }: {
  title: string; to: string; items: { main: string; sub: string; right: ReactNode }[]
}) => (
  <Card title={title} action={<Link className="link" to={to}>View all</Link>}>
    <div className="rows">
      {items.map((it) => (
        <div className="row" key={it.main}>
          <div><span>{it.main}</span><small>{it.sub}</small></div>
          {it.right}
        </div>
      ))}
    </div>
  </Card>
)

function Admin() {
  const [view, setView] = useState<'Collected' | 'Outstanding'>('Collected')
  const total = subscriptionStatus.reduce((s, x) => s + x.value, 0)
  const last = revenueByMonth[revenueByMonth.length - 1]
  const data = revenueByMonth.map((m) => ({
    label: m.label,
    value: view === 'Collected' ? m.collected : m.outstanding,
    sub: view === 'Collected' ? `+${money(m.outstanding)} due` : undefined,
  }))

  return (
    <div className="grid">
      <Card
        title="Revenue" className="span2"
        action={<Tabs options={['Collected', 'Outstanding'] as const} value={view} onChange={setView} />}
      >
        <div className="split">
          <div>
            <span className="eyebrow">MRR this month</span>
            <div className="big">{money(last.collected)}</div>
          </div>
          <div className="stats">
            <Stat label="ARR" value={compact(last.collected * 12)} />
            <Stat label="Churn" value="2.4%" note="monthly" />
          </div>
        </div>
        <Bars data={data} format={money} />
      </Card>

      <Card title="Subscriptions">
        {subscriptionStatus.map((s) => (
          <Meter key={s.label} label={s.label} value={String(s.value)} pct={(s.value / total) * 100} tone={s.tone} />
        ))}
      </Card>

      <Recent rows={invoices} to="/billing" />

      <Attention
        title="Needs attention" to="/insights"
        items={churn.slice(0, 3).map((c) => ({
          main: c.customer, sub: `${c.factors[0]} · ${money(c.atRisk)} at risk`, right: <Pill>{c.level}</Pill>,
        }))}
      />
    </div>
  )
}

function Staff() {
  return (
    <div className="grid">
      <Card title="My workload" className="span2">
        <div className="split">
          <div>
            <span className="eyebrow">Follow-ups due this week</span>
            <div className="big">12</div>
          </div>
          <div className="stats">
            <Stat label="Renewals" value="7" note="next 14 days" />
            <Stat label="Exceptions" value="3" note="reconciliation" />
          </div>
        </div>
        <div className="split" style={{ marginTop: 22, paddingTop: 18, borderTop: '1px solid var(--line)' }}>
          <Stat label="Overdue invoices" value="5" note={money(3670)} />
          <SparkBars values={[3, 5, 4, 7, 5, 6, 4, 8, 5, 5, 6, 4]} />
        </div>
      </Card>

      <Card title="Subscriptions">
        {subscriptionStatus.map((s) => (
          <Meter key={s.label} label={s.label} value={String(s.value)} pct={(s.value / 842) * 100} tone={s.tone} />
        ))}
      </Card>

      <Recent rows={invoices} to="/billing" />

      <Attention
        title="Follow-ups" to="/customers"
        items={churn.slice(0, 3).map((c) => ({ main: c.customer, sub: c.action, right: <Pill>{c.level}</Pill> }))}
      />
    </div>
  )
}

function Customer() {
  const due = myInvoices.filter((i) => i.status !== 'Paid' && i.status !== 'Draft')
  const owed = due.reduce((s, i) => s + i.amount, 0)
  return (
    <div className="grid">
      <Card title="Outstanding" className="span2">
        <div className="split">
          <div>
            <span className="eyebrow">Amount due</span>
            <div className="big">{money(owed)}</div>
          </div>
          <div className="stats">
            <Stat label="Next billing" value="02 Nov" />
            <Stat label="Renews" value="12 Nov" />
          </div>
        </div>
        <div style={{ marginTop: 22 }}>
          <button className="btn dark">Pay outstanding invoices</button>
        </div>
      </Card>

      <Card title="My subscription">
        {mySubscriptions.map((s) => (
          <div className="rows" key={s.id}>
            <div className="row"><span>Plan</span><b>{s.plan}</b></div>
            <div className="row"><span>Status</span><Pill>{s.status}</Pill></div>
            <div className="row"><span>Amount</span><b>{money(s.amount)}</b></div>
            <div className="row">
              <button className="btn sm">Pause</button><button className="btn sm">Request renewal</button>
            </div>
          </div>
        ))}
      </Card>

      <Recent rows={myInvoices} to="/invoices" />

      <Attention
        title="Notifications" to="/"
        items={[
          { main: 'Invoice INV-0188 generated', sub: '2h ago', right: <Pill>Unpaid</Pill> },
          { main: 'Payment PAY-5521 received', sub: '2 days ago', right: <Pill>Paid</Pill> },
        ]}
      />
    </div>
  )
}

export default function Dashboard() {
  const { role } = useAuth()
  return role === 'admin' ? <Admin /> : role === 'staff' ? <Staff /> : <Customer />
}
