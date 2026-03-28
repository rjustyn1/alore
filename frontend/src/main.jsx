import { StrictMode, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './App.css'
import SGDashboard from './SGDashboard.jsx'
import ScenarioPage from './ScenarioPage.jsx'
import SentryPage from './SentryPage.jsx'
import DebateHistoryPage from './DebateHistoryPage.jsx'

const NAV_ITEMS = [
  {
    id: 'dashboard',
    label: 'Home',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M3 9.5L10 3l7 6.5V17a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" fill="none"/>
        <path d="M7.5 18V13h5v5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
  },
  {
    id: 'scenario',
    label: 'Scenarios',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M11 2L3 11h7l-1 7 8-9h-7l1-7z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
      </svg>
    ),
  },
  {
    id: 'sentry',
    label: 'Sentry',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="3" stroke="currentColor" strokeWidth="1.6"/>
        <path d="M10 1v2M10 17v2M1 10h2M17 10h2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
        <path d="M3.5 3.5l1.4 1.4M15.1 15.1l1.4 1.4M3.5 16.5l1.4-1.4M15.1 4.9l1.4-1.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    ),
  },
  {
    id: 'history',
    label: 'Debate History',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" strokeWidth="1.6" fill="none"/>
        <path d="M10 6v4.5l3 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
  },
]

function Sidebar({ page, setPage }) {
  return (
    <div
      style={{
        width: 56,
        flexShrink: 0,
        height: '100vh',
        background: '#FDFCFA',
        borderRight: '1px solid rgba(45,58,82,0.1)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 14,
        gap: 4,
        zIndex: 100,
      }}
    >
      {/* Alore logomark */}
      <svg viewBox="0 0 52 28" width="30" height="16" fill="none" style={{ marginBottom: 14 }}>
        <path d="M 5 23 C 10 23 17 17 24 12 C 28 9 31 8 30 10 C 27 13 20 17 12 20 Z" fill="#C9B89A" />
        <path d="M 5 23 C 8 21 15 15 23 10 C 29 6 38 3 40 5 C 36 4 29 7 23 12 C 15 17 9 21 5 23 Z" fill="#2D3A52" />
        <circle cx="41.5" cy="4.5" r="3.2" fill="#2D3A52" />
      </svg>

      {NAV_ITEMS.map((item) => {
        const active = page === item.id
        return (
          <button
            key={item.id}
            title={item.label}
            onClick={() => setPage(item.id)}
            style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              border: active
                ? '1px solid rgba(45,58,82,0.18)'
                : '1px solid transparent',
              background: active ? 'rgba(45,58,82,0.08)' : 'transparent',
              color: active ? '#2D3A52' : 'rgba(45,58,82,0.38)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'background 0.15s, color 0.15s, border-color 0.15s',
            }}
            onMouseEnter={(e) => {
              if (!active) {
                e.currentTarget.style.background = 'rgba(45,58,82,0.05)'
                e.currentTarget.style.color = 'rgba(45,58,82,0.65)'
              }
            }}
            onMouseLeave={(e) => {
              if (!active) {
                e.currentTarget.style.background = 'transparent'
                e.currentTarget.style.color = 'rgba(45,58,82,0.38)'
              }
            }}
          >
            {item.icon}
          </button>
        )
      })}

      <div style={{ flex: 1 }} />
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: 8,
          background: 'rgba(45,58,82,0.06)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: 14,
        }}
        title="Singapore"
      >
        <span style={{ fontSize: 14 }}>🇸🇬</span>
      </div>
    </div>
  )
}

function App() {
  const [page, setPage] = useState('dashboard')
  return (
    <div style={{ display: 'flex', flexDirection: 'row', height: '100vh' }}>
      <Sidebar page={page} setPage={setPage} />
      <div style={{ flex: 1, minWidth: 0, height: '100vh', overflowY: 'auto', overflowX: 'hidden' }}>
        {page === 'dashboard'
          ? <SGDashboard onNavigate={setPage} />
          : page === 'scenario'
          ? <ScenarioPage onNavigate={setPage} />
          : page === 'sentry'
          ? <SentryPage onNavigate={setPage} />
          : <DebateHistoryPage onNavigate={setPage} />
        }
      </div>
    </div>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)
