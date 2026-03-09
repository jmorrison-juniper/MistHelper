import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { deployQueries } from '@/api/deploy';
import type { DeployJob, JobStatus } from '@/api/deploy';
import { useTableSort } from '@/hooks/useTableSort';
import SortableHeader from '@/components/SortableHeader';

const STATUS_BADGE: Record<string, string> = {
  draft: 'bg-neutral-200 text-neutral-700',
  pending_approval: 'bg-status-warning/20 text-status-warning',
  approved: 'bg-brand-100 text-brand-700',
  scheduled: 'bg-status-info/20 text-status-info',
  running: 'bg-brand-600 text-white',
  completed: 'bg-status-success/20 text-status-success',
  failed: 'bg-status-error/20 text-status-error',
  cancelled: 'bg-neutral-200 text-neutral-500',
  rolled_back: 'bg-status-warning/20 text-status-warning',
};

const STATUSES: JobStatus[] = [
  'draft', 'pending_approval', 'approved', 'scheduled',
  'running', 'completed', 'failed', 'cancelled', 'rolled_back',
];

type JobSortKey = 'name' | 'status' | 'scheduledAt' | 'targetDevices' | 'createdBy' | 'createdAt';

const JOB_SORT_ACCESSORS: Record<JobSortKey, (j: DeployJob) => string | number | null> = {
  name: (j) => j.name,
  status: (j) => j.status,
  scheduledAt: (j) => j.scheduledAt,
  targetDevices: (j) => j.targetDevices.length,
  createdBy: (j) => j.createdBy,
  createdAt: (j) => j.createdAt,
};

export default function JobsListPage() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);

  const jobsQuery = useQuery({
    ...deployQueries.jobs({ status: statusFilter || undefined, page, per_page: 20 }),
    select: (response) => ({ data: response.data, meta: response.meta }),
  });

  const jobs = useMemo(() => jobsQuery.data?.data ?? [], [jobsQuery.data]);
  const meta = jobsQuery.data?.meta;
  const { sortKey, sortDir, handleSort, sortedData } = useTableSort<DeployJob, JobSortKey>(jobs, 'createdAt', JOB_SORT_ACCESSORS, 'desc');

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Deployment Jobs</h1>
        <button
          type="button"
          onClick={() => navigate('/deploy/jobs/new')}
          className="px-4 py-2 bg-brand-600 text-white rounded text-sm font-medium hover:bg-brand-700"
        >
          New Job
        </button>
      </div>

      <div className="flex gap-2 items-center">
        <label htmlFor="status-filter" className="text-sm text-text-secondary">Status:</label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(event) => { setStatusFilter(event.target.value); setPage(1); }}
          className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary"
        >
          <option value="">All</option>
          {STATUSES.map((status) => (
            <option key={status} value={status}>{status.replace(/_/g, ' ')}</option>
          ))}
        </select>
      </div>

      {jobsQuery.isLoading && <div className="text-text-muted">Loading jobs...</div>}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-default text-left text-text-muted">
              <SortableHeader label="Name" sortKey="name" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Status" sortKey="status" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Scheduled" sortKey="scheduledAt" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Targets" sortKey="targetDevices" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Created By" sortKey="createdBy" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Created" sortKey="createdAt" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
            </tr>
          </thead>
          <tbody>
            {sortedData.map((job) => (
              <tr
                key={job.id}
                onClick={() => navigate(`/deploy/jobs/${job.id}`)}
                className="border-b border-border-default hover:bg-surface-secondary cursor-pointer"
              >
                <td className="px-4 py-3 text-text-primary font-medium">{job.name}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${STATUS_BADGE[job.status] ?? ''}`}>
                    {job.status.replace(/_/g, ' ')}
                  </span>
                </td>
                <td className="px-4 py-3 text-text-secondary">
                  {job.scheduledAt ? new Date(job.scheduledAt).toLocaleString() : 'Immediate'}
                </td>
                <td className="px-4 py-3 text-text-secondary">
                  {job.targetDevices.length} device{job.targetDevices.length !== 1 ? 's' : ''}
                </td>
                <td className="px-4 py-3 text-text-secondary">{job.createdBy}</td>
                <td className="px-4 py-3 text-text-secondary">{new Date(job.createdAt).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {jobs.length === 0 && !jobsQuery.isLoading && (
        <div className="text-center py-8 text-text-muted">No deployment jobs found.</div>
      )}

      {meta && meta.totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 mt-4">
          <button type="button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}
            className="px-3 py-1 text-sm border border-border-default rounded disabled:opacity-50">Previous</button>
          <span className="text-sm text-text-secondary">Page {page} of {meta.totalPages}</span>
          <button type="button" onClick={() => setPage((p) => p + 1)} disabled={page >= meta.totalPages}
            className="px-3 py-1 text-sm border border-border-default rounded disabled:opacity-50">Next</button>
        </div>
      )}
    </div>
  );
}
