// Tests for the confirmation dialog of the ops portal.
//
// This component is the safety gate for a destructive action. It asks the
// operator to type a keyword before the Confirm button becomes usable. A
// defect here lets an operator start a destructive job by accident, so this
// component is the right place for the first test of the application.
//
// Issue #1852 records that the project shipped no test at all.

import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';

import ConfirmationDialog from '@/components/ConfirmationDialog';

// The keyword that the tests type to unlock the Confirm button.
const KEYWORD = 'UPGRADE';

afterEach(() => {
  // Remove the rendered nodes, so one test cannot read another one's DOM.
  cleanup();
});

/** Render the dialog and return the two callback spies. */
function renderDialog(confirmKeyword: string | null) {
  // A spy records each call, so a test can prove the button fired the action.
  const onConfirm = vi.fn();
  const onCancel = vi.fn();
  render(
    <ConfirmationDialog
      title="Start the firmware upgrade"
      description="This action upgrades every device in the wave."
      impact="42 devices restart and lose service for about 5 minutes."
      confirmKeyword={confirmKeyword}
      onConfirm={onConfirm}
      onCancel={onCancel}
    />,
  );
  return { onConfirm, onCancel };
}

/** Return the Confirm button of the rendered dialog. */
function confirmButton(): HTMLButtonElement {
  // The accessible name is the one stable handle on this button.
  return screen.getByRole('button', { name: 'Confirm' }) as HTMLButtonElement;
}

describe('ConfirmationDialog keyword gate', () => {
  it('keeps the Confirm button locked until the operator types the keyword', () => {
    renderDialog(KEYWORD);
    // The gate must start closed, because an empty field is not a confirmation.
    expect(confirmButton().disabled).toBe(true);
  });

  it('keeps the Confirm button locked on a wrong keyword', () => {
    renderDialog(KEYWORD);
    // A near miss must not open the gate, so the check is an exact match.
    fireEvent.change(screen.getByLabelText(/to confirm/i), { target: { value: 'UPGRAD' } });
    expect(confirmButton().disabled).toBe(true);
  });

  it('keeps the Confirm button locked on a different case', () => {
    renderDialog(KEYWORD);
    // The match is case sensitive, so a lower case entry stays locked.
    fireEvent.change(screen.getByLabelText(/to confirm/i), { target: { value: 'upgrade' } });
    expect(confirmButton().disabled).toBe(true);
  });

  it('unlocks the Confirm button on the exact keyword', () => {
    renderDialog(KEYWORD);
    // The exact keyword is the one value that opens the gate.
    fireEvent.change(screen.getByLabelText(/to confirm/i), { target: { value: KEYWORD } });
    expect(confirmButton().disabled).toBe(false);
  });

  it('locks the Confirm button again when the operator clears the field', () => {
    renderDialog(KEYWORD);
    const field = screen.getByLabelText(/to confirm/i);
    // Open the gate first, so the test proves the gate can close again.
    fireEvent.change(field, { target: { value: KEYWORD } });
    fireEvent.change(field, { target: { value: '' } });
    expect(confirmButton().disabled).toBe(true);
  });

  it('unlocks the Confirm button at once when no keyword is required', () => {
    // A null keyword marks an action that needs no typed confirmation.
    renderDialog(null);
    expect(confirmButton().disabled).toBe(false);
  });

  it('shows no keyword field when no keyword is required', () => {
    renderDialog(null);
    // The field must be absent, so the dialog does not ask for a needless entry.
    expect(screen.queryByLabelText(/to confirm/i)).toBeNull();
  });
});

describe('ConfirmationDialog actions', () => {
  it('calls onConfirm after the operator types the keyword', () => {
    const { onConfirm } = renderDialog(KEYWORD);
    fireEvent.change(screen.getByLabelText(/to confirm/i), { target: { value: KEYWORD } });
    fireEvent.click(confirmButton());
    // One click must produce exactly one action, never two.
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('does not call onConfirm while the button is locked', () => {
    const { onConfirm } = renderDialog(KEYWORD);
    // A click on a disabled button must reach no handler at all.
    fireEvent.click(confirmButton());
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('calls onCancel when the operator picks Cancel', () => {
    const { onCancel, onConfirm } = renderDialog(KEYWORD);
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    // Cancel must stop the action, so the confirm path stays untouched.
    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onConfirm).not.toHaveBeenCalled();
  });
});

describe('ConfirmationDialog message', () => {
  it('shows the impact text in an alert region', () => {
    renderDialog(KEYWORD);
    // A screen reader must announce the impact, so the text carries a role.
    const alert = screen.getByRole('alert');
    expect(alert.textContent).toContain('42 devices restart');
  });

  it('shows the title and the description', () => {
    renderDialog(KEYWORD);
    // The operator reads both lines before the decision, so both must render.
    expect(screen.getByText('Start the firmware upgrade')).toBeTruthy();
    expect(screen.getByText(/upgrades every device in the wave/i)).toBeTruthy();
  });
});
