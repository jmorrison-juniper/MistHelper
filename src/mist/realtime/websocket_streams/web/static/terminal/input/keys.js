(function() { // Add terminal keyboard shortcut behavior.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    function isCopy(event, controller) { // Detect browser copy shortcuts.
        return (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'c') || (event.ctrlKey && event.key === 'Insert') || (event.metaKey && event.key.toLowerCase() === 'c' && controller.term.hasSelection()); // Support common terminal copy keys.
    }

    function isSelectedCtrlC(event, controller) { // Detect Ctrl+C copy with a selection.
        return event.ctrlKey && !event.shiftKey && event.key.toLowerCase() === 'c' && controller.term.hasSelection(); // Preserve interrupt behavior without a selection.
    }

    function isPaste(event) { // Detect browser paste shortcuts.
        return (event.ctrlKey && event.key.toLowerCase() === 'v') || (event.metaKey && event.key.toLowerCase() === 'v') || (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'v') || (event.shiftKey && event.key === 'Insert'); // Support common terminal paste keys.
    }

    class TerminalKeys { // Own xterm shortcut interception.
        constructor(controller) { // Store the active terminal controller.
            this.controller = controller; // Use selection, paste, and input state.
        }

        bind() { // Attach shortcut handling to xterm.
            this.controller.term.attachCustomKeyEventHandler(this.handle.bind(this)); // Inspect keys before xterm sends them.
        }

        handle(event) { // Decide whether the browser or device handles one key.
            if (event.type !== 'keydown') return true; // Let xterm handle non-keydown events.
            if (isCopy(event, this.controller) || isSelectedCtrlC(event, this.controller)) { // Keep copy shortcuts in the browser.
                event.preventDefault(); // Stop copy bytes from reaching the device.
                this.controller.clipboard.copySelection(); // Copy the active terminal selection.
                return false; // Tell xterm that the browser handled the key.
            }
            if (isPaste(event)) return this.handlePaste(event); // Route paste shortcuts through paste safety.
            return !this.controller.inputBlocked(); // Block other input only for read-only or ended sessions.
        }

        handlePaste(event) { // Handle one paste shortcut.
            if (this.controller.inputBlocked()) { event.preventDefault(); return false; } // Block paste for non-writable sessions.
            var nativePaste = this.controller.preferences.get('ctrlVBehavior') === 'paste' && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'v' && !event.shiftKey; // Detect simple native paste.
            if (nativePaste) return true; // Let the browser emit a paste event.
            event.preventDefault(); // Stop custom paste keys before clipboard read.
            this.controller.pasteFlow.pasteFromClipboard(); // Use shared paste validation.
            return false; // Tell xterm that the browser handled the key.
        }
    }

    terminal.Internal.TerminalKeys = TerminalKeys; // Publish keyboard behavior for runtime composition.
})();
