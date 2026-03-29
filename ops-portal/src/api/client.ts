// Shared types used across all API domains

export interface ApiResponse<T> {
  data: T;
  meta: PaginationMeta | null;
  errors: ApiError[];
}

export interface PaginationMeta {
  page: number;
  perPage: number;
  total: number;
  totalPages: number;
}

export interface ApiError {
  code: string;
  message: string;
  field: string | null;
  detail: string | null;
}

export interface DiffChange {
  path: string;
  changeType: 'added' | 'removed' | 'modified';
  oldValue: unknown | null;
  newValue: unknown | null;
}

export interface DiffSummary {
  added: number;
  removed: number;
  modified: number;
  total: number;
}

export interface NotificationItem {
  id: string;
  type: 'approval_request' | 'drift_alert' | 'deploy_status' | 'export_ready';
  severity: 'info' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  linkTo: string;
}

export interface TimezonePreference {
  mode: 'local' | 'utc' | 'site';
}

// Request options for API calls
interface RequestOptions {
  params?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
}

// Error code to user-facing message mapping (FR-040)
const ERROR_MESSAGES: Record<string, string> = {
  ENTITY_NOT_FOUND: 'The requested resource was not found.',
  UNAUTHORIZED: 'Your session has expired. Please log in again.',
  FORBIDDEN: 'You do not have permission for this action.',
  VALIDATION_ERROR: 'Please check the highlighted fields and try again.',
  CONFLICT: 'This resource was modified by another user. Please refresh.',
  RATE_LIMITED: 'Too many requests. Please wait a moment and try again.',
  SERVICE_UNAVAILABLE: 'The service is temporarily unavailable. Please try again shortly.',
};

export function getErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] ?? 'An unexpected error occurred. Please try again.';
}

// Strip undefined values from params
function buildQueryString(params: Record<string, string | number | boolean | undefined>): string {
  const entries = Object.entries(params).filter(
    (entry): entry is [string, string | number | boolean] => entry[1] !== undefined,
  );
  if (entries.length === 0) return '';
  return '?' + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString();
}

class ApiClient {
  private baseUrl = '/api/v1';

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options?: RequestOptions,
  ): Promise<ApiResponse<T>> {
    const queryString = options?.params ? buildQueryString(options.params) : '';
    const url = `${this.baseUrl}${path}${queryString}`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };

    const response = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: options?.signal,
      credentials: 'include',
    });

    if (response.status === 401 && !window.location.pathname.startsWith('/login')) {
      const returnUrl = window.location.pathname + window.location.search;
      window.location.href = `/login?returnUrl=${encodeURIComponent(returnUrl)}`;
      throw new Error('Session expired');
    }

    if (!response.ok) {
      let message = `Request failed: ${response.status}`;
      try {
        const body = await response.json();
        if (body.errors?.[0]) {
          message = getErrorMessage(body.errors[0].code);
        } else if (body.detail) {
          message = body.detail;
        }
      } catch {
        // non-JSON error body
      }
      throw new ApiRequestError(response.status, message, []);
    }

    const envelope: ApiResponse<T> = await response.json();

    return envelope;
  }

  async get<T>(path: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('GET', path, undefined, options);
  }

  async post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('POST', path, body, options);
  }

  async put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('PUT', path, body, options);
  }

  async delete<T>(path: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('DELETE', path, undefined, options);
  }
}

export class ApiRequestError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly errors: ApiError[],
  ) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

export const apiClient = new ApiClient();
