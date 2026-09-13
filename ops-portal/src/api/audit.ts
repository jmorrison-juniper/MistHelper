import { apiClient } from './client';

// --- Domain 4 Types ---

export interface AuditRecord {
  id: string;
  entityType: string;
  entityId: string;
  entityName: string;
  changeType: 'create' | 'update' | 'delete';
  actor: string;
  timestamp: string;
  oldValues: Record<string, unknown> | null;
  newValues: Record<string, unknown> | null;
  summary: string;
  revisionId: string | null;
  jobId: string | null;
}

export interface AuditExport {
  id: string;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  format: 'csv' | 'json';
  recordCount: number;
  downloadUrl: string | null;
  createdAt: string;
}

export type AuditFilters = {
  entity_type?: string;
  actor?: string;
  change_type?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  per_page?: number;
  [key: string]: string | number | undefined;
};

export interface IncidentCorrelation {
  id: string;
  auditRecordId: string;
  incidentType: 'alarm' | 'sle_degradation';
  incidentId: string;
  confidenceScore: number;
  detectionMethod: string;
  summary: string;
  timestamp: string;
}

export interface CompliancePack {
  id: string;
  framework: 'SOX' | 'PCI-DSS' | 'SOC2';
  status: 'pending' | 'generating' | 'completed' | 'failed';
  startDate: string;
  endDate: string;
  downloadUrl: string | null;
  createdAt: string;
}

// --- Query Factories ---

export const auditQueries = {
  records: (filters?: AuditFilters) => ({
    queryKey: ['audit', 'records', filters] as const,
    queryFn: () => apiClient.get<AuditRecord[]>('/audit/records', { params: filters }),
  }),

  record: (id: string) => ({
    queryKey: ['audit', 'records', id] as const,
    queryFn: () => apiClient.get<AuditRecord>(`/audit/records/${encodeURIComponent(id)}`),
  }),

  exports: () => ({
    queryKey: ['audit', 'exports'] as const,
    queryFn: () => apiClient.get<AuditExport[]>('/audit/exports'),
  }),

  exportStatus: (id: string) => ({
    queryKey: ['audit', 'exports', id] as const,
    queryFn: () => apiClient.get<AuditExport>(`/audit/exports/${encodeURIComponent(id)}`),
  }),

  correlations: (filters?: AuditFilters) => ({
    queryKey: ['audit', 'correlations', filters] as const,
    queryFn: () => apiClient.get<IncidentCorrelation[]>('/audit/correlations', { params: filters }),
  }),

  packs: () => ({
    queryKey: ['audit', 'packs'] as const,
    queryFn: () => apiClient.get<CompliancePack[]>('/audit/compliance/packs'),
  }),

  packStatus: (id: string) => ({
    queryKey: ['audit', 'packs', id] as const,
    queryFn: () => apiClient.get<CompliancePack>(`/audit/compliance/packs/${encodeURIComponent(id)}`),
  }),
};

// --- Mutations ---

export const auditMutations = {
  createExport: (data: { filters: AuditFilters; format: 'csv' | 'json' }) =>
    apiClient.post<AuditExport>('/audit/exports', data),

  createPack: (data: { framework: 'SOX' | 'PCI-DSS' | 'SOC2'; startDate: string; endDate: string }) =>
    apiClient.post<CompliancePack>('/audit/compliance/packs', data),
};
