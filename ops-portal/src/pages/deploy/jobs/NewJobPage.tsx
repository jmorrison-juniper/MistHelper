import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deployMutations, deployQueries } from '@/api/deploy';
import { syncQueries } from '@/api/sync';
import { DryRunPanel } from '@/features/deploy/jobs/DryRunPanel';

type WizardStep = 'targets' | 'payload' | 'schedule' | 'checks' | 'review';

const STEPS: { key: WizardStep; label: string }[] = [
  { key: 'targets', label: 'Select Targets' },
  { key: 'payload', label: 'Change Payload' },
  { key: 'schedule', label: 'Schedule' },
  { key: 'checks', label: 'Pre/Post Checks' },
  { key: 'review', label: 'Review & Submit' },
];

interface JobDraft {
  name: string;
  targetDevices: string[];
  changePayload: string;
  scheduledAt: string;
  scheduledTz: string;
  preChecks: string;
  postChecks: string;
  autoRollback: boolean;
  templateId: string;
}

const INITIAL_DRAFT: JobDraft = {
  name: '',
  targetDevices: [],
  changePayload: '{}',
  scheduledAt: '',
  scheduledTz: Intl.DateTimeFormat().resolvedOptions().timeZone,
  preChecks: '[]',
  postChecks: '[]',
  autoRollback: true,
  templateId: '',
};

export default function NewJobPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [step, setStep] = useState<WizardStep>('targets');
  const [draft, setDraft] = useState<JobDraft>(INITIAL_DRAFT);
  const [deviceSearch, setDeviceSearch] = useState('');

  const devicesQuery = useQuery({
    ...syncQueries.devices(deviceSearch || ''),
    enabled: step === 'targets',
  });

  const templatesQuery = useQuery({
    ...deployQueries.templates(),
    enabled: step === 'payload',
    select: (response) => response.data,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      deployMutations.createJob({
        name: draft.name,
        targetDevices: draft.targetDevices,
        changePayload: JSON.parse(draft.changePayload),
        scheduledAt: draft.scheduledAt || null,
        scheduledTz: draft.scheduledTz,
        preChecks: JSON.parse(draft.preChecks),
        postChecks: JSON.parse(draft.postChecks),
        autoRollback: draft.autoRollback,
      }),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['deploy', 'jobs'] });
      navigate(`/deploy/jobs/${response.data.id}`);
    },
  });

  const stepIndex = STEPS.findIndex((s) => s.key === step);

  function goNext() {
    if (stepIndex < STEPS.length - 1) setStep(STEPS[stepIndex + 1].key);
  }

  function goBack() {
    if (stepIndex > 0) setStep(STEPS[stepIndex - 1].key);
  }

  function toggleDevice(deviceId: string) {
    setDraft((prev) => ({
      ...prev,
      targetDevices: prev.targetDevices.includes(deviceId)
        ? prev.targetDevices.filter((id) => id !== deviceId)
        : [...prev.targetDevices, deviceId],
    }));
  }

  function applyTemplate(templateId: string) {
    const template = templatesQuery.data?.find((t) => t.id === templateId);
    if (template) {
      setDraft((prev) => ({
        ...prev,
        templateId,
        changePayload: JSON.stringify(template.payload, null, 2),
      }));
    }
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-bold text-text-primary">New Deployment Job</h1>

      <nav className="flex gap-1" aria-label="Wizard steps">
        {STEPS.map((s, index) => (
          <button
            key={s.key}
            type="button"
            onClick={() => setStep(s.key)}
            className={`px-3 py-1.5 text-sm rounded ${index === stepIndex ? 'bg-brand-600 text-white' : 'bg-surface-secondary text-text-secondary'}`}
          >
            {index + 1}. {s.label}
          </button>
        ))}
      </nav>

      <div className="bg-surface-primary rounded-lg shadow p-6">
        {step === 'targets' && (
          <TargetsStep
            draft={draft}
            setDraft={setDraft}
            deviceSearch={deviceSearch}
            setDeviceSearch={setDeviceSearch}
            devices={devicesQuery.data?.data ?? []}
            toggleDevice={toggleDevice}
          />
        )}

        {step === 'payload' && (
          <PayloadStep
            draft={draft}
            setDraft={setDraft}
            templates={templatesQuery.data ?? []}
            applyTemplate={applyTemplate}
          />
        )}

        {step === 'schedule' && <ScheduleStep draft={draft} setDraft={setDraft} />}
        {step === 'checks' && <ChecksStep draft={draft} setDraft={setDraft} />}
        {step === 'review' && <ReviewStep draft={draft} />}
      </div>

      <div className="flex items-center justify-between">
        <button type="button" onClick={goBack} disabled={stepIndex <= 0}
          className="px-4 py-2 text-sm border border-border-default rounded disabled:opacity-50">
          Back
        </button>
        {step === 'review' ? (
          <button type="button" onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending}
            className="px-4 py-2 text-sm bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50">
            {createMutation.isPending ? 'Creating...' : 'Submit Job'}
          </button>
        ) : (
          <button type="button" onClick={goNext}
            className="px-4 py-2 text-sm bg-brand-600 text-white rounded hover:bg-brand-700">
            Next
          </button>
        )}
      </div>

      {createMutation.isError && (
        <div className="text-sm text-status-error">
          Failed to create job: {createMutation.error instanceof Error ? createMutation.error.message : 'Unknown error'}
        </div>
      )}
    </div>
  );
}

