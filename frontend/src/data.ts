// Mock data for the template. Replace with calls to the FastAPI backend (/api/v1/...).

export const money = (n: number) =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: n % 1 ? 2 : 0 })

export const compact = (n: number) =>
  n >= 1000 ? `$${(n / 1000).toFixed(n >= 100000 ? 0 : 1)}K` : money(n)

export const revenueByMonth = [
  { label: 'May', collected: 31200, outstanding: 4200 },
  { label: 'Jun', collected: 33800, outstanding: 5100 },
  { label: 'Jul', collected: 35400, outstanding: 3900 },
  { label: 'Aug', collected: 36900, outstanding: 6200 },
  { label: 'Sep', collected: 39100, outstanding: 5400 },
  { label: 'Oct', collected: 42600, outstanding: 7800 },
]

export const subscriptionStatus = [
  { label: 'Active', value: 842, tone: 'orange' },
  { label: 'Paused', value: 64, tone: 'teal' },
  { label: 'Expired', value: 38, tone: 'blue' },
  { label: 'Cancelled', value: 21, tone: 'purple' },
]

export const customers = [
  { id: 'CUS-1001', name: 'Acme Robotics', email: 'billing@acme.io', plan: 'Business Yearly', status: 'Active', mrr: 1450, outstanding: 0 },
  { id: 'CUS-1002', name: 'Flivia Hartman', email: 'flivia@hartman.co', plan: 'Pro Monthly', status: 'Active', mrr: 240, outstanding: 240 },
  { id: 'CUS-1003', name: 'Marcus Riley', email: 'marcus@riley.dev', plan: 'Starter Monthly', status: 'Paused', mrr: 49, outstanding: 0 },
  { id: 'CUS-1004', name: 'Northwind Labs', email: 'ap@northwind.com', plan: 'Business Monthly', status: 'Active', mrr: 890, outstanding: 1780 },
  { id: 'CUS-1005', name: 'Priya Nair', email: 'priya@nair.in', plan: 'Pro Yearly', status: 'Active', mrr: 199, outstanding: 0 },
  { id: 'CUS-1006', name: 'Delta Freight', email: 'finance@deltafreight.com', plan: 'Business Monthly', status: 'Cancelled', mrr: 0, outstanding: 890 },
]

export const subscriptions = [
  { id: 'SUB-1042', customer: 'Acme Robotics', plan: 'Business Yearly', status: 'Active', next: '12 Nov 2026', amount: 1450 },
  { id: 'SUB-1043', customer: 'Flivia Hartman', plan: 'Pro Monthly', status: 'Active', next: '02 Nov 2026', amount: 240 },
  { id: 'SUB-1044', customer: 'Marcus Riley', plan: 'Starter Monthly', status: 'Paused', next: '—', amount: 49 },
  { id: 'SUB-1045', customer: 'Northwind Labs', plan: 'Business Monthly', status: 'Active', next: '05 Nov 2026', amount: 890 },
  { id: 'SUB-1046', customer: 'Priya Nair', plan: 'Pro Yearly', status: 'Active', next: '19 Jan 2027', amount: 199 },
  { id: 'SUB-1047', customer: 'Delta Freight', plan: 'Business Monthly', status: 'Cancelled', next: '—', amount: 890 },
  { id: 'SUB-1048', customer: 'Orbit Studio', plan: 'Pro Monthly', status: 'Expired', next: '—', amount: 240 },
]

export const invoices = [
  { id: 'INV-0187', customer: 'Flivia Hartman', amount: 2480, due: '31 Oct 2026', status: 'Paid' },
  { id: 'INV-0188', customer: 'Marcus Riley', amount: 540, due: '29 Oct 2026', status: 'Unpaid' },
  { id: 'INV-0189', customer: 'Northwind Labs', amount: 1780, due: '18 Oct 2026', status: 'Overdue' },
  { id: 'INV-0190', customer: 'Acme Robotics', amount: 1450, due: '12 Nov 2026', status: 'Draft' },
  { id: 'INV-0191', customer: 'Delta Freight', amount: 890, due: '05 Oct 2026', status: 'Overdue' },
  { id: 'INV-0192', customer: 'Priya Nair', amount: 199, due: '19 Nov 2026', status: 'Unpaid' },
]

export const payments = [
  { id: 'PAY-5521', invoice: 'INV-0187', customer: 'Flivia Hartman', method: 'Credit Card', amount: 2480, date: '31 Oct 2026', status: 'Successful' },
  { id: 'PAY-5520', invoice: 'INV-0185', customer: 'Acme Robotics', method: 'Bank Transfer', amount: 1450, date: '29 Oct 2026', status: 'Successful' },
  { id: 'PAY-5519', invoice: 'INV-0189', customer: 'Northwind Labs', method: 'AutoPay', amount: 890, date: '28 Oct 2026', status: 'Failed' },
  { id: 'PAY-5518', invoice: 'INV-0184', customer: 'Priya Nair', method: 'UPI', amount: 199, date: '27 Oct 2026', status: 'Pending' },
  { id: 'PAY-5517', invoice: 'INV-0181', customer: 'Orbit Studio', method: 'Credit Card', amount: 240, date: '24 Oct 2026', status: 'Refunded' },
]

