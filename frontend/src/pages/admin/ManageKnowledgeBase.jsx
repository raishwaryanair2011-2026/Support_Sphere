import { useEffect, useState } from 'react'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { Upload, Trash2, BookOpen, CheckCircle, Clock, X } from 'lucide-react'

export default function ManageKnowledgeBase() {
  const [docs, setDocs] = useState([])
  const [form, setForm] = useState({ title: '', category: '', file: null })
  const [loading, setLoading] = useState(false)

  const load = () => api.get('/kb/documents').then(r => setDocs(r.data || [])).catch(() => {})
  useEffect(() => { load() }, [])

  const upload = async () => {
    if (!form.title || !form.file) { alert('Title and file required'); return }
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('title', form.title)
      if (form.category) fd.append('category', form.category)
      fd.append('file', form.file)
      await api.post('/kb/documents', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setForm({ title: '', category: '', file: null })
      setTimeout(load, 800)
    } catch (err) { alert(err.response?.data?.detail || 'Upload failed') }
    finally { setLoading(false) }
  }

  const del = async (id) => {
    if (!confirm('Delete this document?')) return
    await api.delete(`/kb/documents/${id}`); load()
  }

  const statusIcon = (s) => {
    if (s === 'Indexed') return <CheckCircle size={14} color="var(--success)" />
    if (s === 'Processing') return <Clock size={14} color="var(--warning)" />
    return <X size={14} color="var(--danger)" />
  }

  return (
    <Shell title="Knowledge Base">
      <div className="page-header">
        <h1>Knowledge Base</h1>
        <p>Upload and manage documents for the AI assistant</p>
      </div>

      {/* Upload card */}
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, marginBottom: 18 }}>Upload New Document</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
          <div className="field" style={{ margin: 0 }}>
            <label>Title</label>
            <input className="input" placeholder="Password Reset Guide" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
          </div>
          <div className="field" style={{ margin: 0 }}>
            <label>Category <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>
            <input className="input" placeholder="IT, HR, Facilities…" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} />
          </div>
        </div>

        <div style={{ border: '2px dashed var(--border)', borderRadius: 'var(--radius-lg)', padding: 24, textAlign: 'center', marginBottom: 16, background: form.file ? '#f0fdf4' : 'var(--surface-2)' }}>
          {form.file ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
              <CheckCircle size={18} color="var(--success)" />
              <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--success)' }}>{form.file.name}</span>
              <button onClick={() => setForm({ ...form, file: null })} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X size={16} /></button>
            </div>
          ) : (
            <>
              <Upload size={24} color="var(--text-muted)" style={{ marginBottom: 8 }} />
              <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 10 }}>PDF or TXT files supported</p>
              <label className="btn btn-secondary btn-sm" style={{ cursor: 'pointer' }}>
                Choose File
                <input type="file" accept=".pdf,.txt" style={{ display: 'none' }} onChange={e => setForm({ ...form, file: e.target.files[0] })} />
              </label>
            </>
          )}
        </div>

        <button className="btn btn-primary" onClick={upload} disabled={loading}>
          <Upload size={15} /> {loading ? 'Uploading…' : 'Upload & Index'}
        </button>
      </div>

      {/* Documents list */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 15 }}>
          Indexed Documents ({docs.length})
        </div>
        {docs.length === 0 ? (
          <div className="empty-state" style={{ padding: 60 }}><BookOpen size={36} /><p style={{ marginTop: 12 }}>No documents yet.</p></div>
        ) : (
          <table className="tbl">
            <thead>
              <tr><th>Title</th><th>Category</th><th>Type</th><th>Chunks</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {docs.map(d => (
                <tr key={d.id}>
                  <td style={{ fontWeight: 600 }}>{d.title}</td>
                  <td>{d.category ? <span className="badge" style={{ background: 'var(--brand-light)', color: 'var(--brand)' }}>{d.category}</span> : <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>—</span>}</td>
                  <td><span style={{ textTransform: 'uppercase', fontSize: 12, fontWeight: 700, color: 'var(--text-muted)' }}>{d.file_type}</span></td>
                  <td style={{ color: 'var(--text-secondary)' }}>{d.chunk_count}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                      {statusIcon(d.status)} {d.status}
                    </div>
                  </td>
                  <td>
                    <button className="btn btn-danger btn-sm" onClick={() => del(d.id)} style={{ padding: '5px 9px' }}><Trash2 size={14} /></button>
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
