import { NavLink, useLocation } from 'react-router-dom'
import { Upload, Users, ShieldCheck, FileText, Activity } from 'lucide-react'
import Header from './Header'

const navItems = [
  { path: '/', label: 'Upload', icon: Upload },
  { path: '/documents', label: 'Documents', icon: FileText },
  { path: '/crm', label: 'CRM Fournisseurs', icon: Users },
  { path: '/conformity', label: 'Conformité', icon: ShieldCheck },
]

export default function Layout({ children }) {
  const location = useLocation()

  const pageTitles = {
    '/': 'Upload de documents',
    '/crm': 'CRM Fournisseurs',
    '/conformity': 'Dashboard Conformité',
  }

  return (
    <>
      {/* Sidebar */}
      <aside style={{
        width: 240,
        position: 'fixed',
        top: 0,
        left: 0,
        height: '100vh',
        background: '#1B2A4A',
        color: 'white',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 100,
      }}>
        {/* Logo */}
        <div style={{
          padding: '24px 20px',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}>
            <div style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: '#00C896',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <FileText size={20} color="white" />
            </div>
            <span style={{
              fontFamily: 'Space Grotesk, sans-serif',
              fontSize: '1.3rem',
              fontWeight: 700,
            }}>DocuFlow</span>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '16px 0' }}>
          {navItems.map(({ path, label, icon: Icon }) => {
            const isActive = location.pathname === path
            return (
              <NavLink
                key={path}
                to={path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '12px 20px',
                  color: isActive ? '#00C896' : 'rgba(255,255,255,0.7)',
                  background: isActive ? 'rgba(0,200,150,0.1)' : 'transparent',
                  borderLeft: isActive ? '3px solid #00C896' : '3px solid transparent',
                  fontSize: 14,
                  fontWeight: isActive ? 600 : 400,
                  textDecoration: 'none',
                  transition: 'all 0.2s',
                }}
              >
                <Icon size={18} />
                {label}
              </NavLink>
            )
          })}
        </nav>

        {/* Status */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          fontSize: 12,
          color: 'rgba(255,255,255,0.5)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Activity size={14} />
            <span>v1.0.0 — Hackathon 2026</span>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="main-content">
        <Header title={pageTitles[location.pathname] || 'DocuFlow'} />
        <div className="page-container">
          {children}
        </div>
      </div>
    </>
  )
}
