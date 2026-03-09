import { useQuery } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router';
import { syncQueries } from '@/api/sync';
import { useNavigationContext } from '@/hooks/useNavigationContext';
import { useEffect, useMemo } from 'react';
import { useTableSort } from '@/hooks/useTableSort';
import SortableHeader from '@/components/SortableHeader';
import type { InventorySite } from '@/api/sync';

type SortKey = 'name' | 'location' | 'deviceCount';

const SORT_ACCESSORS: Record<SortKey, (s: InventorySite) => string | number | null> = {
  name: (s) => s.name,
  location: (s) => s.location ?? '',
  deviceCount: (s) => s.deviceCount,
};

function SiteRow({ site, orgId }: { site: InventorySite; orgId: string }) {
  const navigate = useNavigate();

  return (
    <tr
      className="hover:bg-surface-secondary cursor-pointer"
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/orgs/${orgId}/sites/${site.id}`)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate(`/orgs/${orgId}/sites/${site.id}`); }}
    >
      <td className="px-4 py-3 font-medium text-text-primary">{site.name}</td>
      <td className="px-4 py-3 text-text-secondary">{site.location ?? '-'}</td>
      <td className="px-4 py-3 text-text-secondary">{site.deviceCount}</td>
    </tr>
  );
}

export default function OrgDetailPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const { setOrg } = useNavigationContext();

  const sitesQuery = useQuery({
    ...syncQueries.sites(orgId!),
    enabled: Boolean(orgId),
    select: (response) => response.data,
  });

  const orgsQuery = useQuery({
    ...syncQueries.orgs(),
    select: (response) => response.data,
  });

  const org = orgsQuery.data?.find((o) => o.id === orgId);

  useEffect(() => {
    if (org) {
      setOrg(org.id, org.name);
    }
  }, [org, setOrg]);

  const sites = useMemo(() => sitesQuery.data ?? [], [sitesQuery.data]);
  const { sortKey, sortDir, handleSort, sortedData } = useTableSort<InventorySite, SortKey>(sites, 'name', SORT_ACCESSORS);

  if (sitesQuery.isLoading) {
    return <div className="p-6 text-text-muted">Loading sites...</div>;
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-text-primary">{org?.name ?? 'Organization'}</h1>
      <p className="text-sm text-text-secondary">
        {sites.length} site{sites.length !== 1 ? 's' : ''}
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-default text-left text-text-muted">
              <SortableHeader label="Site Name" sortKey="name" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Location" sortKey="location" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Devices" sortKey="deviceCount" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
            </tr>
          </thead>
          <tbody>
            {sortedData.map((site) => (
              <SiteRow key={site.id} site={site} orgId={orgId!} />
            ))}
          </tbody>
        </table>
      </div>

      {sites.length === 0 && (
        <div className="text-center py-8 text-text-muted">No sites found for this organization.</div>
      )}
    </div>
  );
}
