import { useState, useEffect, useCallback } from 'react';

interface ConnectivityState {
  isOnline: boolean;
  isReconnecting: boolean;
}

export function useConnectivity(): ConnectivityState {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isReconnecting, setIsReconnecting] = useState(false);

  const handleOnline = useCallback(() => {
    setIsOnline(true);
    setIsReconnecting(false);
  }, []);

  const handleOffline = useCallback(() => {
    setIsOnline(false);
    setIsReconnecting(true);
  }, []);

  useEffect(() => {
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleOnline, handleOffline]);

  // Reconnection polling when offline
  useEffect(() => {
    if (isOnline || !isReconnecting) return;
    const interval = setInterval(async () => {
      try {
        const response = await fetch('/api/v1/system/health', {
          method: 'HEAD',
          cache: 'no-store',
        });
        if (response.ok) {
          setIsOnline(true);
          setIsReconnecting(false);
        }
      } catch {
        // Still offline
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [isOnline, isReconnecting]);

  return { isOnline, isReconnecting };
}
