import { useEffect, useState } from 'react'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { Pencil, Trash2, Plus, X, UserCheck, KeyRound, Copy, Check } from 'lucide-react'

const DEPARTMENTS = ['IT', 'HR', 'Finance', 'Facilities']

export default function ManageAgents() {
  const [agents, setAgents] = useState([])
  const [workload, setWorkload] = useState({})
  const [form, setForm] = useState({ name: '', email: '', department: '' })
  const [editId, setEditId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [generatedPwd, setGeneratedPwd] = useState(null)
  const [generatedFor, setGeneratedFor] = useState('')
  const [copied, setCopied] = useState(false)

  const load = async () => {
    const [agRes, wlRes] = await Promise.all([
      api.get('/users/agents').catch(() => ({ data: [] })),
      api.get('/users/agents/workload').catch(() => ({ data: [] })),
    ])
    setAgents(agRes.data || [])
    const wlMap = {}
    ;(wlRes.data || []).forEach(w => { wlMap[w.agent_id] = w })
    setWorkload(wlMap)
  }

  useEffect(() => { load() }, [])

  const save = async () => {
    if (!form.name || !form.email) return
    setLoading(true)
    try {
      if (editId) {
        await api.put(`/users/agents/${editId}`, form)
        setEditId(null)
      } else {
        const res = await api.post('/users/agents', form)
        showPassword(res.data.generated_password, form.name)
      }
      setForm({ name: '', email: '', department: '' })
      setShowForm(false)
      load()
    } catch (err) { alert(err.response?.data?.detail || 'Failed') }
    finally { setLoading(false) }
  }

  const resetPassword = async (agent) => {
    if (!confirm(`Reset password for ${agent.name || agent.email}?`)) return
    const res = await api.post(`/users/agents/${agent.id}/reset-password`)
    showPassword(res.data.generated_password, agent.name || agent.email)
    load()
  }

  const showPassword = (pwd, name) => { setGeneratedPwd(pwd); setGeneratedFor(name); setCopied(false) }
  const copyPwd = () => { navigator.clipboard.writeText(generatedPwd); setCopied(true); setTimeout(() => setCopied(false), 2000) }
  const del = async (id) => { if (!confirm('Delete this agent?')) return; await api.delete(`/users/agents/${id}`); load() }
  const startEdit = (a) => { setForm({ name: a.name || '', email: a.email, department: a.department || '' }); setEditId(a.id); setShowForm(true) }
  const cancel = () => { setForm({ name: '', email: '', department: '' }); setEditId(null); setShowForm(false) }

  const getWorkloadColor = (count) => {
    if (count >= 30) return 'var(--danger)'
    if (count >= 20) return '#f59e0b'
    return 'var(--success)'
  }

  return (
    <Shell title="Manage Agents">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div><h1>Manage Agents</h1><p>Create and manage support agent accounts</p></div>
        <button className="btn btn-primary" onClick={() => { cancel(); setShowForm(true) }}>
          <Plus size={15} /> New Agent
        </button>
      </div>

      {generatedPwd && (
        <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 'var(--radius-lg)', padding: '16px 20px', marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontWeight: 700, color: '#166534', marginBottom: 6 }}>Password for {generatedFor}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <code style={{ background: '#dcfce7', padding: '6px 14px', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: '#166534', letterSpacing: '.05em' }}>{generatedPwd}</code>
                <button onClick={copyPwd} className="btn btn-secondary btn-sm" style={{ gap: 5 }}>
                  {copied ? <><Check size={13} /> Copied!</> : <><Copy size={13} /> Copy</>}
                </button>
              </div>
              <div style={{ fontSize: 12, color: '#16a34a', marginTop: 8 }}>Share this with the agent — it will not be shown again once you close this banner.</div>
            </div>
            <button onClick={() => setGeneratedPwd(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#16a34a', fontSize: 20 }}>×</button>
          </div>
        </div>
      )}

      {showForm && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700 }}>{editId ? 'Edit Agent' : 'Create New Agent'}</h3>
            <button onClick={cancel} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X size={18} /></button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 14, marginBottom: 16 }}>
            <div className="field" style={{ margin: 0 }}>
              <label>Full Name</label>
              <input className="input" placeholder="Jane Smith" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="field" style={{ margin: 0 }}>
              <label>Email Address</label>
              <input className="input" type="email" placeholder="agent@company.com" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
            </div>
            <div className="field" style={{ margin: 0 }}>
              <label>Department</label>
              <select className="input" value={form.department} onChange={e => setForm({ ...form, department: e.target.value })}>
                <option value="">No department (receives all)</option>
                {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" onClick={save} disabled={loading}>{loading ? 'Saving…' : editId ? 'Update Agent' : 'Create Agent'}</button>
            <button className="btn btn-secondary" onClick={cancel}>Cancel</button>
          </div>
        </div>
      )}

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {agents.length === 0 ? (
          <div className="empty-state" style={{ padding: 60 }}><UserCheck size={40} /><p style={{ marginTop: 12 }}>No agents yet.</p></div>
        ) : (
          <table className="tbl">
            <thead>
              <tr><th>Name</th><th>Email</th><th>Department</th><th>Workload</th><th>Temp Password</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {agents.map(a => {
                const wl = workload[a.id]
                const count = wl?.active_tickets ?? 0
                return (
                  <tr key={a.id}>
                    <td style={{ fontWeight: 600 }}>{a.name || '—'}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{a.email}</td>
                    <td>
                      {a.department
                        ? <span className="badge badge-info">{a.department}</span>
                        : <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>All queues</span>}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ flex: 1, height: 6, background: 'var(--border)', borderRadius: 99, overflow: 'hidden', minWidth: 60 }}>
                          <div style={{ height: '100%', width: `${Math.min((count / 30) * 100, 100)}%`, background: getWorkloadColor(count), borderRadius: 99, transition: 'width .3s' }} />
                        </div>
                        <span style={{ fontSize: 12, color: getWorkloadColor(count), fontWeight: 600, minWidth: 32 }}>{count}/30</span>
                      </div>
                    </td>
                    <td>
                      {a.temp_password
                        ? <code style={{ background: 'var(--bg)', padding: '2px 8px', borderRadius: 5, fontSize: 13, border: '1px solid var(--border)' }}>{a.temp_password}</code>
                        : <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>Changed by agent</span>}
                    </td>
                    <td><span className={`badge badge-${a.is_active ? 'resolved' : 'closed'}`}>{a.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button className="btn btn-secondary btn-sm" onClick={() => startEdit(a)} style={{ padding: '5px 9px' }} title="Edit"><Pencil size={14} /></button>
                        <button className="btn btn-secondary btn-sm" onClick={() => resetPassword(a)} style={{ padding: '5px 9px' }} title="Reset password"><KeyRound size={14} /></button>
                        <button className="btn btn-danger btn-sm" onClick={() => del(a.id)} style={{ padding: '5px 9px' }} title="Delete"><Trash2 size={14} /></button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </Shell>
  )
}