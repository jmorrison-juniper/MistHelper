import { apiClient } from './client';
import type { DiffChange } from './client';

// --- Domain 5 Types ---

export interface SyncStatus {
  orgId: string;
  lastSyncAt: string;
  nextPollAt: string;
  state: 'synced' | 'stale' | 'error';
  entityCounts: EntitySyncCount[];
}

export interface EntitySyncCount {
  entityType: string;
  total: number;
  synced: number;
  stale: number;
  error: number;
}

export interface InventoryOrg {
  id: string;
  name: string;
  siteCount: number;
  deviceCount: number;
}

export interface InventorySite {
  id: string;
  orgId: string;
  name: string;
  location: string | null;
  deviceCount: number;
}

export interface InventoryDevice {
  id: string;
  orgId: string;
  siteId: string;
  name: string;
  type: 'ap' | 'switch' | 'gateway';
  model: string;
  serial: string;
  mac: string;
  firmwareVersion: string;
  connectionStatus: 'connected' | 'disconnected';
  uptime: number | null;
  lastSeenAt: string | null;
}

export interface DriftAlert {
  id: string;
  entityType: string;
  entityId: string;
  entityName: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  fieldCount: number;
  detectedAt: string;
  acknowledged: boolean;
  baselineId: string;
  diff: DiffChange[];
}

// --- Query Factories ---

export const syncQueries = {
  status: () => ({
    queryKey: ['sync', 'status'] as const,
    queryFn: () => apiClient.get<SyncStatus[]>('/sync/status'),
  }),

  orgs: () => ({
    queryKey: ['sync', 'inventory', 'orgs'] as const,
    queryFn: () => apiClient.get<InventoryOrg[]>('/inventory/orgs'),
  }),

  sites: (orgId: string) => ({
    queryKey: ['sync', 'inventory', 'sites', orgId] as const,
    queryFn: () => apiClient.get<InventorySite[]>('/inventory/sites', { params: { org_id: orgId } }),
  }),

  devices: (siteId: string) => ({
    queryKey: ['sync', 'inventory', 'devices', siteId] as const,
    queryFn: () => apiClient.get<InventoryDevice[]>('/inventory/devices', { params: { site_id: siteId } }),
  }),

  searchDevices: (search: string) => ({
    queryKey: ['sync', 'inventory', 'devices', 'search', search] as const,
    queryFn: () => apiClient.get<InventoryDevice[]>('/inventory/devices', { params: search ? { search } : undefined }),
  }),

  device: (deviceId: string) => ({
    queryKey: ['sync', 'inventory', 'devices', 'detail', deviceId] as const,
    queryFn: () => apiClient.get<InventoryDevice>(`/inventory/devices/${deviceId}`),
  }),

  driftAlerts: (params?: { acknowledged?: boolean }) => ({
    queryKey: ['sync', 'drift', params] as const,
    queryFn: () => apiClient.get<DriftAlert[]>('/drift/alerts', { params }),
  }),

  driftAlert: (alertId: string) => ({
    queryKey: ['sync', 'drift', alertId] as const,
    queryFn: () => apiClient.get<DriftAlert>(`/drift/alerts/${alertId}`),
  }),
};

// --- Drift Mutation Helpers ---

export function remediateDrift(alertId: string) {
  return apiClient.post<{ jobId: string }>(`/drift/alerts/${alertId}/remediate`, {
    confirm: true,
  });
}

export function acceptDrift(alertId: string) {
  return apiClient.post<void>(`/drift/alerts/${alertId}/accept`, {});
}

export function acknowledgeDrift(alertId: string) {
  return apiClient.post<void>(`/drift/alerts/${alertId}/acknowledge`, {});
}

export function unacknowledgeDrift(alertId: string) {
  return apiClient.post<void>(`/drift/alerts/${alertId}/unacknowledge`, {});
}

export const systemQueries = {
  search: (query: string) => ({
    queryKey: ['system', 'search', query] as const,
    queryFn: () =>
      apiClient.get<SearchResult[]>('/system/search', { params: { q: query } }),
  }),

  notifications: () => ({
    queryKey: ['system', 'notifications'] as const,
    queryFn: () => apiClient.get<NotificationItem[]>('/notifications/channels'),
  }),
};

export interface SearchResult {
  id: string;
  type: 'org' | 'site' | 'device';
  name: string;
  detail: string;
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

// --- Notification Channel Types ---

export interface NotificationChannel {
  id: string;
  type: 'email' | 'webhook' | 'slack';
  destination: string;
  subscriptions: ('drift_alert' | 'deploy_status' | 'approval_request' | 'export_ready')[];
  createdAt: string;
}

export type CreateChannelPayload = {
  type: NotificationChannel['type'];
  destination: string;
  subscriptions: NotificationChannel['subscriptions'];
};

// --- Notification Channel Queries & Mutations ---

export const channelQueries = {
  list: () => ({
    queryKey: ['notifications', 'channels', 'settings'] as const,
    queryFn: () => apiClient.get<NotificationChannel[]>('/notifications/channels/settings'),
  }),
};

export function createChannel(payload: CreateChannelPayload) {
  return apiClient.post<NotificationChannel>('/notifications/channels', payload);
}

export function updateChannel(channelId: string, payload: Partial<CreateChannelPayload>) {
  return apiClient.put<NotificationChannel>(`/notifications/channels/${channelId}`, payload);
}

export function deleteChannel(channelId: string) {
  return apiClient.delete<void>(`/notifications/channels/${channelId}`);
}

export function testChannel(channelId: string) {
  return apiClient.post<void>(`/notifications/channels/${channelId}/test`, {});
}
