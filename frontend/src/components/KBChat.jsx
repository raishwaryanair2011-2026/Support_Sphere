import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send, Bot, Ticket } from 'lucide-react'
import api from '../api/axios'

function renderText(text) {
  if (!text) return null
  return text.split('\n').map((line, i) => {
    if (!line.trim()) return <div key={i} style={{ height: 5 }} />
    const parts = line.split(/(\*\*.*?\*\*)/g).map((p, j) =>
      p.startsWith('**') && p.endsWith('**') ? <strong key={j}>{p.slice(2, -2)}</strong> : p
    )
    return <div key={i} style={{ marginBottom: 4 }}>{parts}</div>
  })
}

function getVideoId(url) {
  const m = url?.match(/v=([^&]+)/)
  return m ? m[1] : null
}

export default function KBChat({ compact = false }) {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([{ role: 'bot', text: 'Hi 👋 How can I help you today?' }])
  const [input, setInput] = useState('')
  const [typing, setTyping] = useState(false)
  const endRef = useRef(null)
  const isFirstRender = useRef(true)

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [messages, typing])

  const HISTORY_LIMIT = 10  // keep last 10 exchanges (20 messages)

  const ask = async () => {
    const q = input.trim()
    if (!q) return
    setInput('')

    // Build updated messages including the new user message
    const newUserMsg = { role: 'user', text: q }
    const updatedMessages = [...messages, newUserMsg]
    setMessages(updatedMessages)
    setTyping(true)

    try {
      // Send last 10 exchanges as history (exclude the initial bot greeting)
      const history = updatedMessages
        .filter(m => m.role === 'user' || (m.role === 'bot' && m.text !== 'Hi 👋 How can I help you today?'))
        .slice(-(HISTORY_LIMIT * 2))  // 10 user + 10 bot = 20 messages max
        .map(m => ({ role: m.role, text: m.text }))

      const res = await api.post('/kb/ask', {
        question: q,
        history: history.slice(0, -1),  // exclude the message we just sent (backend gets it as question)
      })
      setMessages(p => [...p, {
        role: 'bot',
        text: res.data.answer,
        video: res.data.videos?.[0] || null,
        suggestTicket: res.data.suggest_ticket,
      }])
    } catch {
      setMessages(p => [...p, {
        role: 'bot',
        text: 'Something went wrong. Please create a support ticket.',
        suggestTicket: true
      }])
    }
    setTyping(false)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fff', borderRadius: 'var(--radius-lg)', overflow: 'hidden', border: '1px solid var(--border)' }}>
      {/* Header */}
      <div style={{ background: 'var(--brand)', padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(255,255,255,.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Bot size={17} color="#fff" />
        </div>
        <div>
          <div style={{ color: '#fff', fontWeight: 700, fontSize: 14, fontFamily: 'var(--font-display)' }}>AI Assistant</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }} />
            <span style={{ fontSize: 11, color: 'rgba(255,255,255,.65)' }}>Online</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12, background: 'var(--surface-2)' }}>
        {messages.map((m, i) => {
          const isUser = m.role === 'user'
          const vid = getVideoId(m.video)
          return (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: isUser ? 'flex-end' : 'flex-start' }}>
              <div style={{
                maxWidth: '82%', padding: '10px 14px', borderRadius: isUser ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                background: isUser ? 'var(--brand)' : '#fff',
                color: isUser ? '#fff' : 'var(--text-primary)',
                border: isUser ? 'none' : '1px solid var(--border)',
                fontSize: 14, lineHeight: 1.55,
                boxShadow: '0 1px 3px rgba(0,0,0,.06)'
              }}>
                {isUser ? m.text : renderText(m.text)}
                {vid && (
                  <div style={{ marginTop: 10, border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                    <img src={`https://img.youtube.com/vi/${vid}/0.jpg`} style={{ width: '100%', display: 'block' }} alt="thumbnail" />
                    <a href={m.video} target="_blank" rel="noreferrer" style={{ display: 'block', padding: '8px 12px', fontSize: 13, fontWeight: 600, color: 'var(--accent)', background: '#fff' }}>
                      ▶ Watch on YouTube
                    </a>
                  </div>
                )}
                {m.suggestTicket && (
                  <button onClick={() => navigate('/login')} style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 6, background: 'var(--brand)', color: '#fff', border: 'none', borderRadius: 7, padding: '6px 11px', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                    <Ticket size={13} /> Create a Ticket
                  </button>
                )}
              </div>
            </div>
          )
        })}
        {typing && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '10px 14px', background: '#fff', border: '1px solid var(--border)', borderRadius: '14px 14px 14px 4px', width: 'fit-content' }}>
            {[0, 1, 2].map(n => (
              <span key={n} style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--text-muted)', display: 'inline-block', animation: `bounce 1.1s ${n * .18}s infinite` }} />
            ))}
            <style>{`@keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-6px)} }`}</style>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div style={{ padding: '10px 12px', background: '#fff', borderTop: '1px solid var(--border)', display: 'flex', gap: 8 }}>
        <input
          className="input" value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && ask()}
          placeholder="Ask a question…"
          style={{ flex: 1 }}
        />
        <button onClick={ask} className="btn btn-primary btn-sm" style={{ flexShrink: 0 }}>
          <Send size={14} />
        </button>
      </div>
    </div>
  )
}