import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { systemQueries } from '@/api/sync';
import type { SearchResult } from '@/api/sync';

const TYPE_LABELS: Record<string, string> = {
  org: 'Organization',
  site: 'Site',
  device: 'Device',
};

const TYPE_ROUTES: Record<string, (result: SearchResult) => string> = {
  org: (r) => `/orgs/${r.id}`,
  site: (r) => `/orgs/_/sites/${r.id}`,
  device: (r) => `/orgs/_/sites/_/devices/${r.id}`,
};

export function GlobalSearch() {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const searchQuery = useQuery({
    ...systemQueries.search(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
    select: (response) => response.data,
  });

  const results = searchQuery.data ?? [];
  const grouped = results.reduce<Record<string, SearchResult[]>>((acc, result) => {
    const group = acc[result.type] ?? [];
    group.push(result);
    acc[result.type] = group;
    return acc;
  }, {});

  function handleSelect(result: SearchResult) {
    const routeFn = TYPE_ROUTES[result.type];
    if (routeFn) {
      navigate(routeFn(result));
    }
    setQuery('');
    setIsOpen(false);
  }

  return (
    <div ref={containerRef} className="relative w-full max-w-sm">
      <input
        ref={inputRef}
        type="search"
        value={query}
        onChange={(e) => { setQuery(e.target.value); setIsOpen(true); }}
        onFocus={() => setIsOpen(true)}
        placeholder="Search orgs, sites, devices..."
        className="w-full border border-border-default rounded px-3 py-1.5 text-sm bg-surface-primary focus:outline-none focus:ring-2 focus:ring-brand-500"
        aria-label="Global search"
      />

      {isOpen && debouncedQuery.length >= 2 && (
        <div id="global-search-results" className="absolute top-full left-0 right-0 mt-1 bg-surface-primary border border-border-default rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
          {searchQuery.isLoading && (
            <div className="px-4 py-3 text-sm text-text-muted">Searching...</div>
          )}

          {!searchQuery.isLoading && results.length === 0 && (
            <div className="px-4 py-3 text-sm text-text-muted">No results found.</div>
          )}

          {Object.entries(grouped).map(([type, items]) => (
            <div key={type}>
              <div className="px-4 py-1.5 text-xs font-semibold text-text-muted uppercase bg-surface-secondary">
                {TYPE_LABELS[type] ?? type}
              </div>
              {items.map((result) => (
                <button
                  key={result.id}
                  type="button"
                  onClick={() => handleSelect(result)}
                  className="w-full text-left px-4 py-2 hover:bg-surface-secondary text-sm"
                >
                  <div className="font-medium text-text-primary">{result.name}</div>
                  <div className="text-xs text-text-muted">{result.detail}</div>
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
