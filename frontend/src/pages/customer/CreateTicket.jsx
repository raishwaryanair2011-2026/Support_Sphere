import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { Ticket, Upload, CheckCircle } from 'lucide-react'

export default function CreateTicket() {
  const navigate = useNavigate()
  const [subject, setSubject] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const submit = async () => {
    if (!subject.trim() || !description.trim()) { setError('Please fill in both subject and description.'); return }
    setError(''); setLoading(true)
    try {
      const res = await api.post('/tickets', { subject, description })
      if (file) {
        const fd = new FormData(); fd.append('file', file)
        await api.post(`/tickets/${res.data.id}/attachments`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      }
      setDone(true)
      setTimeout(() => navigate('/customer'), 2500)
    } catch (err) { setError(err.response?.data?.detail || 'Submission failed') }
    finally { setLoading(false) }
  }

  if (done) return (
    <Shell title="New Ticket">
      <div style={{ maxWidth: 480, margin: '60px auto', textAlign: 'center' }}>
        <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--success-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
          <CheckCircle size={32} color="var(--success)" />
        </div>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Ticket Submitted!</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 15 }}>Your ticket has been created and assigned. Redirecting…</p>
      </div>
    </Shell>
  )

  return (
    <Shell title="New Ticket">
      <div style={{ maxWidth: 680 }}>
        <div className="page-header"><h1>Create a Support Ticket</h1><p>Describe your issue and our team will get back to you shortly.</p></div>

        <div className="card">
          {error && <div style={{ background: 'var(--danger-bg)', color: 'var(--danger)', border: '1px solid #fca5a5', borderRadius: 'var(--radius)', padding: '10px 14px', fontSize: 14, marginBottom: 18 }}>{error}</div>}

          <div className="field">
            <label>Subject</label>
            <input className="input" placeholder="Brief summary of the issue" value={subject} onChange={e => setSubject(e.target.value)} />
          </div>

          <div className="field">
            <label>Description</label>
            <textarea className="input" rows={5} placeholder="Describe your issue in detail — what happened, when, and what you've already tried…" value={description} onChange={e => setDescription(e.target.value)} style={{ resize: 'vertical' }} />
          </div>

          <div className="field" style={{ marginBottom: 24 }}>
            <label>Attachment <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional — PDF or TXT)</span></label>
            <div style={{ border: '2px dashed var(--border)', borderRadius: 'var(--radius-lg)', padding: 20, textAlign: 'center', background: file ? '#f0fdf4' : 'var(--surface-2)' }}>
              {file ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                  <CheckCircle size={16} color="var(--success)" />
                  <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--success)' }}>{file.name}</span>
                  <button onClick={() => setFile(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex' }}>×</button>
                </div>
              ) : (
                <>
                  <Upload size={20} color="var(--text-muted)" style={{ marginBottom: 8 }} />
                  <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 10 }}>Attach a PDF or TXT for AI-powered summary</p>
                  <label className="btn btn-secondary btn-sm" style={{ cursor: 'pointer' }}>
                    Choose File
                    <input type="file" accept=".pdf,.txt" style={{ display: 'none' }} onChange={e => setFile(e.target.files[0])} />
                  </label>
                </>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" onClick={submit} disabled={loading} style={{ padding: '10px 24px', fontSize: 15 }}>
              <Ticket size={15} /> {loading ? 'Submitting…' : 'Submit Ticket'}
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/customer')}>Cancel</button>
          </div>
        </div>
      </div>
    </Shell>
  )
}
