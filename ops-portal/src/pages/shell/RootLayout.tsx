import { Suspense, useState } from 'react';
import { Outlet, NavLink, Navigate, useNavigate, useLocation } from 'react-router';
import { useSession } from '@/hooks/useSession';
import { useConnectivity } from '@/hooks/useConnectivity';
import { useSettings } from '@/hooks/useSettings';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: 'D' },
  { to: '/time-travel', label: 'Time-Travel', icon: 'T' },
  { to: '/config/revisions', label: 'Config', icon: 'C' },
  { to: '/deploy/jobs', label: 'Deploy', icon: 'J' },
  { to: '/audit', label: 'Audit', icon: 'A' },
  { to: '/drift', label: 'Drift', icon: 'R' },
  { to: '/settings', label: 'Settings', icon: 'S' },
] as const;

function TopBar({ onToggleMenu }: { onToggleMenu: () => void }) {
  const { operator, logout } = useSession();
  const navigate = useNavigate();

  return (
    <header className="flex items-center justify-between px-4 py-2 bg-surface-inverse text-text-inverse border-b border-border-default h-14">
      <div className="flex items-center gap-4">
        <button type="button" onClick={onToggleMenu} className="xl:hidden p-1 rounded hover:bg-white/10"
          aria-label="Toggle navigation">
          <span className="text-lg">&#9776;</span>
        </button>
        <span className="font-bold text-lg tracking-tight">Ops Portal</span>
        <div id="global-search-slot" />
      </div>
      <div className="flex items-center gap-4">
        <div id="notification-badge-slot" />
        {operator && (
          <div className="flex items-center gap-3">
            <span className="text-sm">
              {operator.name} <span className="text-text-muted text-xs">({operator.role})</span>
            </span>
            <button
              type="button"
              onClick={() => { logout(); navigate('/login'); }}
              className="text-sm px-3 py-1 rounded bg-white/10 hover:bg-white/20"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

function NavBar({ collapsed, mobileOpen, onClose }: { collapsed: boolean; mobileOpen: boolean; onClose: () => void }) {
  const widthClass = collapsed ? 'w-14' : 'w-48';
  const mobileClass = mobileOpen
    ? 'fixed inset-y-14 left-0 z-30 w-48 shadow-lg'
    : 'hidden xl:flex';

  return (
    <>
      {mobileOpen && (
        <div className="fixed inset-0 z-20 bg-black/30 xl:hidden" onClick={onClose} aria-hidden="true" />
      )}
      <nav className={`${mobileClass} xl:relative ${widthClass} bg-surface-primary border-r border-border-default py-4 shrink-0 flex-col`}
        aria-label="Main navigation">
        <ul className="space-y-1 px-2">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 py-2 rounded text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-brand-50 text-brand-700'
                      : 'text-text-secondary hover:bg-surface-secondary hover:text-text-primary'
                  }`
                }
                title={collapsed ? item.label : undefined}
              >
                <span className="w-5 text-center font-mono text-xs">{item.icon}</span>
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </>
  );
}

function StatusBar() {
  const { isOnline, isReconnecting } = useConnectivity();
  const { timezone, setTimezone } = useSettings();

  return (
    <footer className="flex items-center justify-between px-4 py-1.5 bg-surface-tertiary border-t border-border-default text-xs">
      <div>
        {!isOnline && (
          <span className="text-status-error font-medium" role="alert">
            Connection Lost {isReconnecting ? '-- Reconnecting...' : ''}
          </span>
        )}
        {isOnline && <span className="text-status-success">Connected</span>}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-text-muted">Timezone:</span>
        {(['local', 'utc', 'site'] as const).map((mode) => (
          <button
            key={mode}
            type="button"
            onClick={() => setTimezone(mode)}
            className={`px-2 py-0.5 rounded text-xs ${
              timezone.mode === mode
                ? 'bg-brand-500 text-white'
                : 'text-text-secondary hover:bg-surface-secondary'
            }`}
          >
            {mode.toUpperCase()}
          </button>
        ))}
      </div>
    </footer>
  );
}

export default function RootLayout() {
  const { isAuthenticated } = useSession();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (!isAuthenticated) {
    const returnUrl = location.pathname + location.search;
    return <Navigate to={`/login?returnUrl=${encodeURIComponent(returnUrl)}`} replace />;
  }

  return (
    <div className="flex flex-col min-h-screen">
      <TopBar onToggleMenu={() => setMobileOpen((prev) => !prev)} />
      <div className="flex flex-1 overflow-hidden">
        <NavBar collapsed={false} mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
        <main className="flex-1 overflow-auto p-6">
          <Suspense fallback={<div className="flex items-center justify-center h-full text-text-muted">Loading...</div>}>
            <Outlet />
          </Suspense>
        </main>
      </div>
      <StatusBar />
    </div>
  );
}
