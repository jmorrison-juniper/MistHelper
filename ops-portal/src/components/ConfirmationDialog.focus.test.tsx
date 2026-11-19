// Regression test for issue #4737. The keyword field must take focus when the
// first confirmation dialog of a module instance opens.
//
// Headless UI renders the children of the first portal in a module instance
// after an extra render pass. Later portals render at once, so the main dialog
// test file cannot reproduce the defect. This file keeps one test, which is the
// first dialog render in its module instance.

import { act, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import ConfirmationDialog from '@/components/ConfirmationDialog';

/** Wait for two animation frames. The focus trap moves focus after the second frame. */
async function settleFocusTrap() {
  await act(async () => {
    await new Promise<void>((resolve) => {
      requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
    });
  });
}

describe('ConfirmationDialog initial focus', () => {
  it('focuses the keyword field when the first dialog opens', async () => {
    render(
      <ConfirmationDialog
        title="Start the firmware upgrade"
        description="This action upgrades every device in the wave."
        impact="42 devices restart and lose service for about 5 minutes."
        confirmKeyword="UPGRADE"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    await settleFocusTrap();
    expect(document.activeElement).toBe(screen.getByLabelText(/to confirm/i));
  });
});
