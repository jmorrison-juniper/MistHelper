import { useQuery } from '@tanstack/react-query';
import type { PaginationMeta } from '@/api/client';
import SortableHeader from '@/components/SortableHeader';
import type { SortDir } from '@/hooks/useTableSort';

export interface ColumnDef<T> {
  key: string;
  header: string;
  render: (row: T) => React.ReactNode;
  sortable?: boolean;
}

export interface FilterDef {
  key: string;
  label: string;
  type: 'text' | 'select';
  options?: { value: string; label: string }[];
}

interface PaginatedTableProps<T> {
  queryKey: readonly unknown[];
  queryFn: (params: { page: number; filters: Record<string, string> }) => Promise<{
    data: T[];
    meta: PaginationMeta | null;
  }>;
  columns: ColumnDef<T>[];
  filters: FilterDef[];
  emptyMessage: string;
  onRowClick?: (row: T) => void;
}

import { useMemo, useState } from 'react';

export default function PaginatedTable<T extends { id?: string }>({
  queryKey,
  queryFn,
  columns,
  filters,
  emptyMessage,
  onRowClick,
}: PaginatedTableProps<T>) {
  const [page, setPage] = useState(1);
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const handleSort = (key: string) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const { data, isLoading } = useQuery({
    queryKey: [...queryKey, page, filterValues],
    queryFn: () => queryFn({ page, filters: filterValues }),
  });

  const rows = data?.data ?? [];
  const meta = data?.meta;

  const sortedRows = useMemo(() => {
    if (!sortKey) return rows;
    const col = columns.find((c) => c.key === sortKey && c.sortable);
    if (!col) return rows;

    const sorted = [...rows].sort((a, b) => {
      const aVal = (a as Record<string, unknown>)[sortKey];
      const bVal = (b as Record<string, unknown>)[sortKey];

      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return aVal - bVal;
      }

      return String(aVal).toLowerCase().localeCompare(String(bVal).toLowerCase());
    });

    return sortDir === 'desc' ? sorted.reverse() : sorted;
  }, [rows, sortKey, sortDir, columns]);

  function handleFilterChange(key: string, value: string) {
    setFilterValues((prev) => ({ ...prev, [key]: value }));
    setPage(1);
  }

  if (isLoading) {
    return <div className="p-8 text-center text-text-muted">Loading...</div>;
  }

  return (
    <div>
      {filters.length > 0 && (
        <div className="flex flex-wrap gap-3 mb-4">
          {filters.map((filter) => (
            <div key={filter.key} className="flex flex-col gap-1">
              <label htmlFor={`filter-${filter.key}`} className="text-xs font-medium text-text-secondary">
                {filter.label}
              </label>
              {filter.type === 'select' ? (
                <select
                  id={`filter-${filter.key}`}
                  value={filterValues[filter.key] ?? ''}
                  onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                  className="border border-border-default rounded px-2 py-1 text-sm"
                >
                  <option value="">All</option>
                  {filter.options?.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              ) : (
                <input
                  id={`filter-${filter.key}`}
                  type="text"
                  value={filterValues[filter.key] ?? ''}
                  onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                  placeholder={`Filter by ${filter.label.toLowerCase()}`}
                  className="border border-border-default rounded px-2 py-1 text-sm"
                />
              )}
            </div>
          ))}
        </div>
      )}

      {rows.length === 0 ? (
        <div className="p-8 text-center text-text-muted border border-border-default rounded-lg">
          {emptyMessage}
        </div>
      ) : (
        <div className="overflow-x-auto border border-border-default rounded-lg">
          <table className="w-full text-sm" role="table" aria-label="Data table">
            <thead className="bg-surface-tertiary">
              <tr>
                {columns.map((col) => (
                  col.sortable ? (
                    <SortableHeader
                      key={col.key}
                      label={col.header}
                      sortKey={col.key}
                      activeKey={sortKey ?? ''}
                      dir={sortDir}
                      onSort={handleSort}
                      className="text-left px-4 py-2 font-medium text-text-secondary border-b border-border-default"
                    />
                  ) : (
                    <th key={col.key} className="text-left px-4 py-2 font-medium text-text-secondary border-b border-border-default">
                      {col.header}
                    </th>
                  )
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row, index) => (
                <tr
                  key={row.id ?? index}
                  onClick={() => onRowClick?.(row)}
                  className={`border-b border-border-default ${onRowClick ? 'cursor-pointer hover:bg-surface-secondary' : ''}`}
                  aria-label={onRowClick ? 'Click to view details' : undefined}
                  tabIndex={onRowClick ? 0 : undefined}
                  onKeyDown={(e) => {
                    if (onRowClick && (e.key === 'Enter' || e.key === ' ')) {
                      e.preventDefault();
                      onRowClick(row);
                    }
                  }}
                >
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-2 text-text-primary">
                      {col.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {meta && meta.totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm">
          <span className="text-text-secondary" aria-live="polite">
            Page {meta.page} of {meta.totalPages} ({meta.total} items)
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={meta.page <= 1}
              className="px-3 py-1 border border-border-default rounded text-text-secondary hover:bg-surface-tertiary disabled:opacity-50"
            >
              Previous
            </button>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(meta.totalPages, p + 1))}
              disabled={meta.page >= meta.totalPages}
              className="px-3 py-1 border border-border-default rounded text-text-secondary hover:bg-surface-tertiary disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
