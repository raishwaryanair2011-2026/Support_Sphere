import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { MessageCircle, Pencil, Trash2, Check, X, Search } from 'lucide-react'

export default function CustomerTickets() {
  const [tickets, setTickets] = useState([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('')
  const [editId, setEditId] = useState(null)
  const [editForm, setEditForm] = useState({ subject: '', description: '' })
  const navigate = useNavigate()

  const load = async () => {
    try {
      const res = await api.get('/tickets/my?page_size=50')
      setTickets(res.data?.items || [])
      setTotal(res.data?.total || 0)
    } catch { setTickets([]) }
  }

  useEffect(() => { load(); const t = setInterval(load, 15000); return () => clearInterval(t) }, [])

  const del = async (id) => {
    if (!confirm('Delete this ticket?')) return
    await api.delete(`/tickets/${id}`); load()
  }

  const startEdit = (t) => { setEditId(t.id); setEditForm({ subject: t.subject, description: t.description }) }
  const cancelEdit = () => { setEditId(null) }
  const saveEdit = async (id) => {
    try { await api.put(`/tickets/${id}`, editForm); setEditId(null); load() }
    catch { alert('Update failed') }
  }

  const filtered = tickets
    .filter(t => !filter || t.status === filter)
    .filter(t => !search || t.subject.toLowerCase().includes(search.toLowerCase()) || t.ticket_number.toLowerCase().includes(search.toLowerCase()))

  return (
    <Shell title="My Tickets">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div><h1>My Tickets</h1><p>{total} ticket{total !== 1 ? 's' : ''} total</p></div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input className="input" placeholder="Search tickets…" value={search} onChange={e => setSearch(e.target.value)} style={{ paddingLeft: 36 }} />
        </div>
        <select value={filter} onChange={e => setFilter(e.target.value)}
          style={{ padding: '10px 14px', border: '1.5px solid var(--border)', borderRadius: 'var(--radius)', fontSize: 14, background: '#fff', color: 'var(--text-primary)' }}>
          <option value="">All Status</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {filtered.length === 0 && (
          <div className="card empty-state"><p>No tickets found.</p></div>
        )}
        {filtered.map(t => {
          const isEditing = editId === t.id
          return (
            <div key={t.id} className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '14px 18px', display: 'flex', gap: 16, alignItems: 'flex-start' }}>
                {/* Colour bar */}
                <div style={{ width: 4, borderRadius: 99, alignSelf: 'stretch', background: t.status === 'open' ? 'var(--danger)' : t.status === 'in_progress' ? '#f59e0b' : 'var(--success)', flexShrink: 0 }} />

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  {isEditing ? (
                    <div>
                      <input className="input" value={editForm.subject} onChange={e => setEditForm({ ...editForm, subject: e.target.value })} style={{ marginBottom: 8 }} />
                      <textarea className="input" rows={2} value={editForm.description} onChange={e => setEditForm({ ...editForm, description: e.target.value })} style={{ resize: 'none' }} />
                    </div>
                  ) : (
                    <>
                      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 3 }}>{t.subject}</div>
                      <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                        #{t.ticket_number} · {new Date(t.created_at).toLocaleDateString()} · Queue: {t.queue || '—'}
                      </div>
                    </>
                  )}
                </div>

                {/* Right */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8, flexShrink: 0 }}>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span className={`badge badge-${t.status}`}>{t.status.replace('_', ' ')}</span>
                    <span className={`badge badge-${t.priority}`}>{t.priority}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/customer/tickets/${t.id}`)} style={{ padding: '5px 9px' }} title="View thread">
                      <MessageCircle size={14} />
                    </button>
                    {!isEditing && t.status === 'open' && (
                      <button className="btn btn-secondary btn-sm" onClick={() => startEdit(t)} style={{ padding: '5px 9px' }} title="Edit">
                        <Pencil size={14} />
                      </button>
                    )}
                    {isEditing && (
                      <>
                        <button className="btn btn-primary btn-sm" onClick={() => saveEdit(t.id)} style={{ padding: '5px 9px' }}><Check size={14} /></button>
                        <button className="btn btn-secondary btn-sm" onClick={cancelEdit} style={{ padding: '5px 9px' }}><X size={14} /></button>
                      </>
                    )}
                    {t.status === 'open' && !isEditing && (
                      <button className="btn btn-danger btn-sm" onClick={() => del(t.id)} style={{ padding: '5px 9px' }} title="Delete">
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </Shell>
  )
}
