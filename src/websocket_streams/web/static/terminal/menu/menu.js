(function() { // Add terminal context menu behavior.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    class TerminalMenu { // Own context menu visibility and actions.
        constructor(controller) { // Store the active terminal controller.
            this.controller = controller; // Use xterm, clipboard, and paste behavior.
            this.menu = controller.elements.menu; // Keep the menu element for positioning.
        }

        bind() { // Attach menu events once.
            this.controller.elements.screen.addEventListener('contextmenu', this.open.bind(this)); // Open at the pointer.
            this.controller.elements.menuCopy.addEventListener('click', this.action.bind(this, 'copy')); // Bind Copy.
            this.controller.elements.menuPaste.addEventListener('click', this.action.bind(this, 'paste')); // Bind Paste.
            this.controller.elements.menuSelectAll.addEventListener('click', this.action.bind(this, 'select')); // Bind Select all.
            this.controller.elements.menuClear.addEventListener('click', this.action.bind(this, 'clear')); // Bind Clear.
            document.addEventListener('click', this.close.bind(this)); // Close after outside clicks.
            document.addEventListener('keydown', function(event) { if (event.key === 'Escape') this.close(); }.bind(this)); // Close on Escape.
        }

        open(event) { // Open the menu or direct paste path.
            event.preventDefault(); // Stop the browser context menu.
            if (this.controller.preferences.get('rightClickAction') === 'paste' && !this.controller.inputBlocked()) { this.controller.pasteFlow.pasteFromClipboard(); return; } // Paste directly when configured.
            this.menu.style.left = event.clientX + 'px'; // Align the menu with the pointer.
            this.menu.style.top = event.clientY + 'px'; // Align the menu vertically.
            this.menu.classList.remove('d-none'); // Show the menu.
            this.controller.elements.menuCopy.focus(); // Move keyboard focus into the menu.
        }

        close() { // Hide the context menu.
            this.menu.classList.add('d-none'); // Remove the menu from view.
        }

        action(name, event) { // Run one selected menu action.
            event.preventDefault(); // Prevent default button behavior.
            this.close(); // Hide the menu before the action.
            if (name === 'copy') this.controller.clipboard.copySelection(); // Copy selected terminal text.
            if (name === 'paste' && !this.controller.inputBlocked()) { this.controller.pasteFlow.pasteFromClipboard(); return; } // Keep paste dialog focus when manual input opens.
            if (name === 'select') this.controller.term.selectAll(); // Select the complete xterm buffer.
            if (name === 'clear') { this.controller.term.clear(); this.controller.term.write('\x1b[2J\x1b[H'); } // Clear local history and visible rows.
            this.controller.focusTerminal(); // Return focus after the menu action.
        }
    }

    terminal.Internal.TerminalMenu = TerminalMenu; // Publish menu behavior for controller composition.
})();
