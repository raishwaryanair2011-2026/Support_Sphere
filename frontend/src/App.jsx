import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'

import Home from './pages/public/Home'
import PublicFAQ from './pages/public/PublicFAQ'
import PublicKB from './pages/public/PublicKB'
import Login from './pages/Login'
import Register from './pages/Register'

import AdminDashboard from './pages/admin/AdminDashboard'
import ManageAgents from './pages/admin/ManageAgents'
import ManageCustomers from './pages/admin/ManageCustomers'
import ManageFAQs from './pages/admin/ManageFAQs'
import ManageKnowledgeBase from './pages/admin/ManageKnowledgeBase'
import Reports from './pages/admin/Reports'

import AgentDashboard from './pages/agent/AgentDashboard'
import AssignedTickets from './pages/agent/AssignedTickets'
import AgentTicketDetail from './pages/agent/TicketDetail'
import AgentChangePassword from './pages/agent/ChangePassword'

import CustomerTickets from './pages/customer/Tickets'
import CreateTicket from './pages/customer/CreateTicket'
import CustomerTicketDetail from './pages/customer/TicketDetail'
import CustomerFAQ from './pages/customer/FAQ'
import CustomerKB from './pages/customer/KnowledgeBase'
import CustomerChangePassword from './pages/agent/ChangePassword'

const P = ({ role, children }) => <ProtectedRoute role={role}>{children}</ProtectedRoute>

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/faq" element={<PublicFAQ />} />
          <Route path="/kb" element={<PublicKB />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/admin" element={<P role="admin"><AdminDashboard /></P>} />
          <Route path="/admin/agents" element={<P role="admin"><ManageAgents /></P>} />
          <Route path="/admin/customers" element={<P role="admin"><ManageCustomers /></P>} />
          <Route path="/admin/faqs" element={<P role="admin"><ManageFAQs /></P>} />
          <Route path="/admin/kb" element={<P role="admin"><ManageKnowledgeBase /></P>} />
          <Route path="/admin/reports" element={<P role="admin"><Reports /></P>} />

          <Route path="/agent" element={<P role="agent"><AgentDashboard /></P>} />
          <Route path="/agent/tickets" element={<P role="agent"><AssignedTickets /></P>} />
          <Route path="/agent/tickets/:id" element={<P role="agent"><AgentTicketDetail /></P>} />
          <Route path="/agent/password" element={<P role="agent"><AgentChangePassword /></P>} />

          <Route path="/customer" element={<P role="customer"><CustomerTickets /></P>} />
          <Route path="/customer/create" element={<P role="customer"><CreateTicket /></P>} />
          <Route path="/customer/tickets/:id" element={<P role="customer"><CustomerTicketDetail /></P>} />
          <Route path="/customer/faqs" element={<P role="customer"><CustomerFAQ /></P>} />
          <Route path="/customer/kb" element={<P role="customer"><CustomerKB /></P>} />
          <Route path="/customer/password" element={<P role="customer"><CustomerChangePassword /></P>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}