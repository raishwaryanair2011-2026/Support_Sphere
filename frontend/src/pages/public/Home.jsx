import { Link } from 'react-router-dom'
import KBChat from '../../components/KBChat'
import { Bot, HelpCircle, BookOpen, Ticket, ArrowRight, Zap, Target, Lightbulb, Library } from 'lucide-react'

export default function Home() {
  return (
    <div style={{ minHeight: '100vh', background: '#f4f6fb', fontFamily: 'var(--font-body)' }}>
      {/* ── Navbar ── */}
      <nav style={{ background: '#fff', borderBottom: '1px solid var(--border)', padding: '0 40px', height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 100 }}>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 18, color: 'var(--brand)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#60a5fa', boxShadow: '0 0 8px #60a5fa' }} />
          SupportSphere
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Link to="/faq" style={{ padding: '7px 14px', borderRadius: 'var(--radius)', fontSize: 14, fontWeight: 500, color: 'var(--text-secondary)' }}>FAQs</Link>
          <Link to="/kb" style={{ padding: '7px 14px', borderRadius: 'var(--radius)', fontSize: 14, fontWeight: 500, color: 'var(--text-secondary)' }}>Knowledge Base</Link>
          <Link to="/login" className="btn btn-primary btn-sm">Sign in</Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section style={{ maxWidth: 1180, margin: '0 auto', padding: '64px 40px 40px', display: 'flex', gap: 60, alignItems: 'flex-start' }}>
        {/* Left */}
        <div style={{ flex: 1, paddingTop: 12 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, background: 'var(--accent-soft)', color: 'var(--accent)', borderRadius: 99, padding: '5px 13px', fontSize: 12, fontWeight: 700, marginBottom: 20, letterSpacing: '.03em' }}>
            <Zap size={12} /> AI-Powered Support
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(32px, 4vw, 46px)', fontWeight: 800, lineHeight: 1.15, color: 'var(--text-primary)', marginBottom: 18 }}>
            How can we<br />
            <span style={{ color: 'var(--brand)' }}>help you today?</span>
          </h1>
          <p style={{ fontSize: 17, color: 'var(--text-secondary)', lineHeight: 1.7, maxWidth: 500, marginBottom: 36 }}>
            Instant AI answers, a smart knowledge base, and human support — all in one place.
          </p>
          <div style={{ display: 'flex', gap: 10 }}>
            <Link to="/login" className="btn btn-primary" style={{ fontSize: 15, padding: '11px 22px' }}>
              Get Support <ArrowRight size={15} />
            </Link>
            <Link to="/kb" className="btn btn-secondary" style={{ fontSize: 15, padding: '11px 22px' }}>Browse Articles</Link>
          </div>

          {/* Pills */}
          <div style={{ display: 'flex', gap: 10, marginTop: 36, flexWrap: 'wrap' }}>
            {['⚡ Instant AI Answers', '📘 Smart Knowledge Base', '🎫 Ticket Support'].map(t => (
              <div key={t} style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 99, padding: '6px 14px', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', boxShadow: 'var(--shadow-sm)' }}>{t}</div>
            ))}
          </div>
        </div>

        {/* Chat card */}
        <div style={{ width: 420, flexShrink: 0, height: 500, boxShadow: 'var(--shadow-lg)', borderRadius: 'var(--radius-xl)', overflow: 'hidden', border: '1px solid var(--border)' }}>
          <KBChat />
        </div>
      </section>

      {/* ── Steps ── */}
      <section style={{ maxWidth: 1180, margin: '0 auto', padding: '20px 40px 60px' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, textAlign: 'center', marginBottom: 32 }}>Choose how to get help</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
          {[
            { icon: HelpCircle, step: '01', title: 'Check FAQs', desc: 'Quick answers to the most common questions.', link: '/faq', cta: 'View FAQs', color: '#eff6ff' },
            { icon: BookOpen,   step: '02', title: 'Search Knowledge Base', desc: 'Browse guides and in-depth documentation.', link: '/kb', cta: 'Open KB', color: '#f0fdf4' },
            { icon: Ticket,     step: '03', title: 'Raise a Ticket', desc: 'Connect directly with our support team.', link: '/login', cta: 'Create Ticket', color: '#fdf4ff' },
          ].map(({ icon: Icon, step, title, desc, link, cta, color }) => (
            <div key={step} style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius-xl)', padding: 28, boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
                <div style={{ width: 46, height: 46, borderRadius: 14, background: color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={22} color="var(--brand)" />
                </div>
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 800, color: 'var(--border)', lineHeight: 1 }}>{step}</span>
              </div>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, fontWeight: 700, marginBottom: 8 }}>{title}</h3>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 20, lineHeight: 1.6 }}>{desc}</p>
              <Link to={link} className="btn btn-primary btn-sm">{cta} <ArrowRight size={13} /></Link>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section style={{ background: '#fff', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)', padding: '60px 40px' }}>
        <div style={{ maxWidth: 1180, margin: '0 auto' }}>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, textAlign: 'center', marginBottom: 48 }}>What makes SupportSphere different?</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '40px 80px', maxWidth: 880, margin: '0 auto' }}>
            {[
              { icon: Bot,       title: 'AI Knowledge Assistant', desc: 'Get instant answers from our intelligent AI assistant trained on support articles and documentation.' },
              { icon: Target,    title: 'Smart Ticket Routing',   desc: 'Automatically routes tickets to the right team member for faster, more accurate resolution.' },
              { icon: Lightbulb, title: 'Automated Suggestions',  desc: 'Receive personalised FAQ recommendations based on your query in real-time.' },
              { icon: Library,   title: 'Guided Knowledge Base',  desc: 'Step-by-step guides and documentation to help you resolve issues independently.' },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} style={{ display: 'flex', gap: 18 }}>
                <div style={{ width: 42, height: 42, borderRadius: 12, background: 'var(--brand-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Icon size={20} color="var(--brand)" />
                </div>
                <div>
                  <h4 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: 6, fontSize: 15 }}>{title}</h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.65 }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{ padding: '28px 40px', textAlign: 'center', fontSize: 13, color: 'var(--text-muted)' }}>
        © {new Date().getFullYear()} SupportSphere. All rights reserved.
      </footer>
    </div>
  )
}
