import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { ArrowLeft, Send, Sparkles, Paperclip } from 'lucide-react'

export default function CustomerTicketDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [ticket, setTicket] = useState(null)
  const [reply, setReply] = useState('')
  const endRef = useRef(null)

  const load = async () => {
    const res = await api.get(`/tickets/${id}`)
    setTicket(res.data)
  }

  useEffect(() => { load() }, [id])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [ticket?.messages?.length])

  const sendReply = async () => {
    if (!reply.trim()) return
    await api.post(`/tickets/${id}/reply`, { message: reply })
    setReply(''); load()
  }

  if (!ticket) return <Shell title="Ticket"><div style={{ color: 'var(--text-muted)', padding: 40, textAlign: 'center' }}>Loading…</div></Shell>

  const fmt = (d) => d ? new Date(d).toLocaleString() : '—'

  return (
    <Shell title={`Ticket #${ticket.ticket_number}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 22 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/customer')}><ArrowLeft size={14} /> My Tickets</button>
        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>#{ticket.ticket_number}</span>
        <span className={`badge badge-${ticket.status}`}>{ticket.status.replace('_', ' ')}</span>
        <span className={`badge badge-${ticket.priority}`}>{ticket.priority}</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 20, alignItems: 'flex-start' }}>
        {/* Main column */}
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, marginBottom: 6 }}>{ticket.subject}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.65 }}>{ticket.description}</p>
          </div>

          {/* AI summary */}
          {ticket.ai_summary && (
            <div style={{ background: '#eef2ff', border: '1px solid #c7d2fe', borderRadius: 'var(--radius-lg)', padding: 16, marginBottom: 16, display: 'flex', gap: 12 }}>
              <Sparkles size={16} color="#6366f1" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#6366f1', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '.06em' }}>AI Summary</div>
                <p style={{ fontSize: 14, color: '#3730a3', lineHeight: 1.6 }}>{ticket.ai_summary}</p>
              </div>
            </div>
          )}

          {/* Attachments */}
          {ticket.attachments?.length > 0 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 7 }}>
                <Paperclip size={14} /> Attachments
              </div>
              {ticket.attachments.map(a => (
                <a key={a.id} href={`http://127.0.0.1:8000/${a.file_path}`} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm" style={{ marginRight: 8 }}>
                  {a.file_name || 'View file'}
                </a>
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
                  <div key={m.id} style={{ display: 'flex', flexDirection: 'column', alignItems: isAgent ? 'flex-start' : 'flex-end' }}>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 3 }}>{isAgent ? 'Support Agent' : 'You'}</div>
                    <div style={{
                      padding: '10px 14px', borderRadius: isAgent ? '14px 14px 14px 4px' : '14px 14px 4px 14px',
                      maxWidth: '72%', fontSize: 14, lineHeight: 1.55,
                      background: isAgent ? '#fff' : 'var(--brand)',
                      color: isAgent ? 'var(--text-primary)' : '#fff',
                      border: isAgent ? '1px solid var(--border)' : 'none',
                      boxShadow: '0 1px 3px rgba(0,0,0,.06)'
                    }}>{m.message}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>{fmt(m.created_at)}</div>
                  </div>
                )
              })}
              <div ref={endRef} />
            </div>

            {ticket.status !== 'resolved' && ticket.status !== 'closed' && (
              <>
                <textarea className="input" rows={3} placeholder="Reply to agent…" value={reply} onChange={e => setReply(e.target.value)} onKeyDown={e => e.ctrlKey && e.key === 'Enter' && sendReply()} style={{ resize: 'none', marginBottom: 10 }} />
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button className="btn btn-primary" onClick={sendReply}><Send size={14} /> Send</button>
                </div>
              </>
            )}
            {(ticket.status === 'resolved' || ticket.status === 'closed') && (
              <div style={{ textAlign: 'center', padding: '16px 0 4px', color: 'var(--text-muted)', fontSize: 14 }}>This ticket is {ticket.status}.</div>
            )}
          </div>
        </div>

        {/* Info sidebar */}
        <div className="card">
          <h4 style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Ticket Info</h4>
          {[
            ['Status', <span key="s" className={`badge badge-${ticket.status}`}>{ticket.status.replace('_', ' ')}</span>],
            ['Priority', <span key="p" className={`badge badge-${ticket.priority}`}>{ticket.priority}</span>],
            ['Queue', ticket.queue || '—'],
            ['Opened', fmt(ticket.created_at)],
            ['Resolved', ticket.closed_at ? fmt(ticket.closed_at) : '—'],
          ].map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13, padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ color: 'var(--text-muted)' }}>{k}</span>
              <span style={{ fontWeight: 500 }}>{v}</span>
            </div>
          ))}
        </div>
      </div>
    </Shell>
  )
}
