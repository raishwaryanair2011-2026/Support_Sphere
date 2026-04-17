import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { Ticket, Clock, CheckCircle, AlertCircle } from 'lucide-react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

export default function AgentDashboard() {
  const [tickets, setTickets] = useState([])
  const [monthly, setMonthly] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/tickets/all?page_size=100').then(r => setTickets(r.data?.items || [])).catch(() => {})
    // monthly stats from dashboard endpoint
    api.get('/admin/dashboard').then(r => setMonthly(r.data?.monthly || [])).catch(() => {})
  }, [])

  const counts = {
    open: tickets.filter(t => t.status === 'open').length,
    in_progress: tickets.filter(t => t.status === 'in_progress').length,
    resolved: tickets.filter(t => t.status === 'resolved').length,
    total: tickets.length,
  }

  const recent = tickets.slice(0, 8)

  return (
    <Shell title="Dashboard">
      <div className="page-header"><h1>Agent Dashboard</h1><p>Your support queue overview</p></div>

      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        {[
          { label: 'Total Tickets', value: counts.total, icon: Ticket, color: '#eff6ff' },
          { label: 'Open', value: counts.open, icon: AlertCircle, color: '#fef2f2' },
          { label: 'In Progress', value: counts.in_progress, icon: Clock, color: '#fffbeb' },
          { label: 'Resolved', value: counts.resolved, icon: CheckCircle, color: '#f0fdf4' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="stat-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div className="stat-card-label">{label}</div>
                <div className="stat-card-value">{value}</div>
              </div>
              <div style={{ width: 38, height: 38, borderRadius: 10, background: color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={18} color="var(--brand)" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
        {/* Recent tickets */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 15 }}>Recent Tickets</span>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate('/agent/tickets')}>View All</button>
          </div>
          <table className="tbl">
            <thead><tr><th>Ticket</th><th>Subject</th><th>Priority</th><th>Status</th></tr></thead>
            <tbody>
              {recent.map(t => (
                <tr key={t.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/agent/tickets/${t.id}`)}>
                  <td style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-muted)' }}>#{t.ticket_number}</td>
                  <td style={{ fontWeight: 500, maxWidth: 220 }}><span style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.subject}</span></td>
                  <td><span className={`badge badge-${t.priority}`}>{t.priority}</span></td>
                  <td><span className={`badge badge-${t.status}`}>{t.status.replace('_', ' ')}</span></td>
                </tr>
              ))}
              {recent.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No tickets yet.</td></tr>}
            </tbody>
          </table>
        </div>

        {/* Monthly chart */}
        <div className="card">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, marginBottom: 18 }}>Monthly Volume</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={monthly} barSize={14}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid var(--border)', fontSize: 13 }} />
              <Bar dataKey="count" fill="var(--brand)" radius={[4, 4, 0, 0]} name="Tickets" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Shell>
  )
}
