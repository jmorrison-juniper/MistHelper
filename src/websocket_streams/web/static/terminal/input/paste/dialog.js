(function() { // Add paste confirmation dialog behavior.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    class PasteDialog { // Own pending paste confirmation state.
        constructor(flow) { // Store the parent paste flow.
            this.flow = flow; // Continue through the same validation path.
            this.pendingText = ''; // Start with no pending clipboard text.
            this.manualMode = false; // Start outside manual paste mode.
        }

        open(text, manual) { // Open review or manual paste mode.
            this.pendingText = text || ''; // Keep review text until confirmation.
            this.manualMode = manual; // Select the dialog input source.
            this.flow.controller.panel.showPasteDialog(text || '', manual); // Display the matching dialog controls.
        }

        confirm() { // Confirm the pending paste.
            var text = this.manualMode ? this.flow.controller.elements.pasteInput.value : this.pendingText; // Read the selected input source.
            this.reset(); // Clear pending state before delivery.
            this.flow.delivery.send(text); // Deliver without a second confirmation.
        }

        cancel() { // Cancel and discard pending paste.
            this.reset(); // Clear pending state and close the dialog.
            this.flow.controller.focusTerminal(); // Return focus after cancellation.
        }

        reset() { // Clear dialog state for close or session switch.
            this.pendingText = ''; // Prevent text from reaching a later session.
            this.manualMode = false; // Leave manual mode.
            this.flow.controller.panel.hidePasteDialog(); // Close and clear dialog controls.
        }
    }

    terminal.Internal.PasteDialog = PasteDialog; // Publish dialog behavior for paste flow composition.
})();
