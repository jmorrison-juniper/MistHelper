import { apiClient } from './client';

// --- Domain 3 Types ---

export type JobStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'scheduled'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'rolled_back';

export interface CheckConfig {
  type: string;
  threshold: number | null;
  operator: 'gte' | 'lte' | 'eq';
}

export interface DeployJob {
  id: string;
  name: string;
  status: JobStatus;
  scheduledAt: string | null;
  scheduledTz: string;
  targetDevices: string[];
  changePayload: Record<string, unknown>;
  preChecks: CheckConfig[];
  postChecks: CheckConfig[];
  autoRollback: boolean;
  requiresApproval: boolean;
  approvedBy: string | null;
  createdBy: string;
  createdAt: string;
}

export interface DryRunResult {
  riskScore: number;
  riskLevel: 'low' | 'medium' | 'high';
  blastRadius: BlastRadius;
  warnings: string[];
  policyViolations: string[];
}

export interface BlastRadius {
  deviceCount: number;
  siteCount: number;
  estimatedClients: number;
}

export interface ChangeTemplate {
  id: string;
  name: string;
  description: string;
  parameters: TemplateParam[];
  payload: Record<string, unknown>;
}

export interface TemplateParam {
  name: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'select';
  required: boolean;
  options: string[] | null;
  defaultValue: unknown | null;
}

export interface GoldenImage {
  id: string;
  version: string;
  deviceType: 'ap' | 'switch' | 'gateway';
  models: string[];
  status: 'pending' | 'approved' | 'retired';
  approvedBy: string | null;
  registeredAt: string;
}

export type RolloutStatus = 'draft' | 'active' | 'paused' | 'completed' | 'cancelled';

export interface RolloutWave {
  waveNumber: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'rolled_back';
  targets: string[];
  completedCount: number;
  failedCount: number;
  healthGatePassed: boolean | null;
}

export interface HealthGate {
  minClientPercent: number;
  maxAlarmCount: number;
  waitMinutes: number;
}

export interface Rollout {
  id: string;
  name: string;
  status: RolloutStatus;
  goldenImageId: string | null;
  promotionMode: 'automatic' | 'manual';
  waves: RolloutWave[];
  healthGates: HealthGate;
  createdBy: string;
  createdAt: string;
}

// --- Query Factories ---

export type JobListParams = {
  [key: string]: string | number | boolean | undefined;
  status?: string;
  page?: number;
  per_page?: number;
};

export const deployQueries = {
  jobs: (params?: JobListParams) => ({
    queryKey: ['deploy', 'jobs', params] as const,
    queryFn: () => apiClient.get<DeployJob[]>('/deploy/jobs', { params }),
  }),

  job: (jobId: string) => ({
    queryKey: ['deploy', 'jobs', jobId] as const,
    queryFn: () => apiClient.get<DeployJob>(`/deploy/jobs/${jobId}`),
  }),

  rollouts: () => ({
    queryKey: ['deploy', 'rollouts'] as const,
    queryFn: () => apiClient.get<Rollout[]>('/deploy/rollouts'),
  }),

  rollout: (rolloutId: string) => ({
    queryKey: ['deploy', 'rollouts', rolloutId] as const,
    queryFn: () => apiClient.get<Rollout>(`/deploy/rollouts/${rolloutId}`),
  }),

  templates: () => ({
    queryKey: ['deploy', 'templates'] as const,
    queryFn: () => apiClient.get<ChangeTemplate[]>('/deploy/templates'),
  }),

  goldenImages: () => ({
    queryKey: ['deploy', 'golden-images'] as const,
    queryFn: () => apiClient.get<GoldenImage[]>('/deploy/golden-images'),
  }),
};

// --- Mutations ---

export const deployMutations = {
  createJob: (body: Partial<DeployJob>) =>
    apiClient.post<DeployJob>('/deploy/jobs', body),

  approveJob: (jobId: string, reason?: string) =>
    apiClient.post(`/deploy/jobs/${jobId}/approve`, { reason }),

  rejectJob: (jobId: string, reason: string) =>
    apiClient.post(`/deploy/jobs/${jobId}/reject`, { reason }),

  cancelJob: (jobId: string) =>
    apiClient.delete(`/deploy/jobs/${jobId}`),

  dryRun: (body: { target_devices: string[]; change_payload: Record<string, unknown> }) =>
    apiClient.post<DryRunResult>('/deploy/dry-run', body),

  installFromRevision: (body: { revision_id: string; target_devices: string[]; confirm: boolean }) =>
    apiClient.post<DeployJob>('/config/install-from-revision', body),

  createRollout: (body: { name: string; goldenImageId: string; waves: Array<{ waveNumber: number; deviceIds: string[] }>; healthGate: HealthGate; promotionMode: string }) =>
    apiClient.post<Rollout>('/deploy/rollouts', body),

  activateRollout: (rolloutId: string) =>
    apiClient.post(`/deploy/rollouts/${rolloutId}/activate`, { confirm: true }),

  pauseRollout: (rolloutId: string) =>
    apiClient.post(`/deploy/rollouts/${rolloutId}/pause`, {}),

  resumeRollout: (rolloutId: string) =>
    apiClient.post(`/deploy/rollouts/${rolloutId}/resume`, {}),

  rollbackWave: (rolloutId: string, waveNumber: number) =>
    apiClient.post(`/deploy/rollouts/${rolloutId}/waves/${waveNumber}/rollback`, { confirm: true }),

  // Template mutations
  createTemplate: (body: Omit<ChangeTemplate, 'id'>) =>
    apiClient.post<ChangeTemplate>('/deploy/templates', body),

  updateTemplate: (templateId: string, body: Partial<Omit<ChangeTemplate, 'id'>>) =>
    apiClient.put<ChangeTemplate>(`/deploy/templates/${templateId}`, body),

  deleteTemplate: (templateId: string) =>
    apiClient.delete(`/deploy/templates/${templateId}`),

  // Golden image mutations
  registerImage: (body: Omit<GoldenImage, 'id' | 'status' | 'approvedBy' | 'registeredAt'>) =>
    apiClient.post<GoldenImage>('/deploy/golden-images', body),

  approveImage: (imageId: string) =>
    apiClient.post(`/deploy/golden-images/${imageId}/approve`, {}),

  retireImage: (imageId: string) =>
    apiClient.post(`/deploy/golden-images/${imageId}/retire`, {}),
};
