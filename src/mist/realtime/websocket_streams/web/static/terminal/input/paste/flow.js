(function() { // Add clipboard paste review and native paste handling.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    class PasteFlow { // Own all paste entry paths.
        constructor(controller) { // Compose paste dialog and delivery leaves.
            this.controller = controller; // Use the active terminal controller.
            this.delivery = new terminal.Internal.PasteDelivery(controller); // Deliver validated text through xterm.
            this.dialog = new terminal.Internal.PasteDialog(this); // Hold confirmation state.
        }

        bind() { // Attach native paste and dialog controls once.
            this.controller.elements.screen.addEventListener('paste', this.nativePaste.bind(this), true); // Capture paste before xterm duplicates it.
            this.controller.elements.pasteSend.addEventListener('click', this.dialog.confirm.bind(this.dialog)); // Confirm pending paste.
            this.controller.elements.pasteCancel.addEventListener('click', this.dialog.cancel.bind(this.dialog)); // Cancel pending paste.
            this.controller.elements.dialog.addEventListener('keydown', function(event) { if (event.key === 'Escape') this.dialog.cancel(); }.bind(this)); // Let Escape cancel safely.
        }

        pasteFromClipboard() { // Read text from the browser clipboard.
            if (this.controller.inputBlocked()) return; // Stop when input is blocked.
            if (window.isSecureContext && navigator.clipboard && navigator.clipboard.readText) { // Use direct clipboard read when available.
                navigator.clipboard.readText().then(this.handleText.bind(this)).catch(function() { this.dialog.open('', true); }.bind(this)); // Use manual input after permission failure.
                return; // Stop after the asynchronous read starts.
            }
            this.dialog.open('', true); // Use manual paste on unsupported pages.
        }

        handleText(text) { // Validate clipboard text before delivery.
            if (this.controller.inputBlocked() || !text) return; // Reject blocked or empty paste input.
            if (new TextEncoder().encode(text).length > terminal.constants.pasteLimit) { this.controller.display.toast('Paste refused. The limit is 256 KiB.'); return; } // Refuse oversized text.
            if (this.controller.preferences.get('confirmPaste') && terminal.Internal.lineCount(text) > 1) { this.dialog.open(text, false); return; } // Review multi-line paste when enabled.
            this.delivery.send(text); // Send safe text directly.
        }

        nativePaste(event) { // Handle a native browser paste event.
            var text = event.clipboardData ? event.clipboardData.getData('text/plain') : ''; // Read plain clipboard text.
            if (!text) return; // Ignore paste events without text.
            event.preventDefault(); // Stop direct browser insertion.
            event.stopPropagation(); // Prevent duplicate xterm paste handling.
            this.handleText(text); // Use the shared validation path.
        }
    }

    terminal.Internal.PasteFlow = PasteFlow; // Publish paste flow for controller composition.
})();
