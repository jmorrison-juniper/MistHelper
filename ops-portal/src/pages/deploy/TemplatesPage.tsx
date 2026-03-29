import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router';
import {
  deployQueries,
  deployMutations,
} from '@/api/deploy';
import type { ChangeTemplate, TemplateParam } from '@/api/deploy';
import ConfirmationDialog from '@/components/ConfirmationDialog';

type FormMode =
  | { kind: 'closed' }
  | { kind: 'create' }
  | { kind: 'edit'; template: ChangeTemplate };

const EMPTY_PARAM: TemplateParam = {
  name: '',
  label: '',
  type: 'string',
  required: false,
  options: null,
  defaultValue: null,
};

export default function TemplatesPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [formMode, setFormMode] = useState<FormMode>({ kind: 'closed' });
  const [deleteTarget, setDeleteTarget] = useState<ChangeTemplate | null>(null);

  const templatesQuery = useQuery({
    ...deployQueries.templates(),
    select: (response) => response.data,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deployMutations.deleteTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deploy', 'templates'] });
      setDeleteTarget(null);
    },
  });

  const templates = templatesQuery.data ?? [];

  function handleUseTemplate(template: ChangeTemplate) {
    const params = new URLSearchParams({ templateId: template.id });
    navigate(`/deploy/jobs/new?${params.toString()}`);
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Change Templates</h1>
        <button onClick={() => setFormMode({ kind: 'create' })}
          className="px-3 py-1.5 text-sm font-medium bg-brand-600 text-white rounded hover:bg-brand-700">
          New Template
        </button>
      </div>

      {templatesQuery.isLoading && <p className="text-sm text-text-muted">Loading templates...</p>}

      {!templatesQuery.isLoading && templates.length === 0 && (
        <p className="text-sm text-text-muted py-8 text-center">No change templates defined</p>
      )}

      {templates.length > 0 && (
        <div className="space-y-3">
          {templates.map((template) => (
            <div key={template.id}
              className="border border-border-default rounded-lg p-4 bg-surface-primary hover:bg-surface-secondary">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-text-primary">{template.name}</h3>
                  <p className="text-sm text-text-secondary mt-0.5">{template.description}</p>
                  <p className="text-xs text-text-muted mt-1">
                    {template.parameters.length} parameter{template.parameters.length !== 1 ? 's' : ''}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleUseTemplate(template)}
                    className="px-3 py-1 text-xs font-medium bg-brand-600 text-white rounded hover:bg-brand-700">
                    Use
                  </button>
                  <button onClick={() => setFormMode({ kind: 'edit', template })}
                    className="px-3 py-1 text-xs text-brand-600 border border-brand-600 rounded hover:bg-brand-50">
                    Edit
                  </button>
                  <button onClick={() => setDeleteTarget(template)}
                    className="px-3 py-1 text-xs text-status-error border border-status-error rounded hover:bg-red-50">
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {formMode.kind !== 'closed' && (
        <TemplateForm mode={formMode} onClose={() => setFormMode({ kind: 'closed' })} />
      )}

      {deleteTarget && (
        <ConfirmationDialog
          title="Delete Template"
          description={`Delete "${deleteTarget.name}"?`}
          impact="This template will no longer be available for new deployments."
          confirmKeyword={null}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}

function TemplateForm({ mode, onClose }: { mode: Exclude<FormMode, { kind: 'closed' }>; onClose: () => void }) {
  const queryClient = useQueryClient();
  const isEdit = mode.kind === 'edit';
  const initial = isEdit ? mode.template : null;

  const [name, setName] = useState(initial?.name ?? '');
  const [description, setDescription] = useState(initial?.description ?? '');
  const [parameters, setParameters] = useState<TemplateParam[]>(
    initial?.parameters ?? [{ ...EMPTY_PARAM }]
  );

  const createMutation = useMutation({
    mutationFn: (body: Omit<ChangeTemplate, 'id'>) => deployMutations.createTemplate(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deploy', 'templates'] });
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (body: Partial<Omit<ChangeTemplate, 'id'>>) =>
      deployMutations.updateTemplate(initial!.id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deploy', 'templates'] });
      onClose();
    },
  });

  const isPending = createMutation.isPending || updateMutation.isPending;

  function updateParam(index: number, field: keyof TemplateParam, value: unknown) {
    setParameters((prev) => prev.map((p, i) => (i === index ? { ...p, [field]: value } : p)));
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const body = { name, description, parameters, payload: initial?.payload ?? {} };
    if (isEdit) {
      updateMutation.mutate(body);
    } else {
      createMutation.mutate(body);
    }
  }

  return (
    <div className="bg-surface-primary border border-border-default rounded-lg p-4 space-y-3">
      <h2 className="text-lg font-semibold text-text-primary">
        {isEdit ? 'Edit Template' : 'New Template'}
      </h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor="tpl-name" className="block text-sm text-text-secondary mb-1">Name</label>
          <input id="tpl-name" type="text" required value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full border border-border-default rounded px-3 py-1.5 text-sm bg-surface-primary text-text-primary" />
        </div>
        <div>
          <label htmlFor="tpl-desc" className="block text-sm text-text-secondary mb-1">Description</label>
          <textarea id="tpl-desc" required value={description}
            onChange={(e) => setDescription(e.target.value)} rows={2}
            className="w-full border border-border-default rounded px-3 py-1.5 text-sm bg-surface-primary text-text-primary" />
        </div>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-text-secondary">Parameters</legend>
          {parameters.map((param, index) => (
            <ParamRow key={index} param={param} index={index}
              onChange={updateParam}
              onRemove={() => setParameters((prev) => prev.filter((_, i) => i !== index))} />
          ))}
          <button type="button"
            onClick={() => setParameters((prev) => [...prev, { ...EMPTY_PARAM }])}
            className="text-xs text-brand-600 hover:underline">
            + Add parameter
          </button>
        </fieldset>

        <div className="flex gap-2 pt-1">
          <button type="submit" disabled={isPending}
            className="px-4 py-1.5 text-sm font-medium bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50">
            {isEdit ? 'Update' : 'Create'}
          </button>
          <button type="button" onClick={onClose}
            className="px-4 py-1.5 text-sm text-text-secondary border border-border-default rounded hover:bg-surface-secondary">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

function ParamRow({
  param,
  index,
  onChange,
  onRemove,
}: {
  param: TemplateParam;
  index: number;
  onChange: (index: number, field: keyof TemplateParam, value: unknown) => void;
  onRemove: () => void;
}) {
  return (
    <div className="grid grid-cols-5 gap-2 items-end">
      <div>
        <label className="block text-xs text-text-muted">Name</label>
        <input type="text" value={param.name} title="Parameter name"
          onChange={(e) => onChange(index, 'name', e.target.value)}
          className="w-full border border-border-default rounded px-2 py-1 text-xs bg-surface-primary text-text-primary" />
      </div>
      <div>
        <label className="block text-xs text-text-muted">Label</label>
        <input type="text" value={param.label} title="Parameter label"
          onChange={(e) => onChange(index, 'label', e.target.value)}
          className="w-full border border-border-default rounded px-2 py-1 text-xs bg-surface-primary text-text-primary" />
      </div>
      <div>
        <label className="block text-xs text-text-muted">Type</label>
        <select value={param.type} title="Parameter type"
          onChange={(e) => onChange(index, 'type', e.target.value)}
          className="w-full border border-border-default rounded px-2 py-1 text-xs bg-surface-primary text-text-primary">
          <option value="string">String</option>
          <option value="number">Number</option>
          <option value="boolean">Boolean</option>
          <option value="select">Select</option>
        </select>
      </div>
      <div className="flex items-center gap-1">
        <input type="checkbox" checked={param.required} title="Required"
          onChange={(e) => onChange(index, 'required', e.target.checked)} />
        <span className="text-xs text-text-muted">Required</span>
      </div>
      <button type="button" onClick={onRemove}
        className="text-xs text-status-error hover:underline justify-self-start">
        Remove
      </button>
    </div>
  );
}
