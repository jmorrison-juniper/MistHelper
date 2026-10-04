(function() { // Add terminal selection and history actions.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    class TerminalHistory { // Own copy-on-select and local history download.
        constructor(controller) { // Store the active terminal controller.
            this.controller = controller; // Read xterm and preference state through one object.
        }

        bind() { // Attach selection and download controls once.
            this.controller.elements.screen.addEventListener('mouseup', this.copySelection.bind(this)); // Copy after a mouse selection completes.
            this.controller.elements.download.addEventListener('click', this.download.bind(this)); // Download the visible xterm history.
        }

        copySelection() { // Copy selected text when the preference permits it.
            if (this.controller.preferences.get('copyOnSelect') && this.controller.term && this.controller.term.hasSelection()) { // Require an active selected range.
                this.controller.clipboard.copySelection({ clearSelection: false }); // Keep the visible selection after automatic copy.
            }
        }

        download() { // Download visible terminal history.
            if (!this.controller.term || !this.controller.session) return; // Stop when no terminal session is active.
            var buffer = this.controller.term.buffer.active; // Read the active xterm scrollback buffer.
            var lines = []; // Collect terminal rows for the text file.
            for (var index = 0; index < buffer.length; index += 1) { // Walk all retained rows.
                var line = buffer.getLine(index); // Read one xterm row.
                if (line) lines.push(line.translateToString(true)); // Preserve non-empty rows in order.
            }
            var blob = new Blob([lines.join('\n') + '\n'], { type: 'text/plain' }); // Build a local text download.
            var link = document.createElement('a'); // Create a temporary download link.
            link.href = URL.createObjectURL(blob); // Create a local object URL.
            link.download = this.name(); // Use a safe session-specific file name.
            document.body.appendChild(link); // Attach the link for one click.
            link.click(); // Start the browser download.
            URL.revokeObjectURL(link.href); // Release the object URL.
            document.body.removeChild(link); // Remove the temporary link.
            this.controller.focusTerminal(); // Return focus to xterm.
        }

        name() { // Build a safe terminal history file name.
            var session = this.controller.session; // Read the active session metadata.
            var label = (session.title || session.key || 'terminal').replace(/[^A-Za-z0-9_.-]+/g, '-'); // Sanitize the title.
            return label + '-' + new Date().toISOString().replace(/[:.]/g, '-') + '.txt'; // Add a file-safe timestamp.
        }
    }

    terminal.Internal.TerminalHistory = TerminalHistory; // Publish history behavior for controller composition.
})();
