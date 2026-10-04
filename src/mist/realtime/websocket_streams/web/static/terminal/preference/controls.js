(function() { // Add preference control and font behavior.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    class PreferenceControls { // Own toolbar preference controls.
        constructor(controller) { // Store the active terminal controller.
            this.controller = controller; // Use controls, preferences, and resize behavior.
        }

        bind() { // Attach preference controls once.
            this.controller.elements.copyOnSelect.addEventListener('change', this.save.bind(this)); // Save selection copy changes.
            this.controller.elements.confirmPaste.addEventListener('change', this.save.bind(this)); // Save paste confirmation changes.
            this.controller.elements.fontUp.addEventListener('click', this.changeFont.bind(this, 1)); // Increase terminal text size.
            this.controller.elements.fontDown.addEventListener('click', this.changeFont.bind(this, -1)); // Decrease terminal text size.
        }

        load() { // Apply saved preferences to page controls.
            this.controller.elements.copyOnSelect.checked = !!this.controller.preferences.get('copyOnSelect'); // Reflect copy-on-select state.
            this.controller.elements.confirmPaste.checked = !!this.controller.preferences.get('confirmPaste'); // Reflect paste confirmation state.
        }

        save() { // Save current checkbox preferences.
            this.controller.preferences.set('copyOnSelect', this.controller.elements.copyOnSelect.checked); // Save selection copy behavior.
            this.controller.preferences.set('confirmPaste', this.controller.elements.confirmPaste.checked); // Save multi-line paste review.
            this.controller.display.toast('Terminal settings saved.'); // Confirm the saved settings.
            this.controller.focusTerminal(); // Return focus to xterm.
        }

        changeFont(delta) { // Change and persist terminal font size.
            var next = Math.max(10, Math.min(28, Number(this.controller.preferences.get('fontSize')) + delta)); // Keep text within a usable range.
            this.controller.preferences.set('fontSize', next); // Save the new size.
            if (this.controller.term) { this.controller.term.options.fontSize = next; this.controller.resize.fit(true); } // Refit the active shell after size changes.
        }
    }

    terminal.Internal.PreferenceControls = PreferenceControls; // Publish preference controls for controller composition.
})();
