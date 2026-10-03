(function() { // Add ordered terminal input delivery.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.
    var chunks = terminal.Internal.inputChunks; // Use the production UTF-8 chunk helpers.

    class QueueParts { // Own queue merging, paste removal, and progress.
        constructor(queue) { // Store the queue that owns the parts.
            this.queue = queue; // Update one ordered input queue.
        }

        push(text, paste, progress) { // Add one input part within the byte limit.
            var parts = this.queue.parts; // Read queued parts once.
            var last = parts[parts.length - 1]; // Inspect the latest queued input.
            if (!paste && last && !last.paste && chunks.utf8Length(last.text + text) <= terminal.constants.sendPartLimit) { // Merge adjacent typed input safely.
                last.text += text; // Reduce small input requests without changing order.
                return; // Stop after merging.
            }
            parts.push({ text: text, paste: paste, progress: progress }); // Add a distinct input part.
        }

        dropPaste(part) { // Remove unsent parts from one failed paste.
            var progress = part.progress; // Identify all parts from the paste.
            var sent = progress ? progress.sent : 0; // Report accepted bytes.
            var total = progress ? progress.total : chunks.utf8Length(part.text); // Report the paste byte total.
            this.queue.parts = this.queue.parts.filter(function(candidate) { return !(candidate.paste && candidate.progress === progress); }); // Keep unrelated input.
            this.queue.controller.display.toast('Paste failed after ' + sent + ' of ' + total + ' bytes.'); // Explain the partial paste.
            this.queue.sendNext(); // Continue with later unrelated input.
        }

        updateProgress(part) { // Update paste progress after a successful input request.
            if (!part.progress) return; // Skip normal typed input.
            part.progress.sent += chunks.utf8Length(part.text); // Add accepted backend bytes.
            this.queue.controller.display.progress(part.progress.sent, part.progress.total); // Refresh the progress bar.
            if (part.progress.sent >= part.progress.total) window.setTimeout(function() { this.queue.controller.display.progress(0, 0); }.bind(this), 600); // Leave completion visible briefly.
        }
    }

    class TerminalSendQueue { // Own ordered input requests and retry behavior.
        constructor(controller) { // Prepare an empty queue for one controller.
            this.controller = controller; // Send input through the active terminal controller.
            this.parts = []; // Start with no queued input.
            this.inFlight = false; // Let the first part send.
            this.generation = 0; // Invalidate late answers after close.
            this.partActions = new QueueParts(this); // Compose queue part behavior.
        }

        enqueueText(text, options) { // Add text to the ordered input queue.
            var paste = !!(options && options.paste); // Mark paste data for failure cleanup.
            var progress = options && options.progress ? options.progress : null; // Share large paste progress across parts.
            chunks.splitText(text, terminal.constants.sendPartLimit).forEach(function(chunk) { this.partActions.push(chunk, paste, progress); }.bind(this)); // Preserve input order while chunking.
            this.sendNext(); // Start delivery when the queue is idle.
        }

        close() { // Close and clear the current session queue.
            this.generation += 1; // Make late answers stale.
            this.parts = []; // Discard unsent input.
            this.inFlight = false; // Reset request state.
        }

        sendNext() { // Send the oldest queued input part.
            if (this.inFlight || !this.parts.length || !this.controller.session) return; // Wait until delivery can continue.
            var part = this.parts.shift(); // Remove the oldest part.
            var generation = this.generation; // Tie the request to this queue generation.
            this.inFlight = true; // Block a second concurrent input request.
            this.controller.transport.postInput(part.text).then(function(answer) { // Send this input part.
                if (generation !== this.generation) return; // Drop an answer for a closed session.
                if (answer && answer.error) return this.handleError(part, answer, generation); // Preserve order through failure handling.
                this.inFlight = false; // Release the queue after success.
                this.partActions.updateProgress(part); // Update paste progress when required.
                this.sendNext(); // Continue with the next queued part.
            }.bind(this)); // Keep the queue object in the callback.
        }

        handleError(part, answer, generation) { // Retry or discard one failed input part.
            this.controller.display.error(answer); // Show the backend refusal.
            if (answer.code === 'rate_limited') { // Retry rate-limited input.
                this.parts.unshift(part); // Put the failed part back first.
                window.setTimeout(function() { if (generation === this.generation) { this.inFlight = false; this.sendNext(); } }.bind(this), 1000); // Retry only for the active session.
                return; // Keep later input behind the failed part.
            }
            this.inFlight = false; // Release the queue after a permanent failure.
            if (part.paste) return this.partActions.dropPaste(part); // Drop the remainder of one failed paste.
            this.sendNext(); // Continue with later typed input.
        }
    }

    terminal.Internal.TerminalSendQueue = TerminalSendQueue; // Publish queue behavior for controller composition.
})();
