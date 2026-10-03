(function() { // Compose all terminal leaf behaviors.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    class TerminalFormatter { // Own terminal footer and warning formatting.
        constructor(controller) { // Store the active controller.
            this.controller = controller; // Read xterm, labels, and warning elements.
        }

        status(payload) { // Build terminal footer text.
            var size = this.controller.term ? 'Size: ' + this.controller.term.cols + ' x ' + this.controller.term.rows : ''; // Include current xterm geometry.
            var value = payload.state || 'live'; // Use live when state is absent.
            var state = 'State: ' + (this.controller.stateText[value] || value); // Apply shared page labels.
            var reason = payload.reason ? 'Reason: ' + payload.reason : ''; // Include a backend reason when present.
            return [state, size, reason].filter(Boolean).join(' | '); // Join non-empty footer parts.
        }

        gap(count) { // Show a dropped-output warning.
            this.controller.elements.gap.textContent = count > 0 ? 'The portal no longer holds ' + count + ' terminal bytes.' : ''; // State the missing byte count.
            this.controller.elements.gap.classList.toggle('d-none', count <= 0); // Hide the warning when no gap exists.
        }

        expiry(value) { // Show a near-expiration warning.
            var element = this.controller.elements.expiry; // Read the expiry element once.
            if (!value) { element.classList.add('d-none'); return; } // Hide stale expiry text.
            var remaining = Date.parse(value) - Date.now(); // Measure time until backend expiry.
            element.textContent = remaining < 120000 && remaining > 0 ? 'This terminal expires at ' + value + '.' : ''; // Warn only after the final two-minute boundary.
            element.classList.toggle('d-none', !element.textContent); // Hide empty warning text.
        }
    }

    class TerminalRuntime { // Own xterm creation, wiring, and disposal.
        constructor(controller) { // Store the active controller.
            this.controller = controller; // Build xterm from current session state.
        }

        create() { // Create xterm for shell or fixed screen output.
            var controller = this.controller; // Use a short state reference.
            var terminalClass = window.Terminal && (window.Terminal.Terminal || window.Terminal); // Support both xterm package shapes.
            var fitClass = window.FitAddon && (window.FitAddon.FitAddon || window.FitAddon); // Support both fit addon shapes.
            controller.elements.screen.textContent = ''; // Clear output from the previous session.
            var options = { convertEol: false, cursorBlink: true, disableStdin: controller.readOnly, fontSize: controller.preferences.get('fontSize'), scrollback: 5000 }; // Keep established terminal options.
            if (controller.readOnly) { options.cols = 80; options.rows = 40; } // Use the fixed Mist screen geometry.
            controller.term = new terminalClass(options); // Create a fresh xterm instance.
            controller.fitAddon = new fitClass(); // Create fit support for shell mode.
            if (!controller.readOnly) controller.term.loadAddon(controller.fitAddon); // Load fit support only for shells.
            controller.term.open(controller.elements.screen); // Attach xterm to the page.
            controller.preferenceControls.load(); // Apply saved toolbar settings.
        }

        wire() { // Connect xterm input and keyboard behavior.
            var controller = this.controller; // Use a short state reference.
            controller.term.onData(function(data) { // Receive keys and xterm paste bytes.
                if (controller.inputBlocked()) return; // Drop bytes for blocked sessions.
                if (controller.pasteFlow.delivery.active) controller.pasteFlow.delivery.consume(data); // Preserve paste progress metadata.
                else controller.sendQueue.enqueueText(data, { paste: false }); // Queue normal typed input.
            }); // Keep the stable controller closure.
            controller.keys = new terminal.Internal.TerminalKeys(controller); // Create keyboard handling after xterm exists.
            controller.keys.bind(); // Attach custom shortcut handling.
        }

        dispose() { // Dispose the active xterm instance.
            if (this.controller.term) this.controller.term.dispose(); // Release xterm resources.
            this.controller.term = null; // Clear the disposed instance.
            this.controller.fitAddon = null; // Clear the disposed fit addon.
        }
    }

    class TerminalController { // Coordinate terminal leaves through the page interface.
        constructor(elements, options) { // Compose one reusable terminal controller.
            options = options || {}; // Accept omitted page callbacks.
            this.elements = elements; // Keep all terminal page elements together.
            this.onState = typeof options.onState === 'function' ? options.onState : function() {}; // Use a safe state callback.
            this.stateText = options.stateText || {}; // Use page state labels when supplied.
            this.session = null; this.term = null; this.fitAddon = null; // Start without an active terminal.
            this.nextPosition = 0; this.openedAt = 0; this.lastState = ''; // Start without output state.
            this.stopped = true; this.readOnly = false; this.inputClosed = false; // Start with input stopped.
            this.lastSize = { cols: 0, rows: 0 }; this.readFailures = 0; this.readGeneration = 0; this.readAbort = null; // Prepare read and resize state.
            this.pasteProgress = null; this.keys = null; // Prepare input helper state.
            this.preferences = new terminal.Internal.TerminalPreferences(window.localStorage); // Load saved preferences first.
            this.display = new terminal.Internal.TerminalDisplay(this); this.panel = new terminal.Internal.TerminalPanel(this); // Compose display leaves.
            this.formatter = new TerminalFormatter(this); this.transport = new terminal.Internal.TerminalTransport(this); // Compose format and HTTP leaves.
            this.resize = new terminal.Internal.TerminalResize(this); this.reader = new terminal.Internal.TerminalReader(this); // Compose output and geometry leaves.
            this.clipboard = new terminal.Internal.TerminalClipboard(this); this.history = new terminal.Internal.TerminalHistory(this); // Compose clipboard leaves.
            this.sendQueue = new terminal.Internal.TerminalSendQueue(this); this.pasteFlow = new terminal.Internal.PasteFlow(this); // Compose input leaves.
            this.menu = new terminal.Internal.TerminalMenu(this); this.preferenceControls = new terminal.Internal.PreferenceControls(this); // Compose menu and setting leaves.
            this.runtime = new TerminalRuntime(this); // Compose xterm lifecycle behavior.
            this.pasteFlow.bind(); this.menu.bind(); this.history.bind(); this.preferenceControls.bind(); // Attach stable page controls once.
            elements.copy.addEventListener('click', function() { this.clipboard.copySelection(); }.bind(this)); // Bind toolbar Copy.
            elements.paste.addEventListener('click', function() { if (!this.inputBlocked()) this.pasteFlow.pasteFromClipboard(); }.bind(this)); // Bind toolbar Paste.
        }

        open(session) { // Open a selected terminal and start its journeys.
            this.close(); // Remove the previous session first.
            this.session = session; this.stopped = false; this.inputClosed = false; // Activate the selected session.
            this.readOnly = session.read_only === true || session.output === 'screen'; // Detect fixed read-only screen output.
            this.lastState = session.state || ''; this.nextPosition = 0; this.openedAt = Date.now(); this.readFailures = 0; // Reset output state.
            this.panel.show(true); // Show clean terminal controls.
            var generation = this.readGeneration; // Bind the deferred mount to this selection.
            window.requestAnimationFrame(function() { // Let the disposed xterm release its shared host first.
                if (generation !== this.readGeneration || this.stopped) return; // Skip a session that changed first.
                this.runtime.create(); this.runtime.wire(); // Create and connect xterm after host cleanup.
                if (!this.readOnly) { this.resize.fit(true); this.resize.start(); } // Fit and observe shell sessions.
                this.reader.start(); // Start terminal output reads after xterm mounts.
                this.focusTerminal(); // Move keyboard focus to xterm.
            }.bind(this)); // Keep the controller in the frame callback.
            if (session.state === 'connecting') this.onState({ notice: terminal.constants.waitingNotice }); // Explain the initial device wait.
        }

        close() { // Close the active terminal and all pending work.
            this.stopped = true; this.readGeneration += 1; // Invalidate reads and timers.
            if (this.readAbort) this.readAbort.abort(); // Cancel the active long read.
            this.readAbort = null; this.sendQueue.close(); this.pasteFlow.dialog.reset(); // Clear pending network and input state.
            this.pasteFlow.delivery.active = false; // Prevent old paste bytes from marking new session input.
            this.pasteProgress = null; this.display.progress(0, 0); this.menu.close(); this.resize.stop(); // Reset local controls.
            this.runtime.dispose(); this.session = null; // Dispose xterm and clear session state.
            this.elements.screen.classList.remove('ws-terminal-screen-fixed'); // Remove fixed screen styling.
            this.panel.show(false); // Hide the terminal panel.
        }

        inputBlocked() { // Report whether device input is blocked.
            return this.readOnly || this.inputClosed; // Block screen output and ended sessions.
        }

        focusTerminal() { // Focus the active xterm instance.
            if (this.term) this.term.focus(); // Skip focus when no terminal exists.
        }
    }

    terminal.TerminalController = TerminalController; // Expose the page controller after all leaves load.
})();
