import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useAuthStore }  from '../stores/authStore'
import { useThemeStore } from '../stores/themeStore'
import { apiGetSupplierActionLog } from '../api/bff'

const NAV_LINKS = [
  { to: '/suppliers',         label: 'My Suppliers'       },
  { to: '/analysis',          label: 'Supplier Analysis'  },
  { to: '/recommendations',   label: 'Recommendations'    },
  { to: '/dashboard',         label: 'Portfolio'          },
  { to: '/audit-log',         label: 'Audit Log'          },
  { to: '/supplier-actions',  label: 'Supplier Actions', badge: true },
]

export default function Layout() {
  const { logout }       = useAuthStore()
  const { dark, toggle } = useThemeStore()
  const navigate         = useNavigate()
  const [unseenActions, setUnseenActions] = useState(0)

  useEffect(() => {
    let cancelled = false
    const poll = async () => {
      try {
        const { data } = await apiGetSupplierActionLog()
        if (!cancelled) setUnseenActions(data.filter(e => !e.admin_seen).length)
      } catch { /* silent */ }
    }
    poll()
    const timer = setInterval(poll, 30000)
    return () => { cancelled = true; clearInterval(timer) }
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-neu-base flex flex-col">

      {/* ── Sticky Navbar ───────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-neu-base shadow-neu-out">
        <div className="max-w-[1280px] mx-auto px-6 h-16 flex items-center gap-6">

          {/* Brand */}
          <NavLink to="/suppliers" className="flex-shrink-0">
            <span className="font-display text-[1.1rem] font-extrabold text-neu-fg tracking-[-1px]">
              Supply<span className="text-neu-accent">Shield</span>
            </span>
          </NavLink>

          {/* Nav links */}
          <nav className="flex items-center gap-1 flex-1 overflow-x-auto">
            {NAV_LINKS.map(({ to, label, badge }) => (
              <NavLink
                key={to}
                to={to}
                onClick={() => { if (badge) setUnseenActions(0) }}
                className={({ isActive }) =>
                  `relative px-3.5 py-1.5 rounded-neu-sm text-[0.78rem] font-semibold whitespace-nowrap
                   transition-all duration-300 ease-out
                   ${isActive
                     ? 'shadow-neu-in text-neu-accent'
                     : 'text-neu-muted hover:-translate-y-px hover:shadow-neu-out-sm hover:text-neu-fg'
                   }`
                }
              >
                {label}
                {badge && unseenActions > 0 && (
                  <span className="absolute -top-1 -right-1 min-w-[1rem] h-4 px-1 rounded-full
                                   bg-neu-accent text-white text-[0.55rem] font-bold flex items-center justify-center">
                    {unseenActions}
                  </span>
                )}
              </NavLink>
            ))}
          </nav>

          {/* Right — theme toggle + profile + logout */}
          <div className="flex items-center gap-2 flex-shrink-0">

            {/* Dark / Light mode toggle */}
            <button
              onClick={toggle}
              title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
              className="neu-card-sm w-9 h-9 flex items-center justify-center text-[1rem]
                         hover:shadow-neu-out transition-all duration-300"
            >
              {dark ? '☀️' : '🌙'}
            </button>

            {/* Company profile shortcut */}
            <NavLink
              to="/onboarding"
              className="neu-card-sm px-3 py-1.5 text-[0.68rem] font-semibold text-neu-muted
                         hover:text-neu-fg transition-all duration-300 hover:shadow-neu-out"
            >
              Profile
            </NavLink>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="neu-card-sm px-3 py-1.5 text-[0.68rem] font-semibold text-neu-muted
                         hover:text-neu-risk-hi transition-all duration-300 hover:shadow-neu-out"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* ── Page Content ────────────────────────────────────────── */}
      <main className="flex-1 max-w-[1280px] w-full mx-auto px-6 py-8">
        <Outlet />
      </main>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <footer className="text-center pb-4 text-[0.65rem] text-[#A0AEC0] tracking-[0.5px]">
        SupplyShield &nbsp;·&nbsp; Microsoft AI Unlocked Hackathon &nbsp;·&nbsp; IIT Roorkee
      </footer>
    </div>
  )
}
