import { NavLink, Outlet } from 'react-router';

const TABS = [
  { to: '/audit', label: 'Audit Trail', end: true },
  { to: '/audit/export', label: 'Export' },
  { to: '/audit/compliance', label: 'Compliance' },
  { to: '/audit/correlations', label: 'Correlations' },
];

export function AuditNav() {
  return (
    <div>
      <nav className="flex border-b border-border-default mb-4" aria-label="Audit sections">
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.end}
            className={({ isActive }) =>
              `px-4 py-2 text-sm font-medium border-b-2 ${
                isActive
                  ? 'border-brand-600 text-brand-600'
                  : 'border-transparent text-text-secondary hover:text-text-primary'
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  );
}
