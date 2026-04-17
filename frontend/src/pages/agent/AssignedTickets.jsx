import { useEffect, useState } from 'react'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { useNavigate } from 'react-router-dom'
import { Ticket } from 'lucide-react'

const PRIORITY_COLORS = { high: 'danger', medium: 'warning', low: 'resolved' }
const STATUS_COLORS = { open: 'info', in_progress: 'warning', resolved: 'resolved', closed: 'closed' }

export default function AssignedTickets() {
  const [tickets, setTickets] = useState([])
  const [filters, setFilters] = useState({ status: '', queue: '', priority: '' })
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.status) params.append('status', filters.status)
      if (filters.queue) params.append('queue', filters.queue)
      if (filters.priority) params.append('priority', filters.priority)
      // Feature 1: call /my instead of /all — only returns assigned tickets
      const res = await api.get(`/tickets/my?${params}`)
      setTickets(res.data.items || res.data || [])
    } catch { setTickets([]) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [filters])

  return (
    <Shell title="My Tickets">
      <div className="page-header">
        <h1>My Assigned Tickets</h1>
        <p>Only tickets assigned to you are shown here</p>
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        {[
          { key: 'status', opts: ['open', 'in_progress', 'resolved', 'closed'] },
          { key: 'queue', opts: ['IT', 'HR', 'Finance', 'Facilities'] },
          { key: 'priority', opts: ['low', 'medium', 'high'] },
        ].map(({ key, opts }) => (
          <select
            key={key}
            className="input"
            style={{ width: 150, padding: '8px 12px' }}
            value={filters[key]}
            onChange={e => setFilters(f => ({ ...f, [key]: e.target.value }))}
          >
            <option value="">All {key}s</option>
            {opts.map(o => <option key={o} value={o}>{o}</option>)}
          </select>
        ))}
        <button className="btn btn-secondary" onClick={load}>Refresh</button>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div className="empty-state" style={{ padding: 50 }}><p>Loading…</p></div>
        ) : tickets.length === 0 ? (
          <div className="empty-state" style={{ padding: 60 }}>
            <Ticket size={36} />
            <p style={{ marginTop: 12 }}>No tickets assigned to you yet.</p>
          </div>
        ) : (
          <table className="tbl">
            <thead><tr><th>Ticket</th><th>Subject</th><th>Queue</th><th>Priority</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>
              {tickets.map(t => (
                <tr key={t.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/agent/tickets/${t.id}`)}>
                  <td><span className="code" style={{ fontSize: 12 }}>{t.ticket_number}</span></td>
                  <td style={{ fontWeight: 500 }}>{t.subject}</td>
                  <td><span className="badge badge-info">{t.queue}</span></td>
                  <td><span className={`badge badge-${PRIORITY_COLORS[t.priority] || 'info'}`}>{t.priority}</span></td>
                  <td><span className={`badge badge-${STATUS_COLORS[t.status] || 'info'}`}>{t.status?.replace('_', ' ')}</span></td>
                  <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{new Date(t.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Shell>
  )
}