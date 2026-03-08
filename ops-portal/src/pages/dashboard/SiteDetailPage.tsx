import { useQuery } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router';
import { syncQueries } from '@/api/sync';
import { useNavigationContext } from '@/hooks/useNavigationContext';
import { useEffect, useState } from 'react';
import type { InventoryDevice } from '@/api/sync';

type DeviceType = 'all' | 'ap' | 'switch' | 'gateway';

const TYPE_TABS: { key: DeviceType; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'ap', label: 'APs' },
  { key: 'switch', label: 'Switches' },
  { key: 'gateway', label: 'Gateways' },
];

const STATUS_STYLES: Record<string, string> = {
  connected: 'text-status-success',
  disconnected: 'text-status-error',
};

function formatUptime(seconds: number | null): string {
  if (seconds === null) return '-';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  if (days > 0) return `${days}d ${hours}h`;
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

function DeviceRow({ device, orgId, siteId }: { device: InventoryDevice; orgId: string; siteId: string }) {
  const navigate = useNavigate();
  const path = `/orgs/${orgId}/sites/${siteId}/devices/${device.id}`;

  return (
    <tr
      className="hover:bg-surface-secondary cursor-pointer"
      role="button"
      tabIndex={0}
      onClick={() => navigate(path)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate(path); }}
    >
      <td className="px-4 py-3 font-medium text-text-primary">{device.name}</td>
      <td className="px-4 py-3 text-text-secondary capitalize">{device.type}</td>
      <td className="px-4 py-3 text-text-secondary">{device.model}</td>
      <td className={`px-4 py-3 font-medium ${STATUS_STYLES[device.connectionStatus]}`}>
        {device.connectionStatus}
      </td>
      <td className="px-4 py-3 text-text-secondary">{device.firmwareVersion}</td>
      <td className="px-4 py-3 text-text-secondary">{formatUptime(device.uptime)}</td>
    </tr>
  );
}

export default function SiteDetailPage() {
  const { orgId, siteId } = useParams<{ orgId: string; siteId: string }>();
  const { setSite } = useNavigationContext();
  const [typeFilter, setTypeFilter] = useState<DeviceType>('all');

  const devicesQuery = useQuery({
    ...syncQueries.devices(siteId!),
    enabled: Boolean(siteId),
    select: (response) => response.data,
  });

  const sitesQuery = useQuery({
    ...syncQueries.sites(orgId!),
    enabled: Boolean(orgId),
    select: (response) => response.data,
  });

  const site = sitesQuery.data?.find((s) => s.id === siteId);

  useEffect(() => {
    if (site) {
      setSite(site.id, site.name);
    }
  }, [site, setSite]);

  const allDevices = devicesQuery.data ?? [];
  const devices = typeFilter === 'all' ? allDevices : allDevices.filter((d) => d.type === typeFilter);

  if (devicesQuery.isLoading) {
    return <div className="p-6 text-text-muted">Loading devices...</div>;
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-text-primary">{site?.name ?? 'Site'}</h1>
      <p className="text-sm text-text-secondary">{allDevices.length} device{allDevices.length !== 1 ? 's' : ''}</p>

      <div className="flex gap-1 border-b border-border-default">
        {TYPE_TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setTypeFilter(tab.key)}
            className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
              typeFilter === tab.key
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-text-muted hover:text-text-secondary'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-default text-left text-text-muted">
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Model</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Firmware</th>
              <th className="px-4 py-2">Uptime</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((device) => (
              <DeviceRow key={device.id} device={device} orgId={orgId!} siteId={siteId!} />
            ))}
          </tbody>
        </table>
      </div>

      {devices.length === 0 && (
        <div className="text-center py-8 text-text-muted">No devices found.</div>
      )}
    </div>
  );
}
