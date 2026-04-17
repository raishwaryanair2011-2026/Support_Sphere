import { useEffect, useState } from 'react'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line } from 'recharts'

export default function Reports() {
  const [data, setData] = useState(null)

  useEffect(() => {
    api.get('/admin/dashboard').then(r => setData(r.data)).catch(() => {})
  }, [])

  if (!data) return <Shell title="Reports"><div style={{ color: 'var(--text-muted)', padding: 40, textAlign: 'center' }}>Loading…</div></Shell>

  const { monthly, agents, counts } = data

  const agentChart = agents.map(a => ({
    name: a.agent_name.split(' ')[0],
    Resolved: a.resolved,
    Messages: a.messages_sent,
    Efficiency: parseFloat(a.efficiency_pct.toFixed(1)),
  }))

  return (
    <Shell title="Reports">
      <div className="page-header"><h1>Reports</h1><p>Analytics and performance overview</p></div>

      {/* Summary row */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 24 }}>
        {[
          { label: 'Total Tickets', value: counts.total },
          { label: 'Open', value: counts.open },
          { label: 'Resolved', value: counts.resolved },
          { label: 'Agents', value: agents.length },
        ].map(({ label, value }) => (
          <div key={label} className="stat-card">
            <div className="stat-card-label">{label}</div>
            <div className="stat-card-value">{value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Monthly volume */}
        <div className="card">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, marginBottom: 18 }}>Monthly Ticket Volume</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={monthly}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid var(--border)', fontSize: 13 }} />
              <Line type="monotone" dataKey="count" stroke="var(--brand)" strokeWidth={2} dot={{ r: 3 }} name="Tickets" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Agent resolved vs messages */}
        <div className="card">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, marginBottom: 18 }}>Agent Activity</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={agentChart} barSize={16}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid var(--border)', fontSize: 13 }} />
              <Legend wrapperStyle={{ fontSize: 13 }} />
              <Bar dataKey="Resolved" fill="var(--brand)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Messages" fill="#93c5fd" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Agent efficiency table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 15 }}>Agent Performance Summary</div>
        <table className="tbl">
          <thead>
            <tr><th>Agent</th><th>Resolved</th><th>Messages</th><th>Pending</th><th>Avg Resolution</th><th>Efficiency</th></tr>
          </thead>
          <tbody>
            {agents.map(a => (
              <tr key={a.agent_id}>
                <td style={{ fontWeight: 600 }}>{a.agent_name}</td>
                <td>{a.resolved}</td>
                <td>{a.messages_sent}</td>
                <td>{a.pending}</td>
                <td>{a.avg_resolution_hours}h</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ flex: 1, height: 6, background: 'var(--bg)', borderRadius: 99, overflow: 'hidden', maxWidth: 80 }}>
                      <div style={{ height: '100%', width: `${Math.min(a.efficiency_pct, 100)}%`, background: a.efficiency_pct >= 70 ? 'var(--success)' : a.efficiency_pct >= 40 ? '#f59e0b' : 'var(--danger)', borderRadius: 99 }} />
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{a.efficiency_pct.toFixed(0)}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Shell>
  )
}
