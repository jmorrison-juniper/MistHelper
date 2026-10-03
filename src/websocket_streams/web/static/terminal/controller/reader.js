/* global readJsonAnswer */ // Declare the shared JSON response helper.

(function() { // Add terminal output reading and state behavior.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    function decodeBytes(data) { // Decode base64 output for xterm.
        var binary = window.atob(data); // Decode route output.
        var bytes = new Uint8Array(binary.length); // Allocate the exact output size.
        for (var index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index); // Copy bytes in order.
        return bytes; // Return xterm-compatible bytes.
    }

    function waitNotice(controller) { // Build the first-output notice.
        if (controller.nextPosition > 0) return ''; // Clear the notice after output arrives.
        var limit = terminal.Internal.testHookValue('noOutputNoticeSeconds', terminal.constants.noOutputNoticeSeconds); // Read the production or test wait.
        if ((Date.now() - controller.openedAt) / 1000 < limit) return terminal.constants.waitingNotice; // Explain the normal initial wait.
        return 'The device sent no output in ' + limit + ' seconds. Stop this session. Start a new session after one minute.'; // Give recovery guidance for a silent device.
    }

    class TerminalReadState { // Apply terminal read answers and final states.
        constructor(controller, reader) { // Store controller and reader behavior.
            this.controller = controller; // Update the active terminal.
            this.reader = reader; // Schedule later reads.
        }

        apply(payload) { // Apply one successful read answer.
            var controller = this.controller; // Use a short state reference.
            controller.readOnly = payload.read_only === true; // Trust the backend mode.
            if (controller.term) controller.term.options.disableStdin = controller.inputBlocked(); // Keep xterm input equal to state.
            controller.panel.readOnly(); // Refresh paste and screen controls.
            if (payload.data) controller.term.write(decodeBytes(payload.data)); // Draw new output bytes.
            controller.nextPosition = payload.next === undefined ? controller.nextPosition : payload.next; // Advance the output position.
            controller.formatter.gap(payload.gap || 0); // Show dropped output bytes.
            controller.formatter.expiry(payload.expires_at); // Show near-expiration state.
            controller.lastState = payload.state || controller.lastState; // Keep the latest state for resize text.
            controller.display.status(controller.formatter.status(payload)); // Refresh footer text.
            this.notify(payload, false); // Update the page session state.
        }

        failure(payload) { // Handle one terminal read failure.
            var controller = this.controller; // Use a short state reference.
            controller.readFailures += 1; // Count consecutive read failures.
            if (payload.code === 'not_found' || payload.code === 'not_terminal') { // Stop for an invalid terminal identity.
                controller.display.error(payload); // Show the permanent failure.
                controller.stopped = true; // Stop further reads.
                controller.inputClosed = true; // Block later input.
                controller.panel.readOnly(); // Disable paste controls.
                if (controller.term) controller.term.options.disableStdin = true; // Disable xterm input.
                controller.sendQueue.close(); // Discard queued input.
                controller.resize.stop(); // Stop geometry work.
                return; // Do not retry a missing terminal.
            }
            if (controller.readFailures >= terminal.constants.maxReadFailures) controller.display.error(payload); // Show repeated transient failures.
            this.reader.schedule(1000); // Retry after a short delay.
        }

        finish(payload) { // Finish one terminal session.
            var controller = this.controller; // Use a short state reference.
            controller.stopped = true; // Stop the read loop.
            controller.inputClosed = true; // Close input.
            if (controller.term) controller.term.options.disableStdin = true; // Disable xterm input.
            controller.panel.readOnly(); // Refresh blocked controls.
            controller.display.status(controller.formatter.status(payload)); // Show final state and reason.
            this.notify(payload, true); // Update the host page with final state.
            controller.sendQueue.close(); // Drop queued input.
            controller.resize.stop(); // Stop geometry observation.
        }

        notify(payload, final) { // Notify the host page of terminal state.
            this.controller.onState({ state: payload.state || 'live', reason: payload.reason || '', notice: final ? '' : waitNotice(this.controller), read_only: this.controller.readOnly, live: !final, terminal_next: this.controller.nextPosition }); // Send compact state metadata.
        }
    }

    class TerminalReader { // Own one long-poll output loop.
        constructor(controller) { // Prepare read state for one controller.
            this.controller = controller; // Read the active session.
            this.state = new TerminalReadState(controller, this); // Apply read answers through a dedicated leaf.
        }

        start() { // Start one terminal long-poll read.
            var controller = this.controller; // Use a short state reference.
            if (controller.stopped || !controller.session) return; // Stop after close or before open.
            var generation = controller.readGeneration; // Tie the read to this session generation.
            var abort = typeof AbortController === 'function' ? new AbortController() : null; // Let close cancel the request.
            controller.readAbort = abort; // Keep the active cancellation handle.
            var url = '/api/websockets/sessions/' + encodeURIComponent(controller.session.session_id) + '/terminal'; // Build the session read route.
            url += '?after=' + encodeURIComponent(String(controller.nextPosition)) + '&wait=' + terminal.Internal.testHookValue('readWaitSeconds', terminal.constants.readWaitSeconds); // Request only unseen output.
            fetch(url, abort ? { signal: abort.signal } : {}).then(readJsonAnswer).then(function(payload) { if (generation === controller.readGeneration) this.answer(payload); }.bind(this)).catch(function() { if (generation === controller.readGeneration) this.answer({ error: 'The portal did not answer.', code: 'network' }); }.bind(this)); // Normalize read success and failure.
        }

        schedule(delayMs) { // Schedule the next read for this session.
            var generation = this.controller.readGeneration; // Capture the active session generation.
            window.setTimeout(function() { if (generation === this.controller.readGeneration) this.start(); }.bind(this), delayMs); // Prevent a closed session from restarting.
        }

        answer(payload) { // Process one terminal read answer.
            if (this.controller.stopped || !this.controller.session) return; // Ignore answers after close.
            if (payload.error) return this.state.failure(payload); // Route failures through retry or stop logic.
            this.controller.readFailures = 0; // Reset failures after a successful read.
            this.state.apply(payload); // Apply output and metadata.
            if (terminal.constants.finalStates.indexOf(payload.state) !== -1) return this.state.finish(payload); // Stop after final state cleanup.
            var delay = payload.data ? 0 : terminal.Internal.testHookValue('emptyLiveReadDelayMs', terminal.constants.emptyReadDelayMs); // Back off only after empty reads.
            this.schedule(delay); // Continue the output loop.
        }
    }

    terminal.Internal.TerminalReader = TerminalReader; // Publish reader behavior for controller composition.
})();
