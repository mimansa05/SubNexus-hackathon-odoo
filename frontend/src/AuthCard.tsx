import type { ReactNode } from 'react'
import { SparkBars } from './ui'

const POINTS = ['Recurring billing & invoices', 'Bank reconciliation', 'AI churn insights']

export const AuthCard = ({ title, children }: { title: ReactNode; children: ReactNode }) => (
  <div className="auth">
    <aside className="auth-art">
      <svg className="swoosh" viewBox="0 0 600 700" preserveAspectRatio="none" aria-hidden>
        {Array.from({ length: 16 }).map((_, i) => (
          <path key={i} d={`M${200 + i * 12} -10 C ${300 + i * 16} 200, ${180 + i * 22} 420, ${380 + i * 14} 720`} />
        ))}
      </svg>
      <div className="brand">Sub<em>Nexus</em></div>
      <div className="art-body">
        <h2>Subscription revenue,<br /><em>under control.</em></h2>
        <p>Billing, payments and AI-powered insights in one calm workspace.</p>
        <div className="chips-dark">{POINTS.map((p) => <span key={p}>{p}</span>)}</div>
      </div>
      <div className="art-card" aria-hidden>
        <small>MRR this month</small>
        <b>$42,600</b>
        <span className="up">▲ 8.4% vs last month</span>
        <SparkBars values={[4, 6, 5, 7, 6, 8, 7, 9, 10]} tone="violet" />
      </div>
    </aside>
    <main className="auth-main">
      <div className="login-card">
        <h1>{title}</h1>
        {children}
      </div>
    </main>
  </div>
)

export default AuthCard
