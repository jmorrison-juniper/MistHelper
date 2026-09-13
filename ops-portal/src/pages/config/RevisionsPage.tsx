import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { configQueries } from '@/api/config';
import type { RevisionParams } from '@/api/config';

// The page size that the list requests from the API.
const PER_PAGE = 50;

// The colors that mark where a revision came from.
const SOURCE_BADGE: Record<string, string> = {
  sync: 'bg-blue-100 text-blue-700',
  manual: 'bg-amber-100 text-amber-700',
  restore: 'bg-purple-100 text-purple-700',
};

export default function RevisionsPage() {
  const [entityType, setEntityType] = useState('');
  const [entityId, setEntityId] = useState('');

  // Send a filter only when the operator typed one, so an empty box means "all".
  const params: RevisionParams = { page: 1, per_page: PER_PAGE };
  if (entityType) params.entity_type = entityType;
  if (entityId) params.entity_id = entityId;

  const revisionsQuery = useQuery({
    ...configQueries.revisions(params),
    select: (response) => response.data,
  });

  const revisions = revisionsQuery.data ?? [];

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Configuration Revisions</h1>
        <span className="text-sm text-text-muted">{revisions.length} shown</span>
      </div>

      <div className="flex flex-wrap gap-3">
        <div>
          <label htmlFor="revision-entity-type" className="block text-xs text-text-muted mb-0.5">
            Entity Type
          </label>
          <input id="revision-entity-type" type="text" value={entityType}
            onChange={(event) => setEntityType(event.target.value)}
            className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary w-40"
            placeholder="device" />
        </div>
        <div>
          <label htmlFor="revision-entity-id" className="block text-xs text-text-muted mb-0.5">
            Entity ID
          </label>
          <input id="revision-entity-id" type="text" value={entityId}
            onChange={(event) => setEntityId(event.target.value)}
            className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary w-64"
            placeholder="Filter..." />
        </div>
      </div>

      {revisionsQuery.isLoading && (
        <p className="text-text-muted text-sm">Loading the configuration revisions...</p>
      )}

      {revisionsQuery.isError && (
        <p role="alert" className="text-sm text-status-error">
          The revision list did not load. Please try again.
        </p>
      )}

      {!revisionsQuery.isLoading && !revisionsQuery.isError && revisions.length === 0 && (
        <p className="text-text-muted text-sm py-8 text-center">No configuration revision matches</p>
      )}

      {revisions.length > 0 && (
        <table className="w-full text-sm border border-border-default rounded-lg overflow-hidden">
          <thead className="bg-surface-secondary text-left text-text-muted text-xs uppercase">
            <tr>
              <th className="px-3 py-2">Captured</th>
              <th className="px-3 py-2">Entity</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Actor</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Summary</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-default">
            {revisions.map((revision) => (
              <tr key={revision.id} className="hover:bg-surface-secondary">
                <td className="px-3 py-2 text-text-secondary">
                  {new Date(revision.capturedAt).toLocaleString()}
                </td>
                <td className="px-3 py-2 font-mono text-text-primary">{revision.entityId}</td>
                <td className="px-3 py-2 text-text-secondary">{revision.entityType}</td>
                <td className="px-3 py-2 text-text-secondary">{revision.actor}</td>
                <td className="px-3 py-2">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${SOURCE_BADGE[revision.source] ?? ''}`}>
                    {revision.source}
                  </span>
                </td>
                <td className="px-3 py-2 text-text-secondary">{revision.summary ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
