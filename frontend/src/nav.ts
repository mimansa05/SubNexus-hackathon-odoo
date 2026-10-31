import {
  LayoutGrid, Users, Repeat, Receipt, FileText, CreditCard, Landmark, LineChart, Sparkles, ScrollText, Package,
  type LucideIcon,
} from 'lucide-react'
import type { Role } from './auth'

export interface NavItem { to: string; label: string; icon: LucideIcon }

const overview = { to: '/', label: 'Overview', icon: LayoutGrid }
const customers = { to: '/customers', label: 'Customers', icon: Users }
const subscriptions = { to: '/subscriptions', label: 'Subscriptions', icon: Repeat }
const billing = { to: '/billing', label: 'Billing', icon: Receipt }
const recon = { to: '/reconciliation', label: 'Reconciliation', icon: Landmark }
const assistant = { to: '/assistant', label: 'Assistant', icon: Sparkles }

export const NAV: Record<Role, NavItem[]> = {
  admin: [
    overview, customers, subscriptions, billing, recon,
    { to: '/insights', label: 'Insights', icon: LineChart },
    assistant,
    { to: '/catalog', label: 'Catalog', icon: Package },
    { to: '/audit', label: 'Audit', icon: ScrollText },
  ],
  staff: [overview, customers, subscriptions, billing, recon, assistant],
  customer: [
    overview,
    subscriptions,
    { to: '/invoices', label: 'Invoices', icon: FileText },
    { to: '/payments', label: 'Payments', icon: CreditCard },
  ],
}