function TargetsStep({ draft, setDraft, deviceSearch, setDeviceSearch, devices, toggleDevice }: {
  draft: JobDraft;
  setDraft: React.Dispatch<React.SetStateAction<JobDraft>>;
  deviceSearch: string;
  setDeviceSearch: (value: string) => void;
  devices: { id: string; name: string; type: string }[];
  toggleDevice: (id: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="job-name" className="block text-sm font-medium text-text-primary mb-1">Job Name</label>
        <input id="job-name" type="text" value={draft.name}
          onChange={(event) => setDraft((prev) => ({ ...prev, name: event.target.value }))}
          className="w-full border border-border-default rounded px-3 py-2 text-sm bg-surface-primary text-text-primary"
          placeholder="e.g. AP firmware upgrade - Building A" />
      </div>
      <div>
        <label htmlFor="device-search" className="block text-sm font-medium text-text-primary mb-1">Search Devices</label>
        <input id="device-search" type="search" value={deviceSearch}
          onChange={(event) => setDeviceSearch(event.target.value)}
          className="w-full border border-border-default rounded px-3 py-2 text-sm bg-surface-primary text-text-primary"
          placeholder="Search by name or MAC..." />
      </div>
      <div className="text-sm text-text-secondary">{draft.targetDevices.length} device(s) selected</div>
      <div className="max-h-64 overflow-y-auto border border-border-default rounded">
        {devices.map((device) => (
          <label key={device.id} className="flex items-center gap-2 px-3 py-2 hover:bg-surface-secondary cursor-pointer">
            <input type="checkbox" checked={draft.targetDevices.includes(device.id)} onChange={() => toggleDevice(device.id)} />
            <span className="text-sm text-text-primary">{device.name}</span>
            <span className="text-xs text-text-muted ml-auto">{device.type}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function PayloadStep({ draft, setDraft, templates, applyTemplate }: {
  draft: JobDraft;
  setDraft: React.Dispatch<React.SetStateAction<JobDraft>>;
  templates: { id: string; name: string; description: string }[];
  applyTemplate: (id: string) => void;
}) {
  return (
    <div className="space-y-4">
      {templates.length > 0 && (
        <div>
          <label htmlFor="template-select" className="block text-sm font-medium text-text-primary mb-1">Use Template</label>
          <select id="template-select" value={draft.templateId}
            onChange={(event) => applyTemplate(event.target.value)}
            className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary">
            <option value="">Select a template...</option>
            {templates.map((tpl) => <option key={tpl.id} value={tpl.id}>{tpl.name}</option>)}
          </select>
        </div>
      )}
      <div>
        <label htmlFor="payload-editor" className="block text-sm font-medium text-text-primary mb-1">Change Payload (JSON)</label>
        <textarea id="payload-editor" rows={12} value={draft.changePayload}
          onChange={(event) => setDraft((prev) => ({ ...prev, changePayload: event.target.value }))}
          className="w-full border border-border-default rounded px-3 py-2 text-sm font-mono bg-surface-primary text-text-primary" />
      </div>
      <DryRunPanel changePayload={draft.changePayload} targetDevices={draft.targetDevices} />
    </div>
  );
}

function ScheduleStep({ draft, setDraft }: {
  draft: JobDraft;
  setDraft: React.Dispatch<React.SetStateAction<JobDraft>>;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="schedule-time" className="block text-sm font-medium text-text-primary mb-1">Schedule Date/Time (leave empty for immediate)</label>
        <input id="schedule-time" type="datetime-local" value={draft.scheduledAt}
          onChange={(event) => setDraft((prev) => ({ ...prev, scheduledAt: event.target.value }))}
          className="border border-border-default rounded px-3 py-2 text-sm bg-surface-primary text-text-primary" />
      </div>
      <div>
        <label htmlFor="timezone" className="block text-sm font-medium text-text-primary mb-1">Timezone (IANA)</label>
        <input id="timezone" type="text" value={draft.scheduledTz}
          onChange={(event) => setDraft((prev) => ({ ...prev, scheduledTz: event.target.value }))}
          className="border border-border-default rounded px-3 py-2 text-sm bg-surface-primary text-text-primary"
          placeholder="America/New_York" />
      </div>
    </div>
  );
}

function ChecksStep({ draft, setDraft }: {
  draft: JobDraft;
  setDraft: React.Dispatch<React.SetStateAction<JobDraft>>;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="pre-checks" className="block text-sm font-medium text-text-primary mb-1">Pre-Checks (JSON array)</label>
        <textarea id="pre-checks" rows={4} value={draft.preChecks}
          onChange={(event) => setDraft((prev) => ({ ...prev, preChecks: event.target.value }))}
          className="w-full border border-border-default rounded px-3 py-2 text-sm font-mono bg-surface-primary text-text-primary" />
      </div>
      <div>
        <label htmlFor="post-checks" className="block text-sm font-medium text-text-primary mb-1">Post-Checks (JSON array)</label>
        <textarea id="post-checks" rows={4} value={draft.postChecks}
          onChange={(event) => setDraft((prev) => ({ ...prev, postChecks: event.target.value }))}
          className="w-full border border-border-default rounded px-3 py-2 text-sm font-mono bg-surface-primary text-text-primary" />
      </div>
      <label className="flex items-center gap-2">
        <input type="checkbox" checked={draft.autoRollback}
          onChange={(event) => setDraft((prev) => ({ ...prev, autoRollback: event.target.checked }))} />
        <span className="text-sm text-text-primary">Enable auto-rollback on post-check failure</span>
      </label>
    </div>
  );
}

function ReviewStep({ draft }: { draft: JobDraft }) {
  return (
    <div className="space-y-3 text-sm">
      <div><strong className="text-text-primary">Name:</strong> <span className="text-text-secondary">{draft.name || '(unnamed)'}</span></div>
      <div><strong className="text-text-primary">Targets:</strong> <span className="text-text-secondary">{draft.targetDevices.length} device(s)</span></div>
      <div><strong className="text-text-primary">Schedule:</strong> <span className="text-text-secondary">{draft.scheduledAt ? `${draft.scheduledAt} (${draft.scheduledTz})` : 'Immediate'}</span></div>
      <div><strong className="text-text-primary">Auto-Rollback:</strong> <span className="text-text-secondary">{draft.autoRollback ? 'Enabled' : 'Disabled'}</span></div>
      <div>
        <strong className="text-text-primary">Change Payload:</strong>
        <pre className="bg-surface-secondary rounded p-2 mt-1 text-xs overflow-x-auto">{draft.changePayload}</pre>
      </div>
    </div>
  );
}
