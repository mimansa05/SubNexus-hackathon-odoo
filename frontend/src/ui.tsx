import { useState, type ReactNode } from 'react'
import { ArrowUpRight } from 'lucide-react'

export function Card({ title, action, children, className = '' }: {
  title?: string; action?: ReactNode; children: ReactNode; className?: string
}) {
  return (
    <section className={`card ${className}`}>
      {title && (
        <header className="card-head">
          <h3>{title}</h3>
          {action ?? <span className="icon-btn"><ArrowUpRight size={14} /></span>}
        </header>
      )}
      {children}
    </section>
  )
}

const TONES: Record<string, string> = {
  paid: 'good', active: 'good', successful: 'good', matched: 'good', approved: 'good', low: 'good',
  unpaid: 'warn', pending: 'warn', confirmed: 'warn', medium: 'warn', 'review required': 'warn',
  'partially matched': 'warn', processing: 'warn',
  overdue: 'bad', failed: 'bad', cancelled: 'bad', high: 'bad', unmatched: 'bad', inactive: 'bad',
  paused: 'mute', draft: 'mute', expired: 'mute', duplicate: 'mute', refunded: 'mute', ai: 'violet',
}

export const Pill = ({ children }: { children: string }) => (
  <span className={`pill ${TONES[children.toLowerCase()] ?? 'mute'}`}>{children}</span>
)

export function Tabs<T extends string>({ options, value, onChange }: {
  options: readonly T[]; value: T; onChange: (v: T) => void
}) {
  return (
    <div className="tabs">
      {options.map((o) => (
        <button key={o} className={o === value ? 'on' : ''} onClick={() => onChange(o)}>{o}</button>
      ))}
    </div>
  )
}

/** Striped purple bars with an inline callout on the selected bar. */
export function Bars({ data, format }: {
  data: { label: string; value: number; sub?: string }[]; format: (n: number) => string
}) {
  const [sel, setSel] = useState(data.length - 1)
  const max = Math.max(...data.map((d) => d.value))
  return (
    <div className="bars">
      {data.map((d, i) => (
        <button key={d.label} className={`bar-col ${i === sel ? 'on' : ''}`} onClick={() => setSel(i)}>
          <div className="bar" style={{ height: `${30 + (d.value / max) * 70}%` }}>
            {i === sel && (
              <div className="bar-tip">
                <small>{d.label}</small>
                <b>{format(d.value)}</b>
                {d.sub && <small>{d.sub}</small>}
              </div>
            )}
          </div>
          <span>{d.label}</span>
        </button>
      ))}
    </div>
  )
}

export function SparkBars({ values, tone = 'orange', peak }: {
  values: number[]; tone?: 'orange' | 'violet'; peak?: number
}) {
  const max = Math.max(...values)
  const hi = peak ?? values.indexOf(max)
  return (
    <div className={`spark ${tone}`}>
      {values.map((v, i) => (
        <i key={i} className={i === hi ? 'hi' : ''} style={{ height: `${Math.max(14, (v / max) * 100)}%` }} />
      ))}
    </div>
  )
}

export function Meter({ label, value, pct, tone }: { label: string; value: string; pct: number; tone: string }) {
  return (
    <div className="meter">
      <div className="meter-row"><span>{label}</span><b>{value}</b></div>
      <div className={`track ${tone}`}><i style={{ width: `${pct}%` }} /></div>
    </div>
  )
}

export const Stat = ({ label, value, note }: { label: string; value: string; note?: string }) => (
  <div className="stat">
    <span>{label}</span>
    <b>{value}</b>
    {note && <small>{note}</small>}
  </div>
)
