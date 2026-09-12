import { useQuery } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router';
import { syncQueries } from '@/api/sync';
import { useNavigationContext } from '@/hooks/useNavigationContext';
import { useEffect, useMemo, useState } from 'react';
import { useTableSort } from '@/hooks/useTableSort';
import SortableHeader from '@/components/SortableHeader';
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

type DeviceSortKey = 'name' | 'type' | 'model' | 'connectionStatus' | 'firmwareVersion' | 'uptime';

const DEVICE_SORT_ACCESSORS: Record<DeviceSortKey, (d: InventoryDevice) => string | number | null> = {
  name: (d) => d.name,
  type: (d) => d.type,
  model: (d) => d.model,
  connectionStatus: (d) => d.connectionStatus,
  firmwareVersion: (d) => d.firmwareVersion,
  uptime: (d) => d.uptime,
};

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
  const devices = useMemo(
    () => typeFilter === 'all' ? allDevices : allDevices.filter((d) => d.type === typeFilter),
    [allDevices, typeFilter],
  );
  const { sortKey, sortDir, handleSort, sortedData } = useTableSort<InventoryDevice, DeviceSortKey>(devices, 'name', DEVICE_SORT_ACCESSORS);

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
              <SortableHeader label="Name" sortKey="name" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Type" sortKey="type" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Model" sortKey="model" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Status" sortKey="connectionStatus" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Firmware" sortKey="firmwareVersion" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Uptime" sortKey="uptime" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
            </tr>
          </thead>
          <tbody>
            {sortedData.map((device) => (
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
