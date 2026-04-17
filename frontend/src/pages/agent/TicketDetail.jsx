import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { ArrowLeft, Send, Paperclip, Sparkles } from 'lucide-react'

export default function AgentTicketDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [ticket, setTicket] = useState(null)
  const [reply, setReply] = useState('')
  const [status, setStatus] = useState('')
  const [queue, setQueue] = useState('')
  const [priority, setPriority] = useState('')
  const [loading, setLoading] = useState(false)
  const [previewFile, setPreviewFile] = useState(null)
  const endRef = useRef(null)

  const load = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/tickets/${id}`)
      setTicket(res.data)
      setStatus(res.data.status)
      setQueue(res.data.queue || 'IT')
      setPriority(res.data.priority)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [id])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [ticket?.messages?.length])

  const updateField = async (field, value) => {
    await api.patch(`/tickets/${id}`, { [field]: value })
    load()
  }

  const sendReply = async () => {
    if (!reply.trim()) return
    await api.post(`/tickets/${id}/reply`, { message: reply })
    if (status === 'open') await api.patch(`/tickets/${id}`, { status: 'in_progress' })
    setReply(''); load()
  }

  if (!ticket) return (
    <Shell title="Ticket Detail">
      <div style={{ color: 'var(--text-muted)', padding: 40, textAlign: 'center' }}>Loading ticket…</div>
    </Shell>
  )

  const fmt = (d) => d ? new Date(d).toLocaleString() : '—'

  return (
    <Shell title={`Ticket #${ticket.ticket_number}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 22 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)}><ArrowLeft size={14} /> Back</button>
        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>#{ticket.ticket_number}</span>
        <span className={`badge badge-${ticket.status}`}>{ticket.status.replace('_', ' ')}</span>
        <span className={`badge badge-${ticket.priority}`}>{ticket.priority}</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 20, alignItems: 'flex-start' }}>
        {/* Main */}
        <div>
          {/* Header */}
          <div className="card" style={{ marginBottom: 16 }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 19, fontWeight: 700, marginBottom: 8 }}>{ticket.subject}</h2>
            <div style={{ display: 'flex', gap: 20, fontSize: 13, color: 'var(--text-muted)' }}>
              <span>Customer: <b style={{ color: 'var(--text-primary)' }}>{ticket.customer_name || '—'}</b></span>
              <span>Created: <b style={{ color: 'var(--text-primary)' }}>{fmt(ticket.created_at)}</b></span>
              {ticket.closed_at && <span>Resolved: <b style={{ color: 'var(--success)' }}>{fmt(ticket.closed_at)}</b></span>}
            </div>
          </div>

          {/* AI Summary */}
          {ticket.ai_summary && (
            <div style={{ background: '#eef2ff', border: '1px solid #c7d2fe', borderRadius: 'var(--radius-lg)', padding: 16, marginBottom: 16, display: 'flex', gap: 12 }}>
              <Sparkles size={16} color="#6366f1" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#6366f1', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '.06em' }}>AI Summary</div>
                <p style={{ fontSize: 14, color: '#3730a3', lineHeight: 1.6 }}>{ticket.ai_summary}</p>
              </div>
            </div>
          )}

          {/* Attachments */}
          {ticket.attachments?.length > 0 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 7 }}>
                <Paperclip size={14} /> Attachments
              </div>
              {ticket.attachments.map(f => (
                <div key={f.id}>
                  <button className="btn btn-secondary btn-sm" onClick={() => setPreviewFile(previewFile === f.id ? null : f.id)} style={{ marginBottom: 8 }}>
                    {f.file_name || 'View attachment'}
                  </button>
                  {previewFile === f.id && (
                    <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden', marginBottom: 8 }}>
                      <iframe src={`http://127.0.0.1:8000/${f.file_path}`} width="100%" height="300" style={{ border: 'none', display: 'block' }} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Conversation */}
          <div className="card">
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, marginBottom: 14 }}>Conversation</h3>
            <div className="chat-wrap" style={{ marginBottom: 14 }}>
              {ticket.messages?.map(m => {
                const isAgent = m.sender_role === 'agent'
                return (
                  <div key={m.id} style={{ display: 'flex', flexDirection: 'column', alignItems: isAgent ? 'flex-end' : 'flex-start' }}>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 3 }}>{isAgent ? 'Agent' : 'Customer'}</div>
                    <div className={`bubble bubble-${isAgent ? 'agent' : 'customer'}`}>{m.message}</div>
                    <div className="bubble-meta">{fmt(m.created_at)}</div>
                  </div>
                )
              })}
              <div ref={endRef} />
            </div>
            <textarea className="input" rows={3} placeholder="Reply to customer…" value={reply} onChange={e => setReply(e.target.value)} onKeyDown={e => e.ctrlKey && e.key === 'Enter' && sendReply()} style={{ resize: 'none', marginBottom: 10 }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Ctrl+Enter to send</span>
              <button className="btn btn-primary" onClick={sendReply}><Send size={14} /> Send Reply</button>
            </div>
          </div>
        </div>

        {/* Sidebar controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card">
            <h4 style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, marginBottom: 14 }}>Ticket Controls</h4>
            <div className="field">
              <label>Status</label>
              <select className="input" value={status} onChange={e => { setStatus(e.target.value); updateField('status', e.target.value) }}>
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
            </div>
            <div className="field">
              <label>Queue</label>
              <select className="input" value={queue} onChange={e => { setQueue(e.target.value); updateField('queue', e.target.value) }}>
                <option value="IT">IT</option>
                <option value="HR">HR</option>
                <option value="Finance">Finance</option>
                <option value="Facilities">Facilities</option>
              </select>
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>Priority</label>
              <select className="input" value={priority} onChange={e => { setPriority(e.target.value); updateField('priority', e.target.value) }}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>

          <div className="card">
            <h4 style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Details</h4>
            {[
              ['Ticket #', `#${ticket.ticket_number}`],
              ['Queue', ticket.queue || '—'],
              ['Created', fmt(ticket.created_at)],
              ['Updated', fmt(ticket.updated_at)],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '7px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ color: 'var(--text-muted)' }}>{k}</span>
                <span style={{ fontWeight: 500 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Shell>
  )
}
