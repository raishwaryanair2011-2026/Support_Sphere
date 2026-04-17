import { useEffect, useState } from 'react'
import Shell from '../../components/Shell'
import KBChat from '../../components/KBChat'
import api from '../../api/axios'
import { BookOpen } from 'lucide-react'

export default function CustomerKB() {
  const [articles, setArticles] = useState([])

  useEffect(() => { api.get('/kb/articles').then(r => setArticles(r.data || [])).catch(() => {}) }, [])

  const grouped = articles.reduce((acc, a) => {
    const cat = a.category || 'General'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(a)
    return acc
  }, {})

  return (
    <Shell title="Knowledge Base">
      <div className="page-header"><h1>Knowledge Base</h1><p>Browse articles or ask the AI assistant</p></div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 24, alignItems: 'flex-start' }}>
        <div>
          {Object.keys(grouped).length === 0 && (
            <div className="card empty-state"><BookOpen size={36} /><p style={{ marginTop: 10 }}>No articles yet.</p></div>
          )}
          {Object.entries(grouped).map(([cat, items]) => (
            <div key={cat} style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10 }}>{cat}</div>
              {items.map(a => (
                <div key={a.id} className="card" style={{ marginBottom: 10, padding: 18 }}>
                  <div style={{ display: 'flex', gap: 14 }}>
                    <div style={{ width: 34, height: 34, borderRadius: 9, background: 'var(--brand-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <BookOpen size={16} color="var(--brand)" />
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 4, fontFamily: 'var(--font-display)' }}>{a.title}</div>
                      {a.content && <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{a.content.slice(0, 140)}{a.content.length > 140 ? '…' : ''}</p>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>

        <div style={{ height: 500, position: 'sticky', top: 80 }}>
          <KBChat />
        </div>
      </div>
    </Shell>
  )
}
