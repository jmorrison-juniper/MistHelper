(function() { // Add validated paste delivery behavior.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    class PasteDelivery { // Own paste size checks and xterm delivery.
        constructor(controller) { // Store the active terminal controller.
            this.controller = controller; // Use xterm and the ordered input queue.
            this.active = false; // Start outside xterm paste emission.
        }

        send(text) { // Send confirmed paste text through xterm.
            if (this.controller.inputBlocked()) return; // Stop when the session cannot accept input.
            if (!text) { this.controller.focusTerminal(); return; } // Return focus for an empty manual paste.
            var total = new TextEncoder().encode(text).length; // Measure backend bytes.
            if (total > terminal.constants.pasteLimit) { this.controller.display.toast('Paste refused. The limit is 256 KiB.'); return; } // Refuse oversized paste text.
            this.active = true; // Mark xterm output as paste data.
            this.controller.pasteProgress = total > terminal.constants.pasteProgressLimit ? { sent: 0, total: total } : null; // Track only large paste operations.
            this.controller.term.paste(text); // Let xterm apply bracketed paste behavior.
            window.setTimeout(function() { this.active = false; }.bind(this), 0); // Leave paste mode after xterm emits data.
            this.controller.focusTerminal(); // Return focus after paste starts.
        }

        consume(data) { // Queue bytes that xterm emits for paste.
            this.controller.sendQueue.enqueueText(data, { paste: true, progress: this.controller.pasteProgress }); // Preserve paste metadata across chunks.
        }
    }

    terminal.Internal.PasteDelivery = PasteDelivery; // Publish paste delivery for flow composition.
})();
