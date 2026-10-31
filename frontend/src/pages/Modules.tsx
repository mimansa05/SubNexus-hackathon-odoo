import { useState } from 'react'
import { Check, Send, Upload, X } from 'lucide-react'
import ListPage from '../ListPage'
import { Card, Pill, Tabs } from '../ui'
import { useAuth } from '../auth'
import {
  audit, churn, customers, discounts, invoices, money, myInvoices, myPayments, mySubscriptions, payments, plans,
  products, reconciliation, subscriptions, taxes,
} from '../data'

export const Customers = () => (
  <ListPage
    title="Customers" subtitle="Profiles, balances and subscription status" cta="New customer"
    statusKey="status" rows={customers}
    columns={[
      { key: 'id', label: 'ID' },
      { key: 'name', label: 'Customer' },
      { key: 'email', label: 'Email', render: (r) => <span className="muted">{r.email}</span> },
      { key: 'plan', label: 'Plan' },
      { key: 'mrr', label: 'MRR', align: 'right', render: (r) => money(r.mrr) },
      { key: 'outstanding', label: 'Outstanding', align: 'right', render: (r) => money(r.outstanding) },
      { key: 'status', label: 'Status', render: (r) => <Pill>{r.status}</Pill> },
    ]}
  />
)

export const Subscriptions = () => {
  const { role } = useAuth()
  const mine = role === 'customer'
  return (
    <ListPage
      title={mine ? 'My subscriptions' : 'Subscriptions'}
      subtitle={mine ? 'Plan, billing dates and requests' : 'Draft → Quotation → Confirmed → Active → Closed'}
      cta={mine ? undefined : 'New subscription'}
      statusKey="status" rows={mine ? mySubscriptions : subscriptions}
      columns={[
        { key: 'id', label: 'Number' },
        { key: 'customer', label: 'Customer' },
        { key: 'plan', label: 'Plan' },
        { key: 'next', label: 'Next billing', render: (r) => <span className="muted">{r.next}</span> },
        { key: 'amount', label: 'Amount', align: 'right', render: (r) => money(r.amount) },
        { key: 'status', label: 'Status', render: (r) => <Pill>{r.status}</Pill> },
      ]}
    />
  )
}

type Inv = (typeof invoices)[number]
const invoiceColumns = [
  { key: 'id', label: 'Invoice' },
  { key: 'customer', label: 'Customer' },
  { key: 'due', label: 'Due', render: (r: Inv) => <span className="muted">{r.due}</span> },
  { key: 'amount', label: 'Amount', align: 'right' as const, render: (r: Inv) => money(r.amount) },
  { key: 'status', label: 'Status', render: (r: Inv) => <Pill>{r.status}</Pill> },
] as const

export const Invoices = ({ embedded }: { embedded?: boolean }) => {
  const { role } = useAuth()
  return (
    <ListPage
      title={embedded ? undefined : 'Invoices'} subtitle="Draft, confirmed, paid and overdue"
      statusKey="status" rows={role === 'customer' ? myInvoices : invoices} columns={[...invoiceColumns]}
    />
  )
}

export const Payments = ({ embedded }: { embedded?: boolean }) => {
  const { role } = useAuth()
  return (
    <ListPage
      title={embedded ? undefined : 'Payments'} subtitle="Gateway and manual payments, refunds and reversals"
      statusKey="status" rows={role === 'customer' ? myPayments : payments}
      columns={[
        { key: 'id', label: 'Reference' },
        { key: 'invoice', label: 'Invoice' },
        { key: 'customer', label: 'Customer' },
        { key: 'method', label: 'Method' },
        { key: 'date', label: 'Date', render: (r) => <span className="muted">{r.date}</span> },
        { key: 'amount', label: 'Amount', align: 'right', render: (r) => money(r.amount) },
        { key: 'status', label: 'Status', render: (r) => <Pill>{r.status}</Pill> },
      ]}
    />
  )
}

