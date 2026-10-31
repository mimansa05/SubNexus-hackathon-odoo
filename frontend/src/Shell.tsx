import { useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Bell, Search, LogOut, ArrowRight, Sparkles } from 'lucide-react'
import { useAuth, type Role } from './auth'
import { NAV } from './nav'
import { notifications } from './data'

const greeting = () => {
  const h = new Date().getHours()
  return h < 12 ? 'Good Morning,' : h < 18 ? 'Good Afternoon,' : 'Good Evening,'
}

const NUDGE: Record<Role, { title: string; text: string; cta: string; to: string }> = {
  admin: { title: '3 approvals waiting', text: 'AI recommendations need a human decision before they run.', cta: 'Review now', to: '/assistant' },
  staff: { title: '4 follow-ups due today', text: 'Overdue invoices and renewals assigned to you.', cta: 'Open tasks', to: '/billing' },
  customer: { title: 'Invoice INV-0188 due', text: 'Pay $540 by 29 Oct to keep your plan active.', cta: 'Pay now', to: '/invoices' },
}

export default function Shell() {
  const { role, user, signOut } = useAuth()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const [bell, setBell] = useState(false)
  const [menu, setMenu] = useState(false)
  const home = pathname === '/'
  const nudge = NUDGE[role!]

  return (
    <div className="app">
      <header className={`hero ${home ? '' : 'compact'}`}>
        <svg className="swoosh" viewBox="0 0 600 240" preserveAspectRatio="none" aria-hidden>
          {Array.from({ length: 14 }).map((_, i) => (
            <path key={i} d={`M${260 + i * 9} -10 C ${330 + i * 14} 80, ${300 + i * 20} 160, ${420 + i * 12} 260`} />
          ))}
        </svg>

        <div className="hero-top">
          <div className="hero-date">
            {new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          </div>
          <div className="hero-tools">
            <label className="search">
              <Search size={14} />
              <input placeholder="Search customers, invoices, refs…" />
            </label>
            <div className="pop-wrap">
              <button className="round" aria-label="Notifications" onClick={() => { setBell(!bell); setMenu(false) }}>
                <Bell size={16} /><span className="dot" />
              </button>
              {bell && (
                <div className="popover">
                  <h4>Notifications</h4>
                  {notifications.map((n) => (
                    <div key={n.id} className="note"><span>{n.text}</span><small>{n.time}</small></div>
                  ))}
                </div>
              )}
            </div>
            <div className="pop-wrap">
              <button className="avatar" aria-label="Account" onClick={() => { setMenu(!menu); setBell(false) }}>
                {user!.first[0]}
              </button>
              {menu && (
                <div className="popover small">
                  <div className="note"><span>{user!.name}</span><small className="cap">{role}</small></div>
                  <button className="menu-item" onClick={() => { signOut(); navigate('/login') }}>
                    <LogOut size={14} /> Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {home && (
          <div className="hero-main">
            <h1>
              {greeting()}
              <br />
              <em>{user!.name}.</em>
            </h1>
            <aside className="nudge">
              <div className="nudge-head"><span><Sparkles size={13} /> For you</span></div>
              <div className="nudge-body">
                <b>{nudge.title}</b>
                <p>{nudge.text}</p>
                <button className="btn-white" onClick={() => navigate(nudge.to)}>{nudge.cta} <ArrowRight size={14} /></button>
              </div>
            </aside>
          </div>
        )}

        <nav className="nav">
          {NAV[role!].map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'on' : '')}>
              <span className="nav-ic"><Icon size={15} /></span>
              {label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="page">
        <Outlet />
      </main>
    </div>
  )
}