export const reconciliation = [
  { id: 'BTX-901', desc: 'NEFT ACME ROBOTICS INV0190', amount: 1450, date: '30 Oct', match: 'INV-0190', confidence: 98, status: 'Matched' },
  { id: 'BTX-902', desc: 'UPI/FLIVIA H/ SUBSCR', amount: 240, date: '30 Oct', match: 'INV-0188', confidence: 71, status: 'Review required' },
  { id: 'BTX-903', desc: 'IMPS NORTHWIND LABS', amount: 900, date: '29 Oct', match: 'INV-0189', confidence: 64, status: 'Partially matched' },
  { id: 'BTX-904', desc: 'CHQ DEP 004417', amount: 3100, date: '28 Oct', match: '—', confidence: 0, status: 'Unmatched' },
  { id: 'BTX-905', desc: 'NEFT ACME ROBOTICS INV0185', amount: 1450, date: '28 Oct', match: 'PAY-5520', confidence: 100, status: 'Duplicate' },
]

export const churn = [
  { id: 'CUS-1004', customer: 'Northwind Labs', score: 86, level: 'High', period: 'Next 30 days', atRisk: 890, factors: ['2 failed payments', 'Overdue invoice 13 days'], action: 'Payment recovery call' },
  { id: 'CUS-1003', customer: 'Marcus Riley', score: 72, level: 'High', period: 'Next 45 days', atRisk: 49, factors: ['Paused twice', 'Declining usage'], action: 'Offer alternative plan' },
  { id: 'CUS-1002', customer: 'Flivia Hartman', score: 48, level: 'Medium', period: 'Next 60 days', atRisk: 240, factors: ['Renewal in 3 days', 'No renewal history'], action: 'Send renewal reminder' },
  { id: 'CUS-1005', customer: 'Priya Nair', score: 14, level: 'Low', period: '—', atRisk: 0, factors: ['Renewed 3 times'], action: 'None' },
]

export const audit = [
  { time: '31 Oct, 14:02', actor: 'Admin · Mimansa', action: 'Updated discount rule', entity: 'DISC-12', source: 'Web' },
  { time: '31 Oct, 13:40', actor: 'Payment Agent', action: 'Suggested match BTX-902 → INV-0188', entity: 'RECON-31', source: 'AI' },
  { time: '31 Oct, 13:41', actor: 'Staff · Rahul', action: 'Approved match BTX-901', entity: 'RECON-30', source: 'Web' },
  { time: '31 Oct, 11:15', actor: 'System', action: 'Generated invoice INV-0190', entity: 'SUB-1042', source: 'Billing job' },
  { time: '30 Oct, 17:22', actor: 'Staff · Rahul', action: 'Paused subscription', entity: 'SUB-1044', source: 'Web' },
  { time: '30 Oct, 09:03', actor: 'Unknown', action: 'Failed login attempt', entity: 'USR-0', source: 'API' },
]

export const products = [
  { id: 'PRD-01', name: 'Platform Seat', type: 'Service', price: 49, cost: 12, status: 'Active' },
  { id: 'PRD-02', name: 'Analytics Add-on', type: 'Add-on', price: 29, cost: 6, status: 'Active' },
  { id: 'PRD-03', name: 'Priority Support', type: 'Service', price: 99, cost: 40, status: 'Inactive' },
]
export const plans = [
  { id: 'PLN-01', name: 'Starter', billing: 'Monthly', price: 49, minQty: 1, status: 'Active' },
  { id: 'PLN-02', name: 'Pro', billing: 'Monthly', price: 240, minQty: 1, status: 'Active' },
  { id: 'PLN-03', name: 'Business', billing: 'Yearly', price: 14500, minQty: 5, status: 'Active' },
]
export const taxes = [
  { id: 'TAX-01', name: 'GST', rate: '18%', from: '01 Apr 2026', status: 'Active' },
  { id: 'TAX-02', name: 'Digital Services', rate: '5%', from: '01 Jan 2026', status: 'Inactive' },
]
export const discounts = [
  { id: 'DISC-12', name: 'Yearly saver', value: '10%', minQty: 5, used: '34 / 100', status: 'Active' },
  { id: 'DISC-09', name: 'Welcome', value: '$20', minQty: 1, used: '100 / 100', status: 'Expired' },
]

export const notifications = [
  { id: 1, text: 'Invoice INV-0192 generated', time: '2h ago' },
  { id: 2, text: 'Your subscription renews on 12 Nov', time: 'Yesterday' },
  { id: 3, text: 'Payment PAY-5521 successful', time: '2 days ago' },
]

// Customer role: "my" data
export const mySubscriptions = subscriptions.filter((s) => s.customer === 'Flivia Hartman')
export const myInvoices = invoices.filter((i) => i.customer === 'Flivia Hartman' || i.id === 'INV-0188')
export const myPayments = payments.filter((p) => p.customer === 'Flivia Hartman')
