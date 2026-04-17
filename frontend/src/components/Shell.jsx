import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import {
  LayoutDashboard, Ticket, Users, BookOpen, HelpCircle,
  FileText, LogOut, ChevronRight, BarChart2, PlusCircle
} from 'lucide-react'

const NAV = {
  admin: [
    { label: 'Dashboard',     icon: LayoutDashboard, path: '/admin' },
    { label: 'Manage Agents', icon: Users,            path: '/admin/agents' },
    { label: 'Manage Customers', icon: Users,          path: '/admin/customers' },
    { label: 'Manage FAQs',   icon: HelpCircle,       path: '/admin/faqs' },
    { label: 'Knowledge Base',icon: BookOpen,         path: '/admin/kb' },
    { label: 'Reports',       icon: BarChart2,        path: '/admin/reports' },
  ],
  agent: [
    { label: 'Dashboard',        icon: LayoutDashboard, path: '/agent' },
    { label: 'All Tickets',      icon: Ticket,          path: '/agent/tickets' },
    { label: 'Change Password',  icon: Users,           path: '/agent/password' },
  ],
  customer: [
    { label: 'My Tickets',    icon: Ticket,          path: '/customer' },
    { label: 'New Ticket',    icon: PlusCircle,      path: '/customer/create' },
    { label: 'FAQs',          icon: HelpCircle,      path: '/customer/faqs' },
    { label: 'Knowledge Base',icon: BookOpen,        path: '/customer/kb' },
    { label: 'Change Password',icon: Users,           path: '/customer/password' },
  ],
}

const ROLE_LABEL = { admin: 'Admin Panel', agent: 'Agent Panel', customer: 'Customer Panel' }

export default function Shell({ children, title }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const nav = NAV[user?.role] || []

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="shell">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-dot" />
          SupportSphere
        </div>

        <div style={{ padding: '12px 12px 4px', fontSize: 11, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,.3)' }}>
          {ROLE_LABEL[user?.role]}
        </div>

        <nav className="sidebar-nav">
          {nav.map(({ label, icon: Icon, path }) => {
            const active = location.pathname === path
            return (
              <div key={path} className={`sidebar-item ${active ? 'active' : ''}`} onClick={() => navigate(path)}>
                <Icon size={16} />
                <span>{label}</span>
                {active && <ChevronRight size={13} style={{ marginLeft: 'auto', opacity: .5 }} />}
              </div>
            )
          })}
        </nav>

        <div className="sidebar-footer">
          <div style={{ padding: '8px 10px', borderRadius: 8, background: 'rgba(255,255,255,.06)', marginBottom: 8 }}>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,.5)', marginBottom: 1 }}>Signed in as</div>
            <div style={{ fontSize: 13, color: '#fff', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user?.name || user?.email}</div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,.4)', textTransform: 'capitalize' }}>{user?.role}</div>
          </div>
          <button className="sidebar-item" style={{ width: '100%', border: 'none', background: 'transparent' }} onClick={handleLogout}>
            <LogOut size={15} />
            <span>Log out</span>
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="main-area">
        <header className="topbar">
          <span className="topbar-title">{title || ''}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              background: 'var(--brand-light)', color: 'var(--brand)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 13
            }}>
              {(user?.name || user?.email || '?')[0].toUpperCase()}
            </div>
          </div>
        </header>
        <main className="page-content">{children}</main>
      </div>
    </div>
  )
}