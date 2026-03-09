import { useState, useMemo } from 'react';

export type SortDir = 'asc' | 'desc';

export interface SortState<K extends string = string> {
  key: K;
  dir: SortDir;
}

export interface UseTableSortResult<T, K extends string = string> {
  sortKey: K;
  sortDir: SortDir;
  handleSort: (key: K) => void;
  sortedData: T[];
}

type SortValueFn<T> = (item: T) => string | number | null | undefined;

export function useTableSort<T, K extends string = string>(
  data: T[],
  defaultKey: K,
  valueAccessors: Record<K, SortValueFn<T>>,
  defaultDir: SortDir = 'asc',
): UseTableSortResult<T, K> {
  const [sortKey, setSortKey] = useState<K>(defaultKey);
  const [sortDir, setSortDir] = useState<SortDir>(defaultDir);

  const handleSort = (key: K) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortedData = useMemo(() => {
    const accessor = valueAccessors[sortKey];
    if (!accessor) return data;

    const sorted = [...data].sort((a, b) => {
      const aVal = accessor(a);
      const bVal = accessor(b);

      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return aVal - bVal;
      }

      return String(aVal).toLowerCase().localeCompare(String(bVal).toLowerCase());
    });

    return sortDir === 'desc' ? sorted.reverse() : sorted;
  }, [data, sortKey, sortDir, valueAccessors]);

  return { sortKey, sortDir, handleSort, sortedData };
}
