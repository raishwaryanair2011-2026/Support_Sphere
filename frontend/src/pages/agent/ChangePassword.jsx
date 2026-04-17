import { useState } from 'react'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { CheckCircle, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../../auth/AuthContext'

export default function ChangePassword() {
  const { user } = useAuth()
  const [form, setForm] = useState({ current_password: '', new_password: '', confirm: '' })
  const [show, setShow] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  const submit = async () => {
    setError('')
    if (form.new_password.length < 8) { setError('New password must be at least 8 characters'); return }
    if (form.new_password !== form.confirm) { setError('Passwords do not match'); return }
    if (form.new_password === form.current_password) { setError('New password must be different from your current password'); return }

    setLoading(true)
    try {
      await api.post('/auth/change-password', {
        current_password: form.current_password,
        new_password: form.new_password,
      })
      setDone(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to change password. Check your current password is correct.')
    } finally { setLoading(false) }
  }

  if (done) return (
    <Shell title="Change Password">
      <div style={{ maxWidth: 480, margin: '60px auto', textAlign: 'center' }}>
        <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--success-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
          <CheckCircle size={32} color="var(--success)" />
        </div>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Password changed!</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 15 }}>Your new password is active. Use it next time you log in.</p>
      </div>
    </Shell>
  )

  return (
    <Shell title="Change Password">
      <div style={{ maxWidth: 480 }}>
        <div className="page-header">
          <h1>Change Password</h1>
          <p>Signed in as {user?.name || user?.email}</p>
        </div>

        <div className="card">
          {error && (
            <div style={{ background: 'var(--danger-bg)', color: 'var(--danger)', border: '1px solid #fca5a5', borderRadius: 'var(--radius)', padding: '10px 14px', fontSize: 13, marginBottom: 18 }}>
              {error}
            </div>
          )}

          <div className="field">
            <label>Current password</label>
            <div style={{ position: 'relative' }}>
              <input
                className="input"
                type={show ? 'text' : 'password'}
                placeholder="Your current password"
                value={form.current_password}
                onChange={e => setForm({ ...form, current_password: e.target.value })}
                style={{ paddingRight: 42 }}
              />
              <button type="button" onClick={() => setShow(!show)} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex' }}>
                {show ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div className="field">
            <label>New password</label>
            <input
              className="input"
              type={show ? 'text' : 'password'}
              placeholder="Min. 8 characters"
              value={form.new_password}
              onChange={e => setForm({ ...form, new_password: e.target.value })}
            />
          </div>

          <div className="field" style={{ marginBottom: 24 }}>
            <label>Confirm new password</label>
            <input
              className="input"
              type={show ? 'text' : 'password'}
              placeholder="Repeat new password"
              value={form.confirm}
              onChange={e => setForm({ ...form, confirm: e.target.value })}
            />
          </div>

          <button
            className="btn btn-primary"
            onClick={submit}
            disabled={loading}
            style={{ width: '100%', justifyContent: 'center', padding: 11, fontSize: 15 }}
          >
            {loading ? 'Changing…' : 'Change Password'}
          </button>
        </div>
      </div>
    </Shell>
  )
}