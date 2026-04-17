import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, ChevronUp, ArrowLeft, HelpCircle } from 'lucide-react'
import api from '../../api/axios'

export default function PublicFAQ() {
  const [faqs, setFaqs] = useState([])
  const [open, setOpen] = useState(null)
  const [search, setSearch] = useState('')

  useEffect(() => { api.get('/faqs').then(r => setFaqs(r.data || [])).catch(() => {}) }, [])

  const filtered = faqs.filter(f =>
    f.question.toLowerCase().includes(search.toLowerCase()) ||
    f.answer.toLowerCase().includes(search.toLowerCase())
  )

  const grouped = filtered.reduce((acc, f) => {
    const cat = f.category || 'General'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(f)
    return acc
  }, {})

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      <nav style={{ background: '#fff', borderBottom: '1px solid var(--border)', padding: '0 40px', height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Link to="/" style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 18, color: 'var(--brand)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#60a5fa', boxShadow: '0 0 8px #60a5fa', display: 'inline-block' }} />
          SupportSphere
        </Link>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link to="/kb" className="btn btn-secondary btn-sm">Knowledge Base</Link>
          <Link to="/login" className="btn btn-primary btn-sm">Sign in</Link>
        </div>
      </nav>

      <div style={{ maxWidth: 760, margin: '0 auto', padding: '48px 24px' }}>
        <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)', fontSize: 13, marginBottom: 28 }}>
          <ArrowLeft size={14} /> Back
        </Link>

        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ width: 52, height: 52, borderRadius: 16, background: 'var(--brand-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <HelpCircle size={26} color="var(--brand)" />
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 30, fontWeight: 800, marginBottom: 10 }}>Frequently Asked Questions</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 15 }}>Find quick answers to the most common questions.</p>
        </div>

        <input className="input" placeholder="Search questions…" value={search} onChange={e => setSearch(e.target.value)} style={{ marginBottom: 32 }} />

        {Object.keys(grouped).length === 0 && (
          <div className="empty-state"><HelpCircle size={40} /><p>No FAQs found.</p></div>
        )}

        {Object.entries(grouped).map(([cat, items]) => (
          <div key={cat} style={{ marginBottom: 32 }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 12, paddingLeft: 4 }}>{cat}</div>
            <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', boxShadow: 'var(--shadow-sm)' }}>
              {items.map((f, i) => (
                <div key={f.id} style={{ borderTop: i > 0 ? '1px solid var(--border)' : 'none' }}>
                  <button onClick={() => setOpen(open === f.id ? null : f.id)} style={{ width: '100%', background: 'none', border: 'none', padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', textAlign: 'left', gap: 12 }}>
                    <span style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>{f.question}</span>
                    {open === f.id ? <ChevronUp size={17} color="var(--text-muted)" style={{ flexShrink: 0 }} /> : <ChevronDown size={17} color="var(--text-muted)" style={{ flexShrink: 0 }} />}
                  </button>
                  {open === f.id && (
                    <div style={{ padding: '0 20px 18px', color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.7 }}>{f.answer}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
