(function() { // Add terminal clipboard behavior.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    class TerminalClipboard { // Own selection copy and browser fallback behavior.
        constructor(controller) { // Store the active terminal controller.
            this.controller = controller; // Read selection and show messages through the controller.
        }

        copySelection(options) { // Copy selected terminal text without device input.
            var text = this.controller.term ? this.controller.term.getSelection() : ''; // Read only the xterm selection.
            var clearSelection = !options || options.clearSelection !== false; // Clear explicit copies by default.
            if (!text) { // Stop when no selection exists.
                this.controller.display.toast('No terminal text is selected.'); // Explain why Copy did nothing.
                return Promise.resolve(false); // Report a local copy miss.
            }
            return this.copyText(text).then(function(copied) { // Use the best browser copy path.
                if (copied && clearSelection) this.controller.term.clearSelection(); // Preserve selection only for copy-on-select.
                if (copied) this.controller.display.toast('Copied ' + text.length + ' characters.'); // Report success without terminal content.
                return copied; // Return the copy result.
            }.bind(this)); // Keep the clipboard object in the callback.
        }

        copyText(text) { // Write text through modern clipboard support.
            if (window.isSecureContext && navigator.clipboard && navigator.clipboard.writeText) { // Use the Clipboard API only when available.
                return navigator.clipboard.writeText(text).then(function() { return true; }).catch(function() { return this.fallback(text); }.bind(this)); // Fall back after permission failure.
            }
            return Promise.resolve(this.fallback(text)); // Use the legacy path on unsupported pages.
        }

        fallback(text) { // Copy through a temporary text area.
            var area = document.createElement('textarea'); // Create a temporary copy target.
            area.value = text; // Put selected terminal text in the target.
            area.setAttribute('aria-hidden', 'true'); // Hide the helper from assistive technology.
            area.className = 'ws-terminal-clipboard-helper'; // Keep the helper off screen.
            document.body.appendChild(area); // Add the helper only for the copy command.
            area.select(); // Select the helper text.
            try { // Attempt the legacy browser copy command.
                var copied = document.execCommand('copy'); // Run the legacy copy command one time.
                if (!copied) this.controller.display.toast('Copy failed. Select the text and copy it again.'); // Give manual recovery guidance.
                return copied; // Report the actual browser copy result.
            } catch (error) { // Handle browsers that throw during copy.
                this.controller.display.toast('Copy failed. Select the text and copy it again.'); // Give the same recovery guidance.
                return false; // Report the failed copy.
            } finally { // Always remove the temporary helper.
                document.body.removeChild(area); // Remove hidden terminal text from the page.
                this.controller.focusTerminal(); // Return focus to the terminal.
            }
        }
    }

    terminal.Internal.TerminalClipboard = TerminalClipboard; // Publish clipboard behavior for controller composition.
})();
