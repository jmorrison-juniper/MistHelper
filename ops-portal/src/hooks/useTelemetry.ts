import { useEffect, useRef } from 'react';
import { apiClient } from '@/api/client';

interface TelemetryEvent {
  type: 'error' | 'api_failure' | 'page_load';
  message: string;
  timestamp: string;
  url: string;
  detail: Record<string, unknown> | null;
}

const BATCH_INTERVAL_MS = 30_000;
const MAX_BATCH_SIZE = 50;

let buffer: TelemetryEvent[] = [];

function push(event: TelemetryEvent) {
  buffer.push(event);
  if (buffer.length >= MAX_BATCH_SIZE) {
    flush();
  }
}

function flush() {
  if (buffer.length === 0) return;
  const batch = buffer.splice(0, MAX_BATCH_SIZE);
  apiClient.post('/system/metrics', { events: batch }).catch(() => {
    // Silently discard — telemetry must not break the app
  });
}

function captureError(event: ErrorEvent) {
  push({
    type: 'error',
    message: event.message,
    timestamp: new Date().toISOString(),
    url: window.location.href,
    detail: {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    },
  });
}

function captureUnhandledRejection(event: PromiseRejectionEvent) {
  const message = event.reason instanceof Error ? event.reason.message : String(event.reason);
  push({
    type: 'error',
    message: `Unhandled rejection: ${message}`,
    timestamp: new Date().toISOString(),
    url: window.location.href,
    detail: null,
  });
}

function capturePageLoad() {
  if (typeof performance === 'undefined') return;
  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
  if (!navigation) return;
  push({
    type: 'page_load',
    message: 'Page loaded',
    timestamp: new Date().toISOString(),
    url: window.location.href,
    detail: {
      domContentLoaded: Math.round(navigation.domContentLoadedEventEnd - navigation.startTime),
      loadComplete: Math.round(navigation.loadEventEnd - navigation.startTime),
      ttfb: Math.round(navigation.responseStart - navigation.requestStart),
    },
  });
}

export function captureApiFailure(status: number, url: string, message: string) {
  push({
    type: 'api_failure',
    message,
    timestamp: new Date().toISOString(),
    url,
    detail: { status },
  });
}

export function useTelemetry() {
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    window.addEventListener('error', captureError);
    window.addEventListener('unhandledrejection', captureUnhandledRejection);

    capturePageLoad();

    const intervalId = setInterval(flush, BATCH_INTERVAL_MS);

    return () => {
      window.removeEventListener('error', captureError);
      window.removeEventListener('unhandledrejection', captureUnhandledRejection);
      clearInterval(intervalId);
      flush();
    };
  }, []);
}
