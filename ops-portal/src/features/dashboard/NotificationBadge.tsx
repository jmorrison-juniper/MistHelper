import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { systemQueries } from '@/api/sync';
import { useSettings } from '@/hooks/useSettings';
import type { NotificationItem } from '@/api/sync';

const SEVERITY_STYLES: Record<string, string> = {
  info: 'text-status-info',
  warning: 'text-status-warning',
  error: 'text-status-error',
};

const TYPE_ICONS: Record<string, string> = {
  approval_request: '[Approve]',
  drift_alert: '[Drift]',
  deploy_status: '[Deploy]',
  export_ready: '[Export]',
};

export function NotificationBadge() {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { polling } = useSettings();

  const notifQuery = useQuery({
    ...systemQueries.notifications(),
    refetchInterval: polling.passiveIntervalMs,
    select: (response) => response.data,
  });

  const notifications: NotificationItem[] = notifQuery.data ?? [];
  const unreadCount = notifications.filter((n) => !n.read).length;

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  function handleClick(notification: NotificationItem) {
    navigate(notification.linkTo);
    setIsOpen(false);
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="relative p-1.5 rounded hover:bg-surface-secondary text-text-secondary"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-status-error text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-surface-primary border border-border-default rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
          <div className="px-4 py-2 border-b border-border-default font-semibold text-sm text-text-primary">
            Notifications
          </div>

          {notifications.length === 0 && (
            <div className="px-4 py-6 text-sm text-text-muted text-center">No notifications</div>
          )}

          {notifications.map((notification) => (
            <button
              key={notification.id}
              type="button"
              onClick={() => handleClick(notification)}
              className={`w-full text-left px-4 py-3 hover:bg-surface-secondary border-b border-border-default last:border-0 ${
                !notification.read ? 'bg-brand-50' : ''
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs font-mono ${SEVERITY_STYLES[notification.severity]}`}>
                  {TYPE_ICONS[notification.type]}
                </span>
                <span className="text-sm font-medium text-text-primary truncate">{notification.title}</span>
              </div>
              <p className="text-xs text-text-secondary line-clamp-2">{notification.message}</p>
              <p className="text-xs text-text-muted mt-1">
                {new Date(notification.timestamp).toLocaleString()}
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
