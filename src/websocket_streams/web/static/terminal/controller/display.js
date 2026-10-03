(function() { // Add terminal display and panel behavior.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    function errorMessage(answer) { // Convert backend codes into operator text.
        var messages = { bad_request: 'The portal refused the terminal request.', csrf_expired: 'The form token expired. Reload the page.', input_full: 'The terminal input queue is full.', network: 'The portal did not answer. Check the network, then try again.', not_found: 'The terminal session is no longer available.', not_open: 'The terminal session is not open.', not_terminal: 'This session has no terminal.', rate_limited: 'The terminal is receiving input too quickly.', read_only: 'This terminal is read-only.', too_large: 'The terminal input is too large.' }; // Define stable failure text.
        return messages[answer.code] || answer.error || 'The terminal request failed.'; // Prefer the most specific available message.
    }

    class TerminalDisplay { // Own footer, toast, and progress output.
        constructor(controller) { // Store the controller for page elements.
            this.controller = controller; // Use the active controller state.
        }

        status(text) { // Set the terminal footer.
            this.controller.elements.status.textContent = text || ''; // Clear old text when no status exists.
        }

        toast(text) { // Show a short local terminal message.
            this.controller.elements.toast.textContent = text || ''; // Replace the previous toast text.
            this.controller.elements.toast.classList.toggle('d-none', !text); // Hide an empty toast.
        }

        progress(sent, total) { // Show or hide large paste progress.
            var progress = this.controller.elements.progress; // Read the shared progress element.
            progress.max = total || 1; // Keep a valid maximum when progress resets.
            progress.value = sent || 0; // Show accepted paste bytes.
            progress.classList.toggle('d-none', !total); // Hide progress when no paste is active.
        }

        error(answer) { // Show one backend failure in the footer.
            this.status(errorMessage(answer)); // Use stable operator text for known codes.
        }
    }

    class TerminalPanel { // Own terminal panel and paste dialog visibility.
        constructor(controller) { // Store the controller for page state.
            this.controller = controller; // Use the active controller and its elements.
        }

        show(visible) { // Show or hide the terminal panel.
            this.controller.elements.panel.classList.toggle('d-none', !visible); // Apply the requested panel visibility.
            this.readOnly(); // Refresh controls for the current mode.
            this.controller.display.toast(''); // Clear stale local messages.
            this.controller.display.progress(0, 0); // Clear stale paste progress.
            this.hidePasteDialog(); // Close a dialog from the previous session.
        }

        readOnly() { // Apply controls for writable or read-only state.
            var blocked = this.controller.inputBlocked(); // Compute input state once.
            this.controller.elements.warning.textContent = this.controller.readOnly ? 'This view is read-only. The device sends the screen.' : 'Warning: Each command runs on the live device.'; // Explain the active mode.
            this.controller.elements.paste.disabled = blocked; // Disable toolbar paste when input is blocked.
            this.controller.elements.menuPaste.disabled = blocked; // Disable menu paste with the same state.
            this.controller.elements.menuPaste.classList.toggle('disabled', blocked); // Show the disabled menu state.
            this.controller.elements.menuPaste.setAttribute('aria-disabled', blocked ? 'true' : 'false'); // Expose the disabled state.
            this.controller.elements.screen.classList.toggle('ws-terminal-screen-fixed', this.controller.readOnly); // Use fixed screen styling for read-only output.
        }

        showPasteDialog(text, manual) { // Show paste review or manual paste input.
            var elements = this.controller.elements; // Use a short reference for dialog elements.
            var lines = text ? text.split(/\r\n|\r|\n/) : []; // Prepare the five-line preview.
            elements.pasteLines.textContent = manual ? 'Paste text into the field, then select Paste.' : 'Lines: ' + terminal.Internal.lineCount(text); // Explain the pending paste.
            elements.pastePreview.textContent = manual ? '' : lines.slice(0, 5).join('\n'); // Limit the preview to five lines.
            elements.pasteInput.value = manual ? '' : text; // Keep preview text for the confirmation path.
            elements.pasteInput.classList.toggle('d-none', !manual); // Show manual input only when required.
            if (elements.pasteInputLabel) elements.pasteInputLabel.classList.toggle('d-none', !manual); // Keep the label equal to input visibility.
            elements.dialog.classList.remove('d-none'); // Show the prepared dialog.
            elements.pasteCancel.focus(); // Focus Cancel to prevent accidental paste.
        }

        hidePasteDialog() { // Hide and clear paste dialog controls.
            var elements = this.controller.elements; // Use a short reference for dialog elements.
            elements.dialog.classList.add('d-none'); // Hide the dialog.
            elements.pasteInput.value = ''; // Remove text from the closed dialog.
            if (elements.pasteInputLabel) elements.pasteInputLabel.classList.add('d-none'); // Hide the manual input label.
        }
    }

    terminal.Internal.TerminalDisplay = TerminalDisplay; // Publish display behavior for controller composition.
    terminal.Internal.TerminalPanel = TerminalPanel; // Publish panel behavior for controller composition.
    terminal.Internal.errorMessage = errorMessage; // Share failure formatting with tests and readers.
})();