export const Billing = () => {
  const [tab, setTab] = useState<'Invoices' | 'Payments'>('Invoices')
  return (
    <div className="stack">
      <div className="page-head">
        <div><h2>Billing</h2><p>Recurring invoices and collected payments</p></div>
        <Tabs options={['Invoices', 'Payments'] as const} value={tab} onChange={setTab} />
      </div>
      {tab === 'Invoices' ? <Invoices embedded /> : <Payments embedded />}
    </div>
  )
}

export const Reconciliation = () => {
  const [decided, setDecided] = useState<Record<string, 'Approved' | 'Rejected'>>({})
  const rows = reconciliation.map((r) => ({ ...r, status: decided[r.id] === 'Approved' ? 'Approved' : r.status }))
  const decide = (id: string, v: 'Approved' | 'Rejected') => setDecided({ ...decided, [id]: v })

  return (
    <ListPage
      title="Reconciliation" subtitle="Import a bank statement, review suggested matches, approve or reject"
      statusKey="status" rows={rows}
      top={
        <Card>
          <div className="drop">
            <Upload size={20} />
            <span><b>Drop a CSV or Excel statement</b> or browse</span>
            <small>Duplicates and parsing errors are flagged before saving</small>
          </div>
        </Card>
      }
      columns={[
        { key: 'id', label: 'Bank txn' },
        { key: 'desc', label: 'Description' },
        { key: 'amount', label: 'Amount', align: 'right', render: (r) => money(r.amount) },
        { key: 'match', label: 'Suggested match' },
        {
          key: 'confidence', label: 'Confidence',
          render: (r) => (
            <div className="conf">
              <div className={`track ${r.confidence > 85 ? 'teal' : r.confidence > 60 ? 'orange' : 'purple'}`}><i style={{ width: `${r.confidence}%` }} /></div>
              <small>{r.confidence}%</small>
            </div>
          ),
        },
        { key: 'status', label: 'Status', render: (r) => <Pill>{decided[r.id] === 'Rejected' ? 'Unmatched' : r.status}</Pill> },
        {
          key: 'id', label: '',
          render: (r) => r.match === '—' || decided[r.id] ? null : (
            <span style={{ display: 'inline-flex', gap: 6 }}>
              <button className="btn sm good" onClick={() => decide(r.id, 'Approved')}><Check size={12} /> Approve</button>
              <button className="btn sm bad" onClick={() => decide(r.id, 'Rejected')}><X size={12} /></button>
            </span>
          ),
        },
      ]}
    />
  )
}

export const Insights = () => (
  <ListPage
    title="Churn insights" subtitle="Transparent, rule-based risk scoring with recommended retention actions"
    statusKey="level" rows={churn}
    columns={[
      { key: 'customer', label: 'Customer' },
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
      { key: 'factors', label: 'Why', render: (r) => <div className="chips">{r.factors.map((f) => <span className="chip" key={f}>{f}</span>)}</div> },
      { key: 'atRisk', label: 'Revenue at risk', align: 'right', render: (r) => money(r.atRisk) },
      { key: 'action', label: 'Recommended' },
    ]}
  />
)

export const Audit = () => (
  <ListPage
    title="Audit trail" subtitle="Append-only record of user, system and AI actions"
    rows={audit}
    columns={[
      { key: 'time', label: 'Time', render: (r) => <span className="muted">{r.time}</span> },
      { key: 'actor', label: 'Actor' },
      { key: 'action', label: 'Action' },
      { key: 'entity', label: 'Entity' },
      { key: 'source', label: 'Source', render: (r) => <Pill>{r.source}</Pill> },
    ]}
  />
)

