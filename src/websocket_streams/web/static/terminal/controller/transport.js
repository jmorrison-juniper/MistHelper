/* global readJsonAnswer */ // Declare the shared JSON response helper.

(function() { // Add terminal HTTP and resize behavior.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    class TerminalTransport { // Own terminal POST requests.
        constructor(controller) { // Store the active controller.
            this.controller = controller; // Read session and input state.
        }

        postInput(text) { // Send one input request.
            if (!this.controller.session || this.controller.inputBlocked()) return Promise.resolve({ error: 'This terminal is read-only.', code: 'read_only' }); // Refuse local invalid input.
            return this.postJson('/api/websockets/sessions/' + encodeURIComponent(this.controller.session.session_id) + '/input', { data: text }); // Post input to the active session.
        }

        postResize(cols, rows) { // Send shell geometry.
            if (!this.controller.session || this.controller.inputBlocked()) return; // Skip non-writable sessions.
            this.postJson('/api/websockets/sessions/' + encodeURIComponent(this.controller.session.session_id) + '/resize', { cols: cols, rows: rows }).then(function(answer) { // Post current geometry.
                if (answer && answer.error) this.controller.display.error(answer); // Show resize failures in the footer.
            }.bind(this)); // Keep the transport object in the callback.
        }

        postJson(url, body) { // Send one protected JSON request.
            return fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken() }, body: JSON.stringify(body) }).then(readJsonAnswer).catch(function() { // Decode portal JSON answers.
                return { error: 'The portal did not answer. Check the network, then try again.', code: 'network' }; // Normalize network failure.
            });
        }

        csrfToken() { // Read the current form token.
            if (window.getCsrfToken) return window.getCsrfToken(); // Prefer the shared portal helper.
            var meta = document.querySelector('meta[name="csrf-token"]'); // Find the fallback token tag.
            return meta ? meta.getAttribute('content') : ''; // Return a token or an empty value.
        }
    }

    class TerminalResize { // Own shell fit and resize observation.
        constructor(controller) { // Store the active controller.
            this.controller = controller; // Read xterm and transport state.
            this.timer = null; // Start without a resize debounce.
            this.observer = null; // Start without a resize observer.
        }

        fit(force) { // Fit xterm and post changed geometry.
            var controller = this.controller; // Use a short state reference.
            if (controller.readOnly || !controller.fitAddon || !controller.term) return; // Skip fixed or absent terminals.
            controller.fitAddon.fit(); // Fit xterm to the visible panel.
            if (controller.inputClosed) return; // Skip backend updates after input closes.
            if (force || controller.term.cols !== controller.lastSize.cols || controller.term.rows !== controller.lastSize.rows) { // Post only changed or forced geometry.
                controller.lastSize = { cols: controller.term.cols, rows: controller.term.rows }; // Remember the posted size.
                controller.transport.postResize(controller.term.cols, controller.term.rows); // Send the new size.
                controller.display.status(controller.formatter.status({ state: controller.lastState })); // Show the size before the next read.
            }
        }

        start() { // Watch the shell screen for size changes.
            if (this.controller.readOnly || !window.ResizeObserver) return; // Skip fixed screens and unsupported browsers.
            this.observer = new ResizeObserver(function() { // Watch terminal panel geometry.
                if (this.timer) window.clearTimeout(this.timer); // Replace the previous debounce.
                this.timer = window.setTimeout(function() { this.fit(false); }.bind(this), 120); // Post stable geometry only.
            }.bind(this)); // Keep the resize object in the observer callback.
            this.observer.observe(this.controller.elements.screen); // Observe only the xterm host.
        }

        stop() { // Stop pending resize work.
            if (this.observer) this.observer.disconnect(); // Stop watching the old session.
            if (this.timer) window.clearTimeout(this.timer); // Cancel a pending fit.
            this.observer = null; // Clear the stopped observer.
            this.timer = null; // Clear the stopped timer.
        }
    }

    terminal.Internal.TerminalTransport = TerminalTransport; // Publish HTTP behavior for controller composition.
    terminal.Internal.TerminalResize = TerminalResize; // Publish resize behavior for controller composition.
})();
