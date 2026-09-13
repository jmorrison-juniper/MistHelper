interface RetentionMessageProps {
  oldestTimestamp: string | null;
  onLoadOldest: (timestamp: string) => void;
}

export function RetentionMessage({ oldestTimestamp, onLoadOldest }: RetentionMessageProps) {
  return (
    <div className="bg-surface-primary rounded-lg shadow p-6 text-center">
      <div className="text-lg font-semibold text-text-primary mb-2">
        No Data Available
      </div>
      <p className="text-sm text-text-secondary mb-4">
        The requested timestamp is outside the data retention window.
        Historical data has been aged out for this time period.
      </p>
      {oldestTimestamp && (
        <div>
          <p className="text-sm text-text-muted mb-2">
            Oldest available data is from{' '}
            <span className="font-medium text-text-primary">
              {new Date(oldestTimestamp).toLocaleString()}
            </span>
          </p>
          <button
            type="button"
            onClick={() => onLoadOldest(oldestTimestamp)}
            className="px-4 py-2 bg-brand-600 text-white rounded font-medium hover:bg-brand-700 text-sm"
          >
            Load Oldest Available Snapshot
          </button>
        </div>
      )}
    </div>
  );
}
