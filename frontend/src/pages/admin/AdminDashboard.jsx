import { useEffect, useState } from 'react'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { Users, HelpCircle, Ticket, BookOpen, TrendingUp } from 'lucide-react'
import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'

const COLORS = ['#dc2626', '#f59e0b', '#16a34a']

export default function AdminDashboard() {
  const [data, setData] = useState(null)
  const [selectedAgent, setSelectedAgent] = useState(null)

  useEffect(() => {
    api.get('/admin/dashboard').then(r => setData(r.data)).catch(() => {})
  }, [])

  if (!data) return (
    <Shell title="Dashboard">
      <div style={{ color: 'var(--text-muted)', padding: 40, textAlign: 'center' }}>Loading dashboard…</div>
    </Shell>
  )

  const { counts, priority, queue, monthly, agents } = data

  const priorityChart = [
    { name: 'Low', value: priority.low || 0 },
    { name: 'Medium', value: priority.medium || 0 },
    { name: 'High', value: priority.high || 0 },
  ]

  const effBuckets = { low: [], medium: [], high: [] }
  agents.forEach(a => {
    if (a.efficiency_pct < 40) effBuckets.low.push(a.agent_name)
    else if (a.efficiency_pct < 70) effBuckets.medium.push(a.agent_name)
    else effBuckets.high.push(a.agent_name)
  })
  const effChart = [
    { name: 'Low (<40%)', value: effBuckets.low.length, agents: effBuckets.low },
    { name: 'Mid (40–70%)', value: effBuckets.medium.length, agents: effBuckets.medium },
    { name: 'High (>70%)', value: effBuckets.high.length, agents: effBuckets.high },
  ]

  const maxHandled = Math.max(...agents.map(a => a.resolved + a.messages_sent), 1)

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const d = payload[0].payload
    return (
      <div style={{ background: '#fff', border: '1px solid var(--border)', padding: '10px 14px', borderRadius: 10, fontSize: 13 }}>
        <b>{d.name}</b>
        <div style={{ color: 'var(--text-secondary)', marginTop: 4 }}>Agents: {d.agents?.join(', ') || 'None'}</div>
      </div>
    )
  }

  return (
    <Shell title="Dashboard">
      <div className="page-header">
        <h1>Admin Dashboard</h1>
        <p>Overview of support operations</p>
      </div>

      {/* Stat cards */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
        {[
          { label: 'Total Tickets', value: counts.total, icon: Ticket, color: '#eff6ff' },
          { label: 'Open', value: counts.open, icon: TrendingUp, color: '#fef2f2' },
          { label: 'In Progress', value: counts.in_progress, icon: TrendingUp, color: '#fffbeb' },
          { label: 'Resolved', value: counts.resolved, icon: TrendingUp, color: '#f0fdf4' },
          { label: 'Agents', value: agents.length, icon: Users, color: '#fdf4ff' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="stat-card" style={{ borderLeft: `3px solid var(--brand)` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div className="stat-card-label">{label}</div>
                <div className="stat-card-value">{value ?? '—'}</div>
              </div>
              <div style={{ width: 38, height: 38, borderRadius: 10, background: color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={18} color="var(--brand)" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Monthly trend */}
        <div className="card">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, marginBottom: 18 }}>Monthly Ticket Volume</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={monthly} barSize={18}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid var(--border)', fontSize: 13 }} />
              <Bar dataKey="count" name="Tickets" fill="var(--brand)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Priority donut */}
        <div className="card">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, marginBottom: 10 }}>Priority Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={priorityChart} dataKey="value" innerRadius={55} outerRadius={88} paddingAngle={3}>
                {priorityChart.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid var(--border)', fontSize: 13 }} />
              <Legend iconType="circle" iconSize={10} wrapperStyle={{ fontSize: 13 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Agent performance bars */}
        <div className="card">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, marginBottom: 18 }}>Agent Performance</h3>
          {agents.length === 0 && <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>No agents yet.</p>}
          {agents.map(a => {
            const total = a.resolved + a.messages_sent
            const pct = total ? Math.round((total / maxHandled) * 100) : 0
            return (
              <div key={a.agent_id} style={{ marginBottom: 16, cursor: 'pointer' }} onClick={() => setSelectedAgent(a)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 5 }}>
                  <span style={{ fontWeight: 600 }}>{a.agent_name}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{total} handled</span>
                </div>
                <div style={{ height: 8, background: 'var(--bg)', borderRadius: 99, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${pct}%`, background: 'var(--brand)', borderRadius: 99, transition: 'width .4s ease' }} />
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3 }}>
                  {a.resolved} resolved · {a.efficiency_pct.toFixed(0)}% efficiency
                </div>
              </div>
            )
          })}
        </div>

        {/* Efficiency distribution */}
        <div className="card">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, marginBottom: 10 }}>Efficiency Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={effChart} dataKey="value" innerRadius={55} outerRadius={88} paddingAngle={3}>
                {effChart.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="circle" iconSize={10} wrapperStyle={{ fontSize: 13 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Queue breakdown */}
      <div className="card" style={{ marginTop: 20 }}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, marginBottom: 14 }}>Queue Breakdown</h3>
        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
          {Object.entries(queue.stats || {}).map(([q, count]) => (
            <div key={q} style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '14px 22px', textAlign: 'center', minWidth: 110 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700 }}>{count}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3, fontWeight: 600 }}>{q}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Agent detail modal */}
      {selectedAgent && <AgentModal agent={selectedAgent} onClose={() => setSelectedAgent(null)} />}
    </Shell>
  )
}

function AgentModal({ agent, onClose }) {
  const [perf, setPerf] = useState(null)
  useEffect(() => {
    api.get(`/admin/agents/${agent.agent_id}/performance`).then(r => setPerf(r.data)).catch(() => {})
  }, [agent.agent_id])

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }} onClick={onClose}>
      <div className="card" style={{ width: 420, padding: 28 }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }}>{agent.agent_name}</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-muted)' }}>×</button>
        </div>
        {!perf ? <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Loading…</p> : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            {[
              ['Resolved', perf.resolved],
              ['Messages Sent', perf.messages_sent],
              ['Pending', perf.pending],
              ['Avg Resolution', `${perf.avg_resolution_hours}h`],
              ['Efficiency', `${perf.efficiency_pct.toFixed(1)}%`],
            ].map(([label, val]) => (
              <div key={label} style={{ background: 'var(--bg)', borderRadius: 'var(--radius)', padding: '12px 16px', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.07em' }}>{label}</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, marginTop: 4 }}>{val}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
