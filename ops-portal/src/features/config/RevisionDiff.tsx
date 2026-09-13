import { useQuery } from '@tanstack/react-query';
import { configQueries } from '@/api/config';
import DiffViewer from '@/components/DiffViewer';

interface RevisionDiffProps {
  leftId: string;
  rightId: string;
}

export function RevisionDiff({ leftId, rightId }: RevisionDiffProps) {
  const diffQuery = useQuery({
    ...configQueries.diff(leftId, rightId),
    enabled: Boolean(leftId) && Boolean(rightId),
    select: (response) => response.data,
  });

  if (diffQuery.isLoading) {
    return <div className="text-text-muted">Computing diff...</div>;
  }

  if (diffQuery.isError) {
    return <div className="text-status-error">Failed to compute diff.</div>;
  }

  const diff = diffQuery.data;
  if (!diff || diff.changes.length === 0) {
    return (
      <div className="bg-surface-primary rounded-lg shadow p-4 text-center text-text-muted">
        No differences found between the selected revisions.
      </div>
    );
  }

  return (
    <div className="bg-surface-primary rounded-lg shadow p-4">
      <DiffViewer
        changes={diff.changes}
        summary={diff.summary}
        leftLabel={`Revision ${leftId.slice(0, 8)}`}
        rightLabel={`Revision ${rightId.slice(0, 8)}`}
        layout="side-by-side"
      />
    </div>
  );
}
