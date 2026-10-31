import { useMemo, useState, type ReactNode } from 'react'
import { Download, Plus, Search } from 'lucide-react'

export interface Column<T> {
  key: keyof T & string
  label: string
  align?: 'right'
  render?: (row: T) => ReactNode
}

interface Props<T> {
  title?: string
  subtitle?: string
  cta?: string
  columns: Column<T>[]
  rows: T[]
  /** Row field used by the status filter chips. */
  statusKey?: keyof T & string
  top?: ReactNode
}

const toCsv = <T extends object>(cols: Column<T>[], rows: T[]) =>
  [cols.map((c) => c.label), ...rows.map((r) => cols.map((c) => String((r as Record<string, unknown>)[c.key]).replace(/,/g, ' ')))]
    .map((l) => l.join(',')).join('\n')

export default function ListPage<T extends object>({ title, subtitle, cta, columns, rows, statusKey, top }: Props<T>) {
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('All')

  const statuses = useMemo(
    () => (statusKey ? ['All', ...Array.from(new Set(rows.map((r) => String(r[statusKey]))))] : []),
    [rows, statusKey],
  )

  const shown = rows.filter((r) => {
    if (statusKey && status !== 'All' && String(r[statusKey]) !== status) return false
    return !q || JSON.stringify(Object.values(r)).toLowerCase().includes(q.toLowerCase())
  })

  const exportCsv = () => {
    const url = URL.createObjectURL(new Blob([toCsv(columns, shown)], { type: 'text/csv' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `${(title ?? 'export').toLowerCase().replace(/\s+/g, '-')}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="stack">
      {title && (
        <div className="page-head">
          <div>
            <h2>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
          {cta && <button className="btn dark"><Plus size={14} /> {cta}</button>}
        </div>
      )}
      {top}
      <section className="card">
        <div className="toolbar">
          <label className="field">
            <Search size={14} />
            <input placeholder="Search…" value={q} onChange={(e) => setQ(e.target.value)} />
          </label>
          {statuses.length > 0 && (
            <div className="tabs">
              {statuses.map((s) => (
                <button key={s} className={s === status ? 'on' : ''} onClick={() => setStatus(s)}>{s}</button>
              ))}
            </div>
          )}
          <span className="spacer" />
          <button className="btn" onClick={exportCsv}><Download size={13} /> Export CSV</button>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>{columns.map((c) => <th key={c.key} className={c.align === 'right' ? 'num' : ''}>{c.label}</th>)}</tr>
            </thead>
            <tbody>
              {shown.map((r, i) => (
                <tr key={i}>
                  {columns.map((c) => (
                    <td key={c.key} className={c.align === 'right' ? 'num' : ''}>
                      {c.render ? c.render(r) : String((r as Record<string, unknown>)[c.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {shown.length === 0 && <div className="empty">No results match your filters.</div>}
        </div>
        <div className="foot">Showing {shown.length} of {rows.length}</div>
      </section>
    </div>
  )
}
