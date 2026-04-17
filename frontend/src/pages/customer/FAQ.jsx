import { useEffect, useState } from 'react'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { ChevronDown, ChevronUp, HelpCircle } from 'lucide-react'

export default function CustomerFAQ() {
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
    <Shell title="FAQs">
      <div className="page-header"><h1>FAQs</h1><p>Frequently asked questions</p></div>

      <div style={{ maxWidth: 720 }}>
        <input className="input" placeholder="Search questions…" value={search} onChange={e => setSearch(e.target.value)} style={{ marginBottom: 28 }} />

        {Object.keys(grouped).length === 0 && (
          <div className="card empty-state"><HelpCircle size={36} /><p style={{ marginTop: 10 }}>No FAQs found.</p></div>
        )}

        {Object.entries(grouped).map(([cat, items]) => (
          <div key={cat} style={{ marginBottom: 28 }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10 }}>{cat}</div>
            <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              {items.map((f, i) => (
                <div key={f.id} style={{ borderTop: i > 0 ? '1px solid var(--border)' : 'none' }}>
                  <button onClick={() => setOpen(open === f.id ? null : f.id)} style={{ width: '100%', background: 'none', border: 'none', padding: '15px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', textAlign: 'left', gap: 12 }}>
                    <span style={{ fontWeight: 600, fontSize: 14 }}>{f.question}</span>
                    {open === f.id ? <ChevronUp size={16} color="var(--text-muted)" /> : <ChevronDown size={16} color="var(--text-muted)" />}
                  </button>
                  {open === f.id && (
                    <div style={{ padding: '0 18px 16px', color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.7 }}>{f.answer}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Shell>
  )
}
