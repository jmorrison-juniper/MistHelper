import { Fragment, useState, useRef, useEffect } from 'react';
import { Dialog, DialogPanel, DialogTitle } from '@headlessui/react';

interface ConfirmationDialogProps {
  title: string;
  description: string;
  impact: string;
  confirmKeyword: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmationDialog({
  title,
  description,
  impact,
  confirmKeyword,
  onConfirm,
  onCancel,
}: ConfirmationDialogProps) {
  const [keyword, setKeyword] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const canConfirm = confirmKeyword ? keyword === confirmKeyword : true;

  useEffect(() => {
    if (confirmKeyword && inputRef.current) {
      inputRef.current.focus();
    }
  }, [confirmKeyword]);

  return (
    <Dialog open onClose={onCancel} as={Fragment}>
      <div className="fixed inset-0 bg-black/50 z-40" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <DialogPanel className="bg-surface-primary rounded-lg shadow-xl max-w-md w-full p-6" aria-describedby="confirm-description confirm-impact">
          <DialogTitle className="text-lg font-semibold text-text-primary">
            {title}
          </DialogTitle>

          <p id="confirm-description" className="mt-2 text-sm text-text-secondary">{description}</p>

          <div id="confirm-impact" role="alert" className="mt-3 px-3 py-2 bg-status-warning/10 border border-status-warning/30 rounded text-sm text-text-primary">
            {impact}
          </div>

          {confirmKeyword && (
            <div className="mt-4">
              <label htmlFor="confirm-keyword" className="block text-sm font-medium text-text-secondary mb-1">
                Type <span className="font-mono font-bold">{confirmKeyword}</span> to confirm
              </label>
              <input
                ref={inputRef}
                id="confirm-keyword"
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="w-full border border-border-default rounded px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                autoComplete="off"
              />
            </div>
          )}

          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-text-secondary bg-surface-secondary border border-border-default rounded hover:bg-surface-tertiary"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={onConfirm}
              disabled={!canConfirm}
              className="px-4 py-2 text-sm font-medium text-white bg-status-error rounded hover:bg-status-error/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Confirm
            </button>
          </div>
        </DialogPanel>
      </div>
    </Dialog>
  );
}
