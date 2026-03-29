import { apiClient } from './client';
import type { DiffChange, DiffSummary } from './client';

// --- Domain 2 Types ---

export interface ConfigRevision {
  id: string;
  entityType: string;
  entityId: string;
  capturedAt: string;
  actor: string;
  source: 'sync' | 'manual' | 'restore';
  contentHash: string;
  summary: string | null;
}

export interface ConfigDiff {
  leftRevisionId: string;
  rightRevisionId: string;
  changes: DiffChange[];
  summary: DiffSummary;
}

export interface TimeTravelSnapshot {
  queriedAt: string;
  actualAt: string;
  config: Record<string, unknown>;
  portStates: PortState[];
  clientCount: number;
  healthMetrics: Record<string, number>;
}

export interface PortState {
  portId: string;
  name: string;
  status: 'up' | 'down' | 'disabled';
  speed: string | null;
}

export interface ConfigBaseline {
  id: string;
  name: string;
  scopeType: 'site' | 'device_group';
  scopeId: string;
  content: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

// --- Query Factories ---

export type RevisionParams = {
  [key: string]: string | number | boolean | undefined;
  entity_type?: string;
  entity_id?: string;
  page?: number;
  per_page?: number;
};

export const configQueries = {
  revisions: (params: RevisionParams) => ({
    queryKey: ['config', 'revisions', params] as const,
    queryFn: () => apiClient.get<ConfigRevision[]>('/config/revisions', { params }),
  }),

  diff: (leftId: string, rightId: string) => ({
    queryKey: ['config', 'diff', leftId, rightId] as const,
    queryFn: () =>
      apiClient.post<ConfigDiff>('/config/diff', { left_id: leftId, right_id: rightId }),
  }),

  timeTravel: (deviceId: string, timestamp: string) => ({
    queryKey: ['config', 'time-travel', deviceId, timestamp] as const,
    queryFn: () =>
      apiClient.get<TimeTravelSnapshot>('/config/time-travel', {
        params: { device_id: deviceId, timestamp },
      }),
  }),

  baselines: () => ({
    queryKey: ['config', 'baselines'] as const,
    queryFn: () => apiClient.get<ConfigBaseline[]>('/config/baselines'),
  }),

  baseline: (baselineId: string) => ({
    queryKey: ['config', 'baselines', baselineId] as const,
    queryFn: () => apiClient.get<ConfigBaseline>(`/config/baselines/${baselineId}`),
  }),
};

// --- Baseline Mutation Helpers ---

export type CreateBaselinePayload = {
  name: string;
  scopeType: 'site' | 'device_group';
  scopeId: string;
};

export type UpdateBaselinePayload = {
  name?: string;
  scopeType?: 'site' | 'device_group';
  scopeId?: string;
};

export function createBaseline(payload: CreateBaselinePayload) {
  return apiClient.post<ConfigBaseline>('/config/baselines', payload);
}

export function updateBaseline(baselineId: string, payload: UpdateBaselinePayload) {
  return apiClient.put<ConfigBaseline>(`/config/baselines/${baselineId}`, payload);
}

export function deleteBaseline(baselineId: string) {
  return apiClient.delete<void>(`/config/baselines/${baselineId}`);
}
