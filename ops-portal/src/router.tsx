import { lazy } from 'react';
import { createBrowserRouter, Navigate } from 'react-router';
import type { RouteObject } from 'react-router';

// Lazy-loaded page components
const RootLayout = lazy(() => import('@/pages/shell/RootLayout'));
const LoginPage = lazy(() => import('@/pages/shell/LoginPage'));
const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage'));
const OrgDetailPage = lazy(() => import('@/pages/dashboard/OrgDetailPage'));
const SiteDetailPage = lazy(() => import('@/pages/dashboard/SiteDetailPage'));
const DeviceDetailPage = lazy(() => import('@/pages/dashboard/DeviceDetailPage'));
const TimeTravelPage = lazy(() => import('@/pages/config/TimeTravelPage'));
const RevisionsPage = lazy(() => import('@/pages/config/RevisionsPage'));
const BaselinesPage = lazy(() => import('@/pages/config/BaselinesPage'));
const JobsListPage = lazy(() => import('@/pages/deploy/jobs/JobsListPage'));
const NewJobPage = lazy(() => import('@/pages/deploy/jobs/NewJobPage'));
const JobDetailPage = lazy(() => import('@/pages/deploy/jobs/JobDetailPage'));
const RolloutListPage = lazy(() => import('@/pages/deploy/rollouts/RolloutListPage'));
const NewRolloutPage = lazy(() => import('@/pages/deploy/rollouts/NewRolloutPage'));
const RolloutDetailPage = lazy(() => import('@/pages/deploy/rollouts/RolloutDetailPage'));
const TemplatesPage = lazy(() => import('@/pages/deploy/TemplatesPage'));
const GoldenImagesPage = lazy(() => import('@/pages/deploy/GoldenImagesPage'));
const AuditListPage = lazy(() => import('@/pages/audit/AuditListPage'));
const AuditDetailPage = lazy(() => import('@/pages/audit/AuditDetailPage'));
const AuditExportPage = lazy(() => import('@/pages/audit/AuditExportPage'));
const CompliancePage = lazy(() => import('@/pages/audit/CompliancePage'));
const CorrelationsPage = lazy(() => import('@/pages/audit/CorrelationsPage'));
const DriftListPage = lazy(() => import('@/pages/drift/DriftListPage'));
const DriftDetailPage = lazy(() => import('@/pages/drift/DriftDetailPage'));
const SettingsPage = lazy(() => import('@/pages/settings/SettingsPage'));

const routes: RouteObject[] = [
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    element: <RootLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'orgs/:orgId', element: <OrgDetailPage /> },
      { path: 'orgs/:orgId/sites/:siteId', element: <SiteDetailPage /> },
      { path: 'orgs/:orgId/sites/:siteId/devices/:deviceId', element: <DeviceDetailPage /> },
      { path: 'time-travel', element: <TimeTravelPage /> },
      { path: 'config/revisions', element: <RevisionsPage /> },
      { path: 'config/baselines', element: <BaselinesPage /> },
      { path: 'deploy/jobs', element: <JobsListPage /> },
      { path: 'deploy/jobs/new', element: <NewJobPage /> },
      { path: 'deploy/jobs/:jobId', element: <JobDetailPage /> },
      { path: 'deploy/rollouts', element: <RolloutListPage /> },
      { path: 'deploy/rollouts/new', element: <NewRolloutPage /> },
      { path: 'deploy/rollouts/:rolloutId', element: <RolloutDetailPage /> },
      { path: 'deploy/templates', element: <TemplatesPage /> },
      { path: 'deploy/golden-images', element: <GoldenImagesPage /> },
      { path: 'audit', element: <AuditListPage /> },
      { path: 'audit/export', element: <AuditExportPage /> },
      { path: 'audit/compliance', element: <CompliancePage /> },
      { path: 'audit/correlations', element: <CorrelationsPage /> },
      { path: 'audit/:recordId', element: <AuditDetailPage /> },
      { path: 'drift', element: <DriftListPage /> },
      { path: 'drift/:alertId', element: <DriftDetailPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'settings/notifications', element: <SettingsPage /> },
    ],
  },
];

export const router = createBrowserRouter(routes);