const CATALOG = ['Products', 'Plans', 'Taxes', 'Discounts'] as const
export const Catalog = () => {
  const [tab, setTab] = useState<(typeof CATALOG)[number]>('Plans')
  const st = (r: { status: string }) => <Pill>{r.status}</Pill>
  return (
    <div className="stack">
      <div className="page-head">
        <div><h2>Catalog</h2><p>Products, plans, tax rules and discount rules</p></div>
        <Tabs options={CATALOG} value={tab} onChange={setTab} />
      </div>
      {tab === 'Products' && <ListPage statusKey="status" rows={products} columns={[
        { key: 'id', label: 'ID' }, { key: 'name', label: 'Product' }, { key: 'type', label: 'Type' },
        { key: 'price', label: 'Sales price', align: 'right', render: (r) => money(r.price) },
        { key: 'cost', label: 'Cost', align: 'right', render: (r) => money(r.cost) },
        { key: 'status', label: 'Status', render: st },
      ]} />}
      {tab === 'Plans' && <ListPage statusKey="status" rows={plans} columns={[
        { key: 'id', label: 'ID' }, { key: 'name', label: 'Plan' }, { key: 'billing', label: 'Billing' },
        { key: 'price', label: 'Price', align: 'right', render: (r) => money(r.price) },
        { key: 'minQty', label: 'Min qty', align: 'right' },
        { key: 'status', label: 'Status', render: st },
      ]} />}
      {tab === 'Taxes' && <ListPage statusKey="status" rows={taxes} columns={[
        { key: 'id', label: 'ID' }, { key: 'name', label: 'Tax rule' }, { key: 'rate', label: 'Rate' },
        { key: 'from', label: 'Effective from' }, { key: 'status', label: 'Status', render: st },
      ]} />}
      {tab === 'Discounts' && <ListPage statusKey="status" rows={discounts} columns={[
        { key: 'id', label: 'ID' }, { key: 'name', label: 'Discount' }, { key: 'value', label: 'Value' },
        { key: 'minQty', label: 'Min qty', align: 'right' }, { key: 'used', label: 'Usage' },
        { key: 'status', label: 'Status', render: st },
      ]} />}
    </div>
  )
}

const PROMPTS = ['Which subscriptions expire this month?', 'Why are payments from Northwind unmatched?', 'Why did revenue dip in August?']
const REPLY = {
  agent: 'Payment Agent',
  text: 'BTX-903 (IMPS NORTHWIND LABS, $900) is a partial payment against INV-0189 ($1,780). $880 remains outstanding.',
  evidence: 'Evidence: bank txn BTX-903 · invoice INV-0189 · payment PAY-5519 (failed AutoPay, 28 Oct)',
  approval: 'Send payment reminder to Northwind Labs',
}

export const Assistant = () => {
  const [thread, setThread] = useState<{ q: string }[]>([])
  const [text, setText] = useState('')
  const ask = (q: string) => { if (q.trim()) { setThread([...thread, { q }]); setText('') } }

  return (
    <div className="stack">
      <div className="page-head">
        <div><h2>Assistant</h2><p>Routes to Lifecycle, Billing, Payment or Revenue agents. Sensitive actions need your approval.</p></div>
      </div>
      <Card>
        <div className="chat">
          {thread.length === 0 && (
            <div className="suggest">{PROMPTS.map((p) => <button key={p} className="btn" onClick={() => ask(p)}>{p}</button>)}</div>
          )}
          {thread.map((t, i) => (
            <div className="chat" key={i}>
              <div className="bubble me">{t.q}</div>
              <div className="bubble ai">
                <span><Pill>AI</Pill> routed to <b>{REPLY.agent}</b></span>
                <span>{REPLY.text}</span>
                <span className="evidence">{REPLY.evidence}</span>
                <div className="approval">
                  <span>Approval required: {REPLY.approval}</span>
                  <span style={{ display: 'flex', gap: 6 }}>
                    <button className="btn sm good">Approve</button><button className="btn sm bad">Reject</button>
                  </span>
                </div>
              </div>
            </div>
          ))}
          <form className="composer" onSubmit={(e) => { e.preventDefault(); ask(text) }}>
            <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask about customers, invoices, churn or revenue…" />
            <button className="btn dark" type="submit"><Send size={13} /> Ask</button>
          </form>
        </div>
      </Card>
    </div>
  )
}
