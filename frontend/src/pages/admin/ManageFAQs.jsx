import { useEffect, useState } from 'react'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { Plus, Pencil, Trash2, X } from 'lucide-react'

export default function ManageFAQs() {
  const [faqs, setFaqs] = useState([])
  const [form, setForm] = useState({ question: '', answer: '', category: '' })
  const [editId, setEditId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(false)

  const load = () => api.get('/faqs').then(r => setFaqs(r.data || [])).catch(() => {})
  useEffect(() => { load() }, [])

  const save = async () => {
    if (!form.question || !form.answer) return
    setLoading(true)
    try {
      editId ? await api.put(`/faqs/${editId}`, form) : await api.post('/faqs', form)
      setForm({ question: '', answer: '', category: '' })
      setEditId(null); setShowForm(false); load()
    } catch (err) { alert(err.response?.data?.detail || 'Failed') }
    finally { setLoading(false) }
  }

  const del = async (id) => {
    if (!confirm('Delete FAQ?')) return
    await api.delete(`/faqs/${id}`); load()
  }

  const startEdit = (f) => { setForm({ question: f.question, answer: f.answer, category: f.category || '' }); setEditId(f.id); setShowForm(true) }
  const cancel = () => { setForm({ question: '', answer: '', category: '' }); setEditId(null); setShowForm(false) }

  return (
    <Shell title="Manage FAQs">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div><h1>Manage FAQs</h1><p>{faqs.length} FAQ{faqs.length !== 1 ? 's' : ''} published</p></div>
        <button className="btn btn-primary" onClick={() => { cancel(); setShowForm(true) }}><Plus size={15} /> Add FAQ</button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700 }}>{editId ? 'Edit FAQ' : 'New FAQ'}</h3>
            <button onClick={cancel} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X size={18} /></button>
          </div>
          <div className="field">
            <label>Question</label>
            <input className="input" placeholder="What is…?" value={form.question} onChange={e => setForm({ ...form, question: e.target.value })} />
          </div>
          <div className="field">
            <label>Answer</label>
            <textarea className="input" rows={4} placeholder="The answer is…" value={form.answer} onChange={e => setForm({ ...form, answer: e.target.value })} style={{ resize: 'vertical' }} />
          </div>
          <div className="field">
            <label>Category <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>
            <input className="input" placeholder="e.g. Account, Billing…" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} />
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" onClick={save} disabled={loading}>{loading ? 'Saving…' : editId ? 'Update' : 'Publish FAQ'}</button>
            <button className="btn btn-secondary" onClick={cancel}>Cancel</button>
          </div>
        </div>
      )}

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {faqs.length === 0 ? (
          <div className="empty-state" style={{ padding: 60 }}><p>No FAQs yet. Add your first FAQ above.</p></div>
        ) : (
          <table className="tbl">
            <thead>
              <tr><th>Question</th><th>Category</th><th>Answer preview</th><th style={{ width: 90 }}>Actions</th></tr>
            </thead>
            <tbody>
              {faqs.map(f => (
                <tr key={f.id}>
                  <td style={{ fontWeight: 600, maxWidth: 260 }}>{f.question}</td>
                  <td>{f.category ? <span className="badge" style={{ background: 'var(--brand-light)', color: 'var(--brand)' }}>{f.category}</span> : <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>—</span>}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: 13, maxWidth: 300 }}>{f.answer.slice(0, 90)}{f.answer.length > 90 ? '…' : ''}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => startEdit(f)} style={{ padding: '5px 9px' }}><Pencil size={14} /></button>
                      <button className="btn btn-danger btn-sm" onClick={() => del(f.id)} style={{ padding: '5px 9px' }}><Trash2 size={14} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Shell>
  )
}
