import { useEffect, useState } from 'react'
import Shell from '../../components/Shell'
import api from '../../api/axios'
import { Pencil, Trash2, X, Check, Users } from 'lucide-react'

export default function ManageCustomers() {
  const [customers, setCustomers] = useState([])
  const [editId, setEditId] = useState(null)
  const [editForm, setEditForm] = useState({ name: '', email: '' })
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')

  const load = () =>
    api.get('/users/customers').then(r => setCustomers(r.data || [])).catch(() => {})

  useEffect(() => { load() }, [])

  const startEdit = (c) => {
    setEditId(c.id)
    setEditForm({ name: c.name || '', email: c.email })
  }

  const cancelEdit = () => setEditId(null)

  const saveEdit = async (id) => {
    setLoading(true)
    try {
      await api.put(`/users/customers/${id}`, editForm)
      setEditId(null)
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Update failed')
    } finally { setLoading(false) }
  }

  const del = async (id) => {
    if (!confirm('Delete this customer? Their tickets will also be deleted.')) return
    await api.delete(`/users/customers/${id}`)
    load()
  }

  const toggle = async (c) => {
    await api.put(`/users/customers/${c.id}`, { is_active: !c.is_active })
    load()
  }

  const filtered = customers.filter(c =>
    (c.name || '').toLowerCase().includes(search.toLowerCase()) ||
    c.email.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <Shell title="Manage Customers">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1>Manage Customers</h1>
          <p>{customers.length} registered customer{customers.length !== 1 ? 's' : ''}</p>
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <input
          className="input"
          placeholder="Search by name or email…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {filtered.length === 0 ? (
          <div className="empty-state" style={{ padding: 60 }}>
            <Users size={36} />
            <p style={{ marginTop: 12 }}>No customers found.</p>
          </div>
        ) : (
          <table className="tbl">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Status</th>
                <th style={{ width: 140 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(c => {
                const isEditing = editId === c.id
                return (
                  <tr key={c.id}>
                    <td>
                      {isEditing ? (
                        <input
                          className="input"
                          value={editForm.name}
                          onChange={e => setEditForm({ ...editForm, name: e.target.value })}
                          style={{ padding: '6px 10px', fontSize: 13 }}
                          placeholder="Full name"
                        />
                      ) : (
                        <span style={{ fontWeight: 500 }}>{c.name || <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No name</span>}</span>
                      )}
                    </td>
                    <td>
                      {isEditing ? (
                        <input
                          className="input"
                          type="email"
                          value={editForm.email}
                          onChange={e => setEditForm({ ...editForm, email: e.target.value })}
                          style={{ padding: '6px 10px', fontSize: 13 }}
                        />
                      ) : (
                        <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{c.email}</span>
                      )}
                    </td>
                    <td>
                      <span
                        className={`badge badge-${c.is_active ? 'resolved' : 'closed'}`}
                        style={{ cursor: 'pointer' }}
                        onClick={() => toggle(c)}
                        title="Click to toggle"
                      >
                        {c.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        {isEditing ? (
                          <>
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => saveEdit(c.id)}
                              disabled={loading}
                              style={{ padding: '5px 9px' }}
                            >
                              <Check size={14} />
                            </button>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={cancelEdit}
                              style={{ padding: '5px 9px' }}
                            >
                              <X size={14} />
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => startEdit(c)}
                              style={{ padding: '5px 9px' }}
                              title="Edit"
                            >
                              <Pencil size={14} />
                            </button>
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => del(c.id)}
                              style={{ padding: '5px 9px' }}
                              title="Delete"
                            >
                              <Trash2 size={14} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </Shell>
  )
}