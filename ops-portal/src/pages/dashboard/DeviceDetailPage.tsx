import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router';
import { syncQueries } from '@/api/sync';
import { useNavigationContext } from '@/hooks/useNavigationContext';
import { useEffect } from 'react';

const STATUS_STYLES: Record<string, string> = {
  connected: 'bg-status-success text-white',
  disconnected: 'bg-status-error text-white',
};

function formatUptime(seconds: number | null): string {
  if (seconds === null) return 'Unknown';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${days}d ${hours}h ${minutes}m`;
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[140px_1fr] gap-4 py-3 border-b border-border-default">
      <span className="text-text-muted text-sm">{label}</span>
      <span className="text-text-primary font-medium font-mono text-sm">{value || '-'}</span>
    </div>
  );
}

export default function DeviceDetailPage() {
  const { orgId, siteId, deviceId } = useParams<{ orgId: string; siteId: string; deviceId: string }>();
  const { setDevice } = useNavigationContext();

  const deviceQuery = useQuery({
    ...syncQueries.device(deviceId!),
    enabled: Boolean(deviceId),
    select: (response) => response.data,
  });

  const device = deviceQuery.data;

  useEffect(() => {
    if (device) {
      setDevice(device.id);
    }
  }, [device, setDevice]);

  if (deviceQuery.isLoading) {
    return <div className="p-6 text-text-muted">Loading device...</div>;
  }

  if (!device) {
    return <div className="p-6 text-status-error">Device not found.</div>;
  }

  const lastSeen = device.lastSeenAt ? new Date(device.lastSeenAt).toLocaleString() : 'Never';

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-text-primary">{device.name || device.model}</h1>
        <span className={`text-xs px-3 py-1 rounded-full font-medium ${STATUS_STYLES[device.connectionStatus] || 'bg-gray-500 text-white'}`}>
          {device.connectionStatus}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface-primary rounded-lg shadow p-6">
          <h2 className="font-semibold text-text-primary mb-4 text-lg">Device Information</h2>
          <DetailRow label="Model" value={device.model} />
          <DetailRow label="Type" value={device.type} />
          <DetailRow label="Serial" value={device.serial} />
          <DetailRow label="MAC Address" value={device.mac} />
          <DetailRow label="Firmware" value={device.firmwareVersion} />
          <DetailRow label="Uptime" value={formatUptime(device.uptime)} />
          <DetailRow label="Last Seen" value={lastSeen} />
        </div>

        <div className="bg-surface-primary rounded-lg shadow p-6">
          <h2 className="font-semibold text-text-primary mb-4 text-lg">Quick Navigation</h2>
          <div className="space-y-1">
          <Link
            to={`/time-travel?device=${deviceId}&org=${orgId}&site=${siteId}`}
            className="block px-3 py-2 rounded hover:bg-surface-secondary text-brand-600 text-sm"
          >
            View Time-Travel History
          </Link>
          <Link
            to={`/config/revisions?entity_type=device&entity_id=${deviceId}`}
            className="block px-3 py-2 rounded hover:bg-surface-secondary text-brand-600 text-sm"
          >
            View Revision History
          </Link>
          <Link
            to={`/drift?entity_id=${deviceId}`}
            className="block px-3 py-2 rounded hover:bg-surface-secondary text-brand-600 text-sm"
          >
            View Drift Alerts
          </Link>
          <Link
            to={`/audit?entity_id=${deviceId}`}
            className="block px-3 py-2 rounded hover:bg-surface-secondary text-brand-600 text-sm"
          >
            View Audit Records
          </Link>
        </div>
        </div>
      </div>
    </div>
  );
}
