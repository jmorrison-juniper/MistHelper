import type { SortDir } from '@/hooks/useTableSort';

function SortIndicator({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className="ml-1 opacity-30">&#8597;</span>;
  return <span className="ml-1">{dir === 'asc' ? '\u25B2' : '\u25BC'}</span>;
}

interface SortableHeaderProps<K extends string> {
  label: string;
  sortKey: K;
  activeKey: K;
  dir: SortDir;
  onSort: (key: K) => void;
  className?: string;
}

export default function SortableHeader<K extends string>({
  label,
  sortKey,
  activeKey,
  dir,
  onSort,
  className = 'px-4 py-2',
}: SortableHeaderProps<K>) {
  return (
    <th
      className={`${className} cursor-pointer select-none hover:text-text-primary`}
      onClick={() => onSort(sortKey)}
    >
      {label}
      <SortIndicator active={activeKey === sortKey} dir={dir} />
    </th>
  );
}
