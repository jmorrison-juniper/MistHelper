(function() { // Add saved terminal preferences to the shared namespace.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the namespace from the bootstrap leaf.

    class TerminalPreferences { // Own terminal preference storage.
        constructor(storage) { // Load preferences before controls use them.
            this.storage = storage || window.localStorage; // Let tests replace local storage.
            this.values = this.load(); // Merge stored values with safe defaults.
        }

        get(name) { // Return one saved preference.
            return this.values[name]; // Keep preference reads in this leaf.
        }

        set(name, value) { // Save one preference value.
            this.values[name] = value; // Update the active value first.
            this.save(); // Persist the new value for reloads.
        }

        load() { // Load stored preferences with safe defaults.
            var defaults = { copyOnSelect: true, confirmPaste: true, ctrlVBehavior: 'paste', fontSize: 14, rightClickAction: 'menu' }; // Define first-visit behavior.
            try { // Read stored JSON when it is valid.
                return Object.assign(defaults, JSON.parse(this.storage.getItem(terminal.constants.preferenceKey) || '{}')); // Keep defaults for missing fields.
            } catch (error) { // Recover from damaged browser storage.
                return defaults; // Keep the terminal usable with default settings.
            }
        }

        save() { // Persist all preference values.
            this.storage.setItem(terminal.constants.preferenceKey, JSON.stringify(this.values)); // Store one compact JSON record.
        }
    }

    terminal.Internal.TerminalPreferences = TerminalPreferences; // Publish the preference leaf for controller composition.
})();
