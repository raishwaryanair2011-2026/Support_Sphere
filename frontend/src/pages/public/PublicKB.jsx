import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, BookOpen } from 'lucide-react'
import KBChat from '../../components/KBChat'
import api from '../../api/axios'

export default function PublicKB() {
  const [articles, setArticles] = useState([])

  useEffect(() => { api.get('/kb/articles').then(r => setArticles(r.data || [])).catch(() => {}) }, [])

  const grouped = articles.reduce((acc, a) => {
    const cat = a.category || 'General'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(a)
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
          <Link to="/faq" className="btn btn-secondary btn-sm">FAQs</Link>
          <Link to="/login" className="btn btn-primary btn-sm">Sign in</Link>
        </div>
      </nav>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '48px 24px' }}>
        <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)', fontSize: 13, marginBottom: 28 }}>
          <ArrowLeft size={14} /> Back
        </Link>

        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 30, fontWeight: 800, marginBottom: 10 }}>Knowledge Base</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 15 }}>Browse articles or ask the AI assistant below.</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 28, alignItems: 'flex-start' }}>
          {/* Articles */}
          <div>
            {Object.keys(grouped).length === 0 && (
              <div className="card empty-state"><BookOpen size={36} /><p style={{ marginTop: 10 }}>No articles published yet.</p></div>
            )}
            {Object.entries(grouped).map(([cat, items]) => (
              <div key={cat} style={{ marginBottom: 28 }}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10, paddingLeft: 2 }}>{cat}</div>
                {items.map(a => (
                  <div key={a.id} className="card" style={{ marginBottom: 12, padding: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                      <div style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--brand-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        <BookOpen size={17} color="var(--brand)" />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 5, fontFamily: 'var(--font-display)' }}>{a.title}</div>
                        {a.content && <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{a.content.slice(0, 160)}{a.content.length > 160 ? '…' : ''}</p>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>

          {/* Chat */}
          <div style={{ height: 520, position: 'sticky', top: 80 }}>
            <KBChat />
          </div>
        </div>
      </div>
    </div>
  )
}
