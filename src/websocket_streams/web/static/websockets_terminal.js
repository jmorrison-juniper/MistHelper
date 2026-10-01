/* global readJsonAnswer */ // Declare the shared JSON helper for browser lint checks.

(function() { // Keep terminal code private to this browser module.
    'use strict'; // Fail fast when a variable is misspelled.

    var PREF_KEY = 'misthelper.wsTerminal.prefs'; // Use one storage key for all terminal preferences.
    var PASTE_LIMIT = 256 * 1024; // Refuse very large pastes before they reach xterm.
    var PASTE_PROGRESS_LIMIT = 16 * 1024; // Show progress only when a paste is large enough to matter.
    var SEND_PART_LIMIT = 4096; // Keep each input request within the backend byte limit.
    var READ_WAIT_SECONDS = 20; // Let the read route wait for output before it answers.
    var EMPTY_LIVE_READ_DELAY_MS = 250; // Wait after an empty live read so idle terminals do not flood the portal.
    var MAX_READ_FAILURES = 5; // Hide transient read errors until repeated failures show a real problem.
    var FINAL_STATES = ['stopped', 'finished', 'timed_out', 'failed']; // Stop polling only when the backend reports a final state.

    function testHookValue(name, fallback) { // Read browser test overrides for timing-sensitive terminal behavior.
        var hooks = window.MistWebSocketTerminalTestHooks || {}; // Read test hooks from the browser only when tests install them.
        return hooks[name] === undefined ? fallback : hooks[name]; // Prefer the test override and otherwise use the production value.
    }

    function terminalLineCount(text) { // Count terminal lines consistently for paste warnings.
        if (!text) return 0; // Treat empty paste text as zero lines.
        return text.replace(/\r\n|\r|\n$/, '').split(/\r\n|\r|\n/).length; // Ignore one trailing newline so the dialog shows the submitted line count.
    }

    class TerminalPreferences { // Keep saved terminal settings with their storage behavior.
        constructor(storage) { // Prepare preference storage before the terminal opens.
            this.storage = storage || window.localStorage; // Store the storage object so tests can replace localStorage.
            this.values = this._load(); // Load preferences before toolbar controls read them.
        }

        get(name) { // Read one saved preference value.
            return this.values[name]; // Give callers the current saved value.
        }

        set(name, value) { // Change one preference and persist it.
            this.values[name] = value; // Update the in-memory setting before persistence.
            this._save(); // Write changed preferences immediately so a reload keeps them.
        }

        _load() { // Load saved settings and safe defaults.
            var defaults = { // Define safe defaults for a first terminal visit.
                copyOnSelect: true, // Enable quick copy by default for operator convenience.
                confirmPaste: true, // Ask before multi-line paste by default to protect devices.
                ctrlVBehavior: 'paste', // Let normal Ctrl+V paste when the browser supports it.
                fontSize: 14, // Start at a readable terminal font size.
                rightClickAction: 'menu' // Open the menu on right click unless the operator changes it.
            };
            try { // Try stored settings first because operators may have changed defaults.
                return Object.assign(defaults, JSON.parse(this.storage.getItem(PREF_KEY) || '{}')); // Merge saved values over defaults so missing keys remain safe.
            } catch (error) { // Use defaults when stored JSON is missing or invalid.
                return defaults; // Keep the terminal usable when preference parsing fails.
            }
        }

        _save() { // Save terminal preference values.
            this.storage.setItem(PREF_KEY, JSON.stringify(this.values)); // Save preferences as JSON for a later page load.
        }
    }

    class TerminalClipboard { // Keep copy behavior and fallback support together.
        constructor(controller) { // Prepare copy behavior for one terminal controller.
            this.controller = controller; // Keep the controller reference for terminal selection and messages.
        }

        copySelection(options) { // Copy highlighted terminal text without sending device input.
            var text = this.controller.term ? this.controller.term.getSelection() : ''; // Read only the current xterm selection.
            var clearSelection = !options || options.clearSelection !== false; // Clear selection by default after an explicit Copy action.
            if (!text) { // Stop copy when no text is selected.
                this.controller.showToast('No terminal text is selected.'); // Tell the operator why the Copy action did nothing.
                return Promise.resolve(false); // Report a local copy miss without throwing an exception.
            }
            return this.copyText(text).then(function(copied) { // Copy text through the best available browser path.
                if (copied) { // Run success actions only after the clipboard accepts text.
                    if (clearSelection) this.controller.term.clearSelection(); // Clear highlighted text only for copy actions that requested it.
                    this.controller.showToast('Copied ' + text.length + ' characters.'); // Report copy success without revealing terminal output.
                }
                return copied; // Return the copy result to the caller.
            }.bind(this)); // Keep this bound inside the asynchronous copy callback.
        }

        copyText(text) { // Write text to the browser clipboard when possible.
            if (window.isSecureContext && navigator.clipboard && navigator.clipboard.writeText) { // Use Clipboard API only in a secure page with write support.
                return navigator.clipboard.writeText(text).then(function() { // Write selected text through the browser clipboard API.
                    return true; // Report success after the Clipboard API accepts text.
                }).catch(function() { // Use the fallback path when Clipboard API write fails.
                    return this._fallbackCopy(text); // Try the text area copy path after Clipboard API failure.
                }.bind(this)); // Keep this bound inside the clipboard failure callback.
            }
            return Promise.resolve(this._fallbackCopy(text)); // Use the fallback copy path when Clipboard API support is absent.
        }

        _fallbackCopy(text) { // Copy through a temporary element when modern clipboard access fails.
            var area = document.createElement('textarea'); // Create a temporary text area for legacy browser copy support.
            area.value = text; // Place selected terminal text into the temporary element.
            area.setAttribute('aria-hidden', 'true'); // Hide the helper element from assistive technology.
            area.className = 'ws-terminal-clipboard-helper'; // Use the helper class so CSS keeps the element off screen.
            document.body.appendChild(area); // Add the helper only for the browser copy command.
            area.select(); // Select helper text so the browser copy command has a target.
            try { // Attempt the legacy browser copy command safely.
                if (!document.execCommand('copy')) { // Handle a rejected legacy copy command.
                    this.controller.showToast('Copy failed. Select the text and copy it again.'); // Tell the operator to use manual copy after fallback failure.
                    return false; // Report failed fallback copy to the caller.
                }
                return true; // Report that the fallback copy command succeeded.
            } catch (error) { // Handle browsers that throw during the fallback copy command.
                this.controller.showToast('Copy failed. Select the text and copy it again.'); // Show the same operator guidance after a thrown copy error.
                return false; // Report thrown fallback failure to the caller.
            } finally { // Always remove the temporary helper after copy work.
                document.body.removeChild(area); // Remove the helper so the page does not keep hidden text.
                this.controller.focusTerminal(); // Return focus to the terminal after the copy attempt.
            }
        }
    }

    class TerminalSendQueue { // Keep ordered terminal input delivery in one queue.
        constructor(controller) { // Prepare the input queue for one terminal controller.
            this.controller = controller; // Keep the controller reference for input POST requests.
            this.parts = []; // Start with no queued input for a new session.
            this.inFlight = false; // Allow the first queued input part to send.
            this.progress = null; // Start without paste progress because no paste is active.
            this.generation = 0; // Count queue closes so a late answer for a closed session is dropped.
        }

        enqueueText(text, options) { // Add terminal input to the ordered send queue.
            var chunks = this._splitText(text, SEND_PART_LIMIT); // Split input before queueing so each request stays small.
            var paste = !!(options && options.paste); // Mark paste data so failed paste cleanup can remove related parts.
            var progress = options && options.progress ? options.progress : null; // Attach progress only when a large paste needs operator feedback.
            chunks.forEach(function(chunk) { // Queue chunks in browser event order.
                this._pushPart(chunk, paste, progress); // Add one chunk with its paste and progress metadata.
            }.bind(this)); // Keep this bound while chunk callbacks run.
            this._sendNext(); // Start sending immediately when the queue was idle.
        }

        close() { // Close the input queue for the current session.
            this.generation += 1; // Make every answer and retry timer of the closed session stale.
            this.parts = []; // Discard unsent input when the terminal closes.
            this.inFlight = false; // Clear the active request flag for the next session.
            this.progress = null; // Clear progress tracking with the closed queue.
        }

        _pushPart(text, paste, progress) { // Add one input part while preserving byte limits.
            var last = this.parts[this.parts.length - 1]; // Read the last queued part so typed bytes can merge safely.
            if (!paste && last && !last.paste && this._utf8Length(last.text + text) <= SEND_PART_LIMIT) { // Merge normal typing while the combined UTF-8 size stays safe.
                last.text += text; // Append typed text to reduce small POST requests.
                return; // Stop after merging because no new queue item is needed.
            }
            this.parts.push({ text: text, paste: paste, progress: progress }); // Append a new part when merge rules do not apply.
        }

        _sendNext() { // Send the next queued input part when the queue is ready.
            if (this.inFlight || !this.parts.length || !this.controller.session) return; // Wait when a request is active, no input exists, or no session exists.
            var part = this.parts.shift(); // Remove one part so requests run in strict order.
            var generation = this.generation; // Tie this request to the session that queued the part.
            this.inFlight = true; // Mark the request active before sending input.
            this.controller.postInput(part.text).then(function(answer) { // Post this input part to the current terminal session.
                if (generation !== this.generation) return; // Drop the answer because the page closed that session.
                if (answer && answer.error) { // Handle backend refusal before the queue advances.
                    this._handleSendError(part, answer, generation); // Choose retry or drop behavior from the error response.
                    return; // Stop this success path after an error.
                }
                this.inFlight = false; // Clear the active flag after a successful POST.
                this._updateProgress(part); // Advance paste progress after the backend accepts bytes.
                this._sendNext(); // Send the next queued part after this one succeeds.
            }.bind(this)); // Keep this bound inside the input POST callback.
        }

        _handleSendError(part, answer, generation) { // Handle a failed input request without losing order.
            this.controller.showError(answer); // Show the backend input error to the operator.
            if (answer.code === 'rate_limited') { // Retry rate-limited input instead of dropping typed bytes.
                this.parts.unshift(part); // Put the failed part back first to preserve byte order.
                window.setTimeout(function() { // Wait before retrying so the backend queue can drain.
                    if (generation !== this.generation) return; // Never resend old input after the page closed its session.
                    this.inFlight = false; // Allow the queued part to send again after the delay.
                    this._sendNext(); // Retry the oldest queued input part.
                }.bind(this), 1000); // Keep this bound inside the retry timer.
                return; // Stop after scheduling the retry.
            }
            this.inFlight = false; // Clear the active flag after a non-retryable failure.
            if (part.paste) { // Treat a paste failure as one failed paste operation.
                this._dropPaste(part); // Drop remaining paste parts that belong to the same paste.
                return; // Stop after reporting the paste failure.
            }
            this._sendNext(); // Continue with later normal input after a non-paste failure.
        }

        _dropPaste(part) { // Drop unsent parts from a failed paste.
            var progress = part.progress; // Read the progress object shared by this paste.
            var sent = progress ? progress.sent : 0; // Show how many bytes reached the backend before failure.
            var total = progress ? progress.total : this._utf8Length(part.text); // Use known paste size, or measure this part when progress is absent.
            this.parts = this.parts.filter(function(candidate) { // Keep only queued parts that do not belong to the failed paste.
                return !(candidate.paste && candidate.progress === progress); // Remove unsent parts from the same paste operation.
            });
            this.controller.showToast('Paste failed after ' + sent + ' of ' + total + ' bytes.'); // Tell the operator how much paste data was accepted before failure.
            this._sendNext(); // Continue with later queued input after dropping failed paste parts.
        }

        _updateProgress(part) { // Update the paste progress meter after a send succeeds.
            if (!part.progress) return; // Skip progress updates for normal typing.
            part.progress.sent += this._utf8Length(part.text); // Add accepted bytes to the shared paste progress.
            this.controller.showPasteProgress(part.progress.sent, part.progress.total); // Refresh the progress bar with accepted paste bytes.
            if (part.progress.sent >= part.progress.total) { // Hide the progress bar after the full paste reaches the backend.
                window.setTimeout(function() { // Leave the completed bar visible briefly for operator confirmation.
                    this.controller.hidePasteProgress(); // Hide progress after the operator can see completion.
                }.bind(this), 600); // Keep this bound inside the completion delay.
            }
        }

        _splitText(text, limit) { // Split text without exceeding the gateway byte limit.
            if (/^[\x00-\x7F]*$/.test(text)) return this._splitAsciiText(text, limit); // Use faster slicing when input contains only single-byte characters.
            var chunks = []; // Collect UTF-8 safe chunks for mixed-byte text.
            var start = 0; // Mark the start of the current chunk.
            var currentLength = 0; // Track UTF-8 bytes in the current chunk.
            for (var index = 0; index < text.length;) { // Walk the string by code point, not only code unit.
                var codePoint = text.codePointAt(index); // Read the next Unicode code point for byte measurement.
                var characterUnits = codePoint > 0xffff ? 2 : 1; // Advance two code units for characters outside the basic plane.
                var characterLength = this._utf8CodePointLength(codePoint); // Measure this character before adding it to the chunk.
                if (index > start && currentLength + characterLength > limit) { // Start a new chunk before the current one exceeds the byte limit.
                    chunks.push(text.slice(start, index)); // Save the full chunk without splitting the current character.
                    start = index; // Begin the next chunk at the current character.
                    currentLength = 0; // Reset the byte count for the new chunk.
                }
                currentLength += characterLength; // Count this character in the current chunk.
                index += characterUnits; // Move to the next character boundary.
            }
            if (start < text.length) chunks.push(text.slice(start)); // Keep the final partial chunk if text remains.
            return chunks; // Return chunks that stay within the byte limit.
        }

        _splitAsciiText(text, limit) { // Split ASCII input with direct slicing.
            var chunks = []; // Collect fixed-size slices for ASCII input.
            for (var index = 0; index < text.length; index += limit) chunks.push(text.slice(index, index + limit)); // Slice ASCII text by byte limit because each character is one byte.
            return chunks; // Return ASCII chunks in original order.
        }

        _utf8CodePointLength(codePoint) { // Measure one code point as UTF-8 bytes.
            if (codePoint <= 0x7f) return 1; // Classify ASCII characters as one byte.
            if (codePoint <= 0x7ff) return 2; // Classify two-byte UTF-8 code points.
            if (codePoint <= 0xffff) return 3; // Classify three-byte UTF-8 code points.
            return 4; // Classify remaining code points as four UTF-8 bytes.
        }

        _utf8Length(text) { // Measure full text as UTF-8 bytes.
            return new TextEncoder().encode(text).length; // Measure text exactly as fetch sends it.
        }
    }

    class PasteFlow { // Keep paste review and delivery behavior together.
        constructor(controller) { // Prepare paste state for one terminal controller.
            this.controller = controller; // Keep the controller reference for paste dialog and input paths.
            this.activePaste = false; // Start outside paste mode until xterm emits paste data.
            this.pendingText = ''; // Start with no paste text awaiting confirmation.
            this.manualMode = false; // Start outside manual mode until clipboard access fails.
        }

        bind() { // Attach the native paste listener to the terminal screen.
            this.controller.screen.addEventListener('paste', this._onPasteEvent.bind(this), true); // Capture native paste before xterm can duplicate the data.
        }

        pasteFromClipboard() { // Start paste from the browser clipboard.
            if (this.controller.inputBlocked()) return; // Ignore paste requests when the session cannot take input.
            if (window.isSecureContext && navigator.clipboard && navigator.clipboard.readText) { // Use clipboard read only on secure pages that support it.
                navigator.clipboard.readText().then(function(text) { // Read clipboard text asynchronously from the browser.
                    this.handleText(text); // Validate clipboard text before terminal delivery.
                }.bind(this)).catch(function() { // Fall back when clipboard read is denied or unavailable.
                    this.openManualPaste(); // Open a field where the operator can paste text manually.
                }.bind(this)); // Keep this bound inside the clipboard read failure callback.
                return; // Stop after the Clipboard API path starts.
            }
            this.openManualPaste(); // Use manual paste when direct clipboard read is unavailable.
        }

        openManualPaste() { // Open the manual paste dialog.
            if (this.controller.inputBlocked()) return; // Do not open paste UI for read-only or ended sessions.
            this.manualMode = true; // Mark that confirmation will read from the manual text box.
            this.controller.showPasteDialog('', true); // Show the manual text box for operator input.
        }

        handleText(text) { // Validate paste text before device delivery.
            if (this.controller.inputBlocked()) return; // Reject paste work when the session cannot accept input.
            if (!text) return; // Ignore empty clipboard text.
            if (new TextEncoder().encode(text).length > PASTE_LIMIT) { // Measure paste size before xterm receives it.
                this.controller.showToast('Paste refused. The limit is 256 KiB.'); // Tell the operator that the paste exceeds the limit.
                return; // Stop before oversized text reaches xterm.
            }
            if (this.controller.prefs.get('confirmPaste') && this.lineCount(text) > 1) { // Require confirmation for multi-line paste when the preference is enabled.
                this.pendingText = text; // Store the paste text until the operator confirms it.
                this.manualMode = false; // Use confirmation preview mode, not manual input mode.
                this.controller.showPasteDialog(text, false); // Show the paste preview before sending commands to the device.
                return; // Wait for the operator decision before sending paste text.
            }
            this.sendThroughTerminal(text); // Send single-line or unconfirmed paste text through xterm.
        }

        confirmPending() { // Confirm pending paste text.
            var text = this.manualMode ? this.controller.pasteInput.value : this.pendingText; // Choose manual text only when manual paste mode is active.
            this.pendingText = ''; // Clear pending text so it cannot send twice.
            this.manualMode = false; // Leave manual mode after the operator confirms paste.
            this.controller.hidePasteDialog(); // Close the dialog before terminal focus returns.
            this.handleTextWithoutDialog(text); // Continue without a second confirmation dialog.
        }

        cancelPending() { // Cancel the pending paste.
            this.pendingText = ''; // Clear pending text because the operator cancelled paste.
            this.manualMode = false; // Leave manual mode after cancel.
            this.controller.hidePasteDialog(); // Close the dialog after the operator cancels.
            this.controller.focusTerminal(); // Return focus to xterm after cancel.
        }

        reset() { // Drop all paste state when the page closes the terminal session.
            this.pendingText = ''; // A paste for the closed session must never reach the next session.
            this.manualMode = false; // The next session starts outside manual paste mode.
            this.activePaste = false; // Typed keys of the next session are not paste data.
            this.controller.hidePasteDialog(); // Close a confirmation dialog that belongs to the closed session.
        }

        handleTextWithoutDialog(text) { // Send confirmed paste text without another confirmation prompt.
            if (this.controller.inputBlocked()) return; // Stop confirmed paste if the session stopped accepting input.
            if (!text) { // Handle an empty manual paste without an error.
                this.controller.focusTerminal(); // Return focus because no paste data needs delivery.
                return; // Stop the empty paste path.
            }
            if (new TextEncoder().encode(text).length > PASTE_LIMIT) { // Recheck size because manual paste can bypass earlier checks.
                this.controller.showToast('Paste refused. The limit is 256 KiB.'); // Tell the operator that the paste exceeds the limit.
                return; // Stop before oversized confirmed text reaches xterm.
            }
            this.sendThroughTerminal(text); // Deliver validated text through xterm.
        }

        sendThroughTerminal(text) { // Send paste text through xterm.
            var total = new TextEncoder().encode(text).length; // Measure paste bytes so progress uses backend units.
            this.activePaste = true; // Enter paste mode so emitted xterm data is queued as paste.
            this.controller.pasteProgress = total > PASTE_PROGRESS_LIMIT ? { sent: 0, total: total } : null; // Track progress only for paste data large enough to show.
            this.controller.term.paste(text); // Let xterm apply bracketed paste behavior before sending bytes.
            window.setTimeout(function() { // Clear paste mode after xterm emits paste data.
                this.activePaste = false; // Leave paste mode so normal typing uses the normal queue.
            }.bind(this), 0); // Keep this bound inside the zero-delay paste cleanup.
            this.controller.focusTerminal(); // Return focus after the browser paste action finishes.
        }

        consumeData(data) { // Queue bytes emitted by xterm during paste.
            var progress = this.controller.pasteProgress; // Read the active paste progress record.
            this.controller.sendQueue.enqueueText(data, { paste: true, progress: progress }); // Queue paste bytes with progress metadata.
        }

        _onPasteEvent(event) { // Handle a native paste event.
            var text = event.clipboardData ? event.clipboardData.getData('text/plain') : ''; // Read plain text from the native paste event.
            if (!text) return; // Ignore paste events that contain no text.
            event.preventDefault(); // Stop the browser from inserting paste data directly.
            event.stopPropagation(); // Prevent xterm from receiving the same paste event.
            if (this.controller.inputBlocked()) return; // Ignore paste text after the session becomes blocked.
            this.handleText(text); // Validate native paste text through the shared paste path.
        }

        lineCount(text) { // Count paste lines for dialog display.
            return terminalLineCount(text); // Use the shared terminal line counter for paste warnings.
        }
    }

    class TerminalKeys { // Keep keyboard shortcut handling together.
        constructor(controller) { // Prepare key handling for one terminal controller.
            this.controller = controller; // Keep the controller reference for key decisions.
        }

        bind() { // Attach custom key handling to xterm.
            this.controller.term.attachCustomKeyEventHandler(this._handleKey.bind(this)); // Inspect key events before xterm forwards them to the device.
        }

        _handleKey(event) { // Decide whether a key shortcut stays local or reaches the device.
            if (event.type !== 'keydown') return true; // Let xterm handle key release and other non-keydown events.
            if (this._copyKey(event)) { // Keep copy shortcuts in the browser.
                event.preventDefault(); // Stop the copy shortcut from reaching the device.
                this.controller.clipboard.copySelection(); // Copy selected terminal text through the shared path.
                return false; // Tell xterm that the browser handled the copy shortcut.
            }
            if (this._ctrlCWithSelection(event)) { // Treat Ctrl+C as copy when text is selected.
                event.preventDefault(); // Protect the live device from an accidental interrupt.
                this.controller.clipboard.copySelection(); // Copy the current selection without clearing it first.
                return false; // Stop xterm from also handling the selected-text copy.
            }
            if (this._pasteKey(event)) { // Handle paste shortcuts before device input is sent.
                if (this.controller.inputBlocked()) { // Block paste shortcuts for read-only and ended sessions.
                    event.preventDefault(); // Stop blocked paste keys before xterm receives them.
                    return false; // Tell xterm the blocked paste shortcut was handled.
                }
                if (this._nativePasteKey(event)) return true; // Let xterm handle simple Ctrl+V when preferences allow it.
                event.preventDefault(); // Stop custom paste shortcuts before reading the clipboard.
                this.controller.pasteFlow.pasteFromClipboard(); // Use shared paste validation for keyboard paste.
                return false; // Tell xterm that the browser handled this paste shortcut.
            }
            if (this.controller.inputBlocked()) return false; // Block all other device input when the session is not writable.
            return true; // Allow normal keys to reach the live shell.
        }

        _copyKey(event) { // Detect keyboard copy shortcuts.
            return (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'c') // Recognize Ctrl+Shift+C as browser copy.
                || (event.ctrlKey && event.key === 'Insert') // Recognize Ctrl+Insert as browser copy.
                || (event.metaKey && event.key.toLowerCase() === 'c' && this.controller.term.hasSelection()); // Recognize Command+C as copy only when text is selected.
        }

        _ctrlCWithSelection(event) { // Detect Ctrl+C copy when terminal text is selected.
            return event.ctrlKey && !event.shiftKey && event.key.toLowerCase() === 'c' && this.controller.term.hasSelection(); // Detect selected text before treating Ctrl+C as copy.
        }

        _pasteKey(event) { // Detect keyboard paste shortcuts.
            return (event.ctrlKey && event.key.toLowerCase() === 'v') // Recognize Ctrl+V as a paste shortcut.
                || (event.metaKey && event.key.toLowerCase() === 'v') // Recognize Command+V as a paste shortcut.
                || (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'v') // Recognize Ctrl+Shift+V as a paste shortcut.
                || (event.shiftKey && event.key === 'Insert'); // Recognize Shift+Insert as a paste shortcut.
        }

        _nativePasteKey(event) { // Detect when native browser paste can handle a key.
            if (this.controller.prefs.get('ctrlVBehavior') !== 'paste') return false; // Disable native paste when the preference selects custom paste handling.
            return (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'v' && !event.shiftKey; // Allow native paste only for simple Ctrl+V or Command+V.
        }
    }

    class TerminalMenu { // Keep context menu behavior together.
        constructor(controller) { // Prepare menu behavior for one terminal controller.
            this.controller = controller; // Keep the controller reference for menu actions.
            this.menu = controller.menu; // Store the menu element for show and hide operations.
        }

        bind() { // Attach context menu actions to browser events.
            this.controller.screen.addEventListener('contextmenu', this._open.bind(this)); // Open the terminal menu from right-click events.
            this.controller.menuCopy.addEventListener('click', this._copy.bind(this)); // Connect the menu Copy item to terminal selection copy.
            this.controller.menuPaste.addEventListener('click', this._paste.bind(this)); // Connect the menu Paste item to paste validation.
            this.controller.menuSelectAll.addEventListener('click', this._selectAll.bind(this)); // Connect Select All to the xterm buffer selection.
            this.controller.menuClear.addEventListener('click', this._clear.bind(this)); // Connect Clear to local terminal buffer cleanup.
            document.addEventListener('click', this.close.bind(this)); // Close the menu when the operator clicks elsewhere.
            document.addEventListener('keydown', this._onKeyDown.bind(this)); // Let Escape close menu UI without device input.
        }

        close() { // Hide the context menu.
            this.menu.classList.add('d-none'); // Hide the context menu after a selection or outside click.
        }

        _open(event) { // Open the context menu or direct paste path.
            event.preventDefault(); // Stop the browser context menu for the terminal area.
            if (this.controller.prefs.get('rightClickAction') === 'paste' && !this.controller.inputBlocked()) { // Paste directly on right click only when the preference allows it.
                this.controller.pasteFlow.pasteFromClipboard(); // Use shared paste validation for right-click paste.
                return; // Stop after the right-click paste path starts.
            }
            this.menu.style.left = event.clientX + 'px'; // Place the menu at the pointer position.
            this.menu.style.top = event.clientY + 'px'; // Align the menu vertically with the pointer.
            this.menu.classList.remove('d-none'); // Show the menu after deciding not to paste directly.
            this.controller.menuCopy.focus(); // Move focus into the menu for keyboard users.
        }

        _copy(event) { // Handle the menu Copy action.
            event.preventDefault(); // Prevent menu link navigation before Copy runs.
            this.close(); // Hide the menu before copying selected text.
            this.controller.clipboard.copySelection(); // Copy the current selection from the terminal.
        }

        _paste(event) { // Handle the menu Paste action.
            event.preventDefault(); // Prevent menu link navigation before Paste runs.
            this.close(); // Hide the menu before paste UI opens.
            if (!this.controller.inputBlocked()) this.controller.pasteFlow.pasteFromClipboard(); // Paste only when the session still accepts input.
        }

        _selectAll(event) { // Handle the Select All menu action.
            event.preventDefault(); // Prevent menu link navigation before selection changes.
            this.close(); // Hide the menu before selecting the buffer.
            this.controller.term.selectAll(); // Select all visible terminal buffer text through xterm.
            this.controller.focusTerminal(); // Return focus to xterm after selecting text.
        }

        _clear(event) { // Handle the Clear menu action.
            event.preventDefault(); // Prevent menu link navigation before clearing scrollback.
            this.close(); // Hide the menu before clearing local output.
            this.controller.term.clear(); // Clear local terminal history only.
            this.controller.focusTerminal(); // Return focus to xterm after clearing history.
        }

        _onKeyDown(event) { // Handle Escape while the menu is open.
            if (event.key === 'Escape') this.close(); // Close the menu when Escape is pressed.
        }
    }

    class TerminalController { // Keep the browser terminal panel controller together.
        constructor(elements, options) { // Prepare all page elements and helpers for terminal sessions.
            options = options || {}; // Accept empty options so tests can omit callbacks.
            this.elements = elements; // Keep all page elements used by the terminal panel.
            this.panel = elements.panel; // Store the panel so open and close can change visibility.
            this.screen = elements.screen; // Store the xterm host element for attach and resize work.
            this.status = elements.status; // Store the status area for read state and errors.
            this.warning = elements.warning; // Store the warning area for shell and screen guidance.
            this.expiry = elements.expiry; // Store the expiry area for near-expiration warnings.
            this.gap = elements.gap; // Store the gap notice so missed bytes stay visible.
            this.toast = elements.toast; // Store the toast area for short operator messages.
            this.progress = elements.progress; // Store the progress element for large paste feedback.
            this.dialog = elements.dialog; // Store the paste dialog for review and manual paste.
            this.pasteInput = elements.pasteInput; // Store the manual paste field for HTTP clipboard fallback.
            this.pasteLines = elements.pasteLines; // Store the line count area for paste risk review.
            this.pastePreview = elements.pastePreview; // Store the preview area so operators can review paste text.
            this.pasteSend = elements.pasteSend; // Store the send button for confirmed paste delivery.
            this.pasteCancel = elements.pasteCancel; // Store the cancel button for paste discard.
            this.menu = elements.menu; // Store the menu element for right-click actions.
            this.menuCopy = elements.menuCopy; // Store the Copy menu item for focus and action binding.
            this.menuPaste = elements.menuPaste; // Store the Paste menu item for read-only disabling.
            this.menuSelectAll = elements.menuSelectAll; // Store Select All for xterm buffer selection.
            this.menuClear = elements.menuClear; // Store Clear for local buffer cleanup.
            this.pasteInputLabel = elements.pasteInputLabel; // Store the manual paste label for mode-specific display.
            this.onState = typeof options.onState === 'function' ? options.onState : function() {}; // Use the supplied state callback or a safe no-op.
            this.stateText = options.stateText || {}; // Use shared state labels from the page when present.
            this.session = null; // Start with no active terminal session.
            this.term = null; // Start without xterm until a session opens.
            this.fitAddon = null; // Start without a fit addon until xterm exists.
            this.nextPosition = 0; // Start reading output from byte zero.
            this.stopped = true; // Start stopped so no read loop runs before open.
            this.readOnly = false; // Start in shell mode until a session says otherwise.
            this.inputClosed = false; // Start with input available until a session blocks it.
            this.lastSize = { cols: 0, rows: 0 }; // Force the first shell resize to post geometry.
            this.resizeTimer = null; // Start without a resize debounce timer.
            this.resizeObserver = null; // Start without a resize observer.
            this.readFailures = 0; // Start with no read failures for a new controller.
            this.readGeneration = 0; // Count session closes so a late read answer for a closed session is dropped.
            this.readAbort = null; // Hold the abort handle of the long read that is in flight.
            this.prefs = new TerminalPreferences(window.localStorage); // Load preferences before toolbar wiring reads them.
            this.clipboard = new TerminalClipboard(this); // Create shared clipboard behavior for all copy paths.
            this.sendQueue = new TerminalSendQueue(this); // Create the ordered send queue for typed and pasted input.
            this.pasteFlow = new PasteFlow(this); // Create shared paste validation and delivery behavior.
            this.keys = null; // Delay key handling until xterm exists.
            this.menuController = new TerminalMenu(this); // Create context menu behavior for this terminal panel.
            this.pasteProgress = null; // Start without paste progress until a large paste begins.
            this._wireToolbar(); // Attach toolbar handlers once for this controller.
            this.pasteFlow.bind(); // Attach native paste handling to the terminal screen.
            this.menuController.bind(); // Attach context menu handlers to the terminal screen.
            this.screen.addEventListener('mouseup', this._copyOnSelect.bind(this)); // Enable copy-on-select after mouse selection completes.
        }

        open(session) { // Open a selected terminal session and start reading output.
            this.close(); // Close any prior terminal before opening the selected session.
            this.session = session; // Store the selected session for reads and input requests.
            this.stopped = false; // Allow the read loop to run for the new session.
            this.readOnly = session.read_only === true || session.output === 'screen'; // Detect fixed screen output that must stay read-only.
            this.inputClosed = false; // Open the new session with input allowed until state says otherwise.
            this.nextPosition = 0; // Start the new session read at the first byte.
            this.readFailures = 0; // Failures of the previous session must not count against this session.
            this._showPanel(true); // Show the terminal panel before xterm attaches.
            this._createTerminal(); // Create xterm with the selected session mode.
            this._wireTerminal(); // Attach xterm input and keyboard handlers.
            if (!this.readOnly) this._fitAndResize(true); // Fit writable shell sessions before posting their size.
            if (!this.readOnly) this._startResizeObserver(); // Watch size changes only for writable shell sessions.
            this._readLoop(); // Begin long-poll reads for terminal output.
            this.focusTerminal(); // Move keyboard focus to the opened terminal.
        }

        close() { // Close the active terminal session panel.
            this.stopped = true; // Stop reads for the current session.
            this.readGeneration += 1; // Make every read answer and read timer of the closing session stale.
            if (this.readAbort) this.readAbort.abort(); // Cancel the long read so it frees its browser connection now.
            this.readAbort = null; // Clear the abort handle of the cancelled read.
            this.sendQueue.close(); // Discard queued input for the closing session.
            this.pasteFlow.reset(); // Drop a paste that waits for confirmation, so it cannot reach the next session.
            this.pasteProgress = null; // Forget the paste progress of the closing session.
            this.hidePasteProgress(); // Hide the progress bar of the closing session.
            this.menuController.close(); // Hide the context menu of the closing session.
            if (this.resizeObserver) this.resizeObserver.disconnect(); // Stop watching panel size when the terminal closes.
            this.resizeObserver = null; // Clear the observer reference after disconnect.
            if (this.resizeTimer) window.clearTimeout(this.resizeTimer); // Cancel any pending resize debounce callback.
            this.resizeTimer = null; // Clear the resize timer reference after cancel.
            if (this.term) this.term.dispose(); // Dispose xterm resources when a terminal exists.
            this.term = null; // Clear the xterm reference after disposal.
            this.fitAddon = null; // Clear the fit addon with the disposed terminal.
            this.session = null; // Clear the active session after close.
            this.screen.classList.remove('ws-terminal-screen-fixed'); // Remove fixed-screen styling when no screen session is active.
            this._showPanel(false); // Hide the terminal panel after cleanup.
        }

        inputBlocked() { // Report whether the current session can accept input.
            return this.readOnly || this.inputClosed; // A screen command and an ended shell both block input.
        }

        postInput(text) { // Send one input request to the portal for the active session.
            if (!this.session || this.inputBlocked()) return Promise.resolve({ error: 'This terminal is read-only.', code: 'read_only' }); // Refuse locally when no writable session can take input.
            return this._postJson('/api/websockets/sessions/' + encodeURIComponent(this.session.session_id) + '/input', { data: text }); // Send input bytes to the active session route.
        }

        showError(answer) { // Show a readable status message for a portal or session error.
            this.setStatus(this._errorMessage(answer)); // Convert the error response to footer text.
        }

        setStatus(text) { // Update the terminal footer with the current session message.
            this.status.textContent = text || ''; // Set footer text and clear it when no message exists.
        }

        showToast(text) { // Show a short page message for copy, paste, and setting actions.
            this.toast.textContent = text || ''; // Set toast text or clear the old message.
            this.toast.classList.toggle('d-none', !text); // Hide the toast when no message is present.
        }

        showPasteProgress(sent, total) { // Display paste progress for large input.
            this.progress.max = total; // Set the progress maximum in backend byte units.
            this.progress.value = sent; // Set current progress to accepted paste bytes.
            this.progress.classList.remove('d-none'); // Show the progress bar while a large paste sends.
        }

        hidePasteProgress() { // Hide the paste progress meter.
            this.progress.classList.add('d-none'); // Hide the progress bar after paste completion or panel reset.
            this.progress.value = 0; // Reset progress value for the next paste.
        }

        _applyReadOnlyUi() { // Apply page controls for read-only state.
            var warningText = this.readOnly ? 'This view is read-only. The device sends the screen.' : 'Warning: Each command runs on the live device.'; // Choose the warning text from the active session mode.
            this.warning.textContent = warningText; // Show shell risk or read-only guidance to the operator.
            var pasteBlocked = this.inputBlocked(); // Compute paste state after read-only and closed flags update.
            this.elements.paste.disabled = pasteBlocked; // Disable toolbar Paste when input is blocked.
            this.menuPaste.disabled = pasteBlocked; // Disable menu Paste with the same state.
            this.menuPaste.classList.toggle('disabled', pasteBlocked); // Show the disabled menu state visually.
            this.menuPaste.setAttribute('aria-disabled', pasteBlocked ? 'true' : 'false'); // Expose disabled paste state to assistive technology.
            this.screen.classList.toggle('ws-terminal-screen-fixed', this.readOnly); // Apply fixed-screen styling for read-only screen output.
        }

        showPasteDialog(text, manual) { // Show the paste review or manual paste dialog.
            var lines = text ? text.split(/\r\n|\r|\n/) : []; // Prepare preview lines for paste review.
            this.pasteLines.textContent = manual ? 'Paste text into the field, then select Paste.' : 'Lines: ' + this.pasteFlow.lineCount(text); // Show manual instructions or the paste line count.
            this.pastePreview.textContent = manual ? '' : lines.slice(0, 5).join('\n'); // Show only the first five paste lines in the preview.
            this.pasteInput.value = manual ? '' : text; // Fill the manual box only for preview mode data.
            this.pasteInput.classList.toggle('d-none', !manual); // Show the manual input box only in manual mode.
            if (this.pasteInputLabel) this.pasteInputLabel.classList.toggle('d-none', !manual); // Show the manual label only with the manual input box.
            this.dialog.classList.remove('d-none'); // Display the paste dialog after its content is ready.
            this.pasteCancel.focus(); // Focus Cancel first so accidental Enter does not send paste.
        }

        hidePasteDialog() { // Hide paste dialog controls.
            this.dialog.classList.add('d-none'); // Hide the paste dialog after send, cancel, or reset.
            this.pasteInput.value = ''; // Clear manual paste text after the dialog closes.
            if (this.pasteInputLabel) this.pasteInputLabel.classList.add('d-none'); // Hide the manual label with the closed dialog.
        }

        focusTerminal() { // Focus the active terminal.
            if (this.term) this.term.focus(); // Focus xterm only when an active terminal exists.
        }

        _wireToolbar() { // Attach toolbar actions.
            this.elements.copy.addEventListener('click', function() { this.clipboard.copySelection(); }.bind(this)); // Bind toolbar Copy to selected terminal text.
            this.elements.paste.addEventListener('click', function() { if (!this.inputBlocked()) this.pasteFlow.pasteFromClipboard(); }.bind(this)); // Bind toolbar Paste to shared paste validation.
            this.elements.download.addEventListener('click', this._downloadHistory.bind(this)); // Bind Download to local history export.
            this.elements.fontUp.addEventListener('click', this._changeFont.bind(this, 1)); // Bind font increase to the clamped size change.
            this.elements.fontDown.addEventListener('click', this._changeFont.bind(this, -1)); // Bind font decrease to the clamped size change.
            this.elements.copyOnSelect.addEventListener('change', this._saveSettings.bind(this)); // Save copy-on-select preference changes immediately.
            this.elements.confirmPaste.addEventListener('change', this._saveSettings.bind(this)); // Save paste-confirmation preference changes immediately.
            this.pasteSend.addEventListener('click', this.pasteFlow.confirmPending.bind(this.pasteFlow)); // Bind Paste dialog send to pending paste confirmation.
            this.pasteCancel.addEventListener('click', this.pasteFlow.cancelPending.bind(this.pasteFlow)); // Bind Paste dialog cancel to pending paste discard.
            this.dialog.addEventListener('keydown', this._dialogKey.bind(this)); // Let Escape close the paste dialog safely.
        }

        _createTerminal() { // Create xterm for the selected session mode.
            var terminalClass = window.Terminal && (window.Terminal.Terminal || window.Terminal); // Read the xterm constructor from either package shape.
            var fitClass = window.FitAddon && (window.FitAddon.FitAddon || window.FitAddon); // Read the fit addon constructor from either package shape.
            this.screen.textContent = ''; // Clear old terminal output before attaching new xterm.
            var options = { // Collect the xterm options for the selected session.
                convertEol: false, // Keep backend line endings unchanged in xterm.
                cursorBlink: true, // Show the cursor blink for an active terminal feel.
                disableStdin: this.readOnly, // Disable keyboard input for read-only screen sessions.
                fontSize: this.prefs.get('fontSize'), // Apply the saved font size to the new terminal.
                scrollback: 5000 // Keep enough scrollback for troubleshooting session output.
            };
            if (this.readOnly) { // Only a screen command uses the fixed Mist screen size.
                options.cols = 80; // xterm refuses an undefined size, so a shell omits both size keys.
                options.rows = 40; // The fit addon sets the shell size after xterm opens.
            }
            this.term = new terminalClass(options); // Create a fresh xterm instance for the selected session.
            this.fitAddon = new fitClass(); // Create the fit addon before shell geometry changes.
            if (!this.readOnly) this.term.loadAddon(this.fitAddon); // Load fit support only for resizable shell sessions.
            this.term.open(this.screen); // Attach xterm to the page screen element.
            this._loadSettings(); // Apply stored toolbar settings after xterm creation.
        }

        _wireTerminal() { // Connect xterm data to input delivery.
            this.term.onData(function(data) { // Listen for bytes that xterm emits from keys or paste.
                if (this.inputBlocked()) return; // Drop emitted bytes when the session cannot take input.
                if (this.pasteFlow.activePaste) this.pasteFlow.consumeData(data); // Route paste bytes through paste progress accounting.
                else this.sendQueue.enqueueText(data, { paste: false }); // Queue normal typed bytes without paste metadata.
            }.bind(this)); // Keep this bound inside the xterm data handler.
            this.keys = new TerminalKeys(this); // Create key handling after xterm exists.
            this.keys.bind(); // Attach keyboard shortcut handling to xterm.
        }

        _readLoop() { // Start one long-poll read for terminal output.
            if (this.stopped || !this.session) return; // Do not read after close or before a session opens.
            var generation = this.readGeneration; // Tie this read to the session that is open now.
            var abort = typeof AbortController === 'function' ? new AbortController() : null; // Let close() cancel this read.
            this.readAbort = abort; // Keep the handle that close() uses to cancel this read.
            var url = '/api/websockets/sessions/' + encodeURIComponent(this.session.session_id) + '/terminal'; // Build the read URL for the active session.
            url += '?after=' + encodeURIComponent(String(this.nextPosition)) + '&wait=' + this._readWaitSeconds(); // Request bytes after the last processed position.
            fetch(url, abort ? { signal: abort.signal } : {}).then(readJsonAnswer).then(function(payload) { // Start the long-poll request without blocking the page.
                if (generation !== this.readGeneration) return; // Drop the answer because the page closed that session.
                this._handleReadAnswer(payload); // Process the backend read response.
            }.bind(this)).catch(function() { // Convert network failure into the same error path.
                if (generation !== this.readGeneration) return; // A cancelled read of a closed session is not a failure.
                this._handleReadAnswer({ error: 'The portal did not answer.', code: 'network' }); // Report a network read failure through normal read handling.
            }.bind(this)); // Keep this bound inside the read failure callback.
        }

        _scheduleRead(delayMs) { // Start the next long-poll read after a delay.
            var generation = this.readGeneration; // Tie the timer to the session that is open now.
            window.setTimeout(function() { // Wait so an idle terminal does not flood the portal.
                if (generation === this.readGeneration) this._readLoop(); // A closed session must not start a second read loop.
            }.bind(this), delayMs); // Keep this bound inside the read timer.
        }

        _handleReadAnswer(payload) { // Handle one read route answer.
            if (this.stopped || !this.session) return; // Ignore a read answer after the session finished.
            if (payload.error) { // Handle read errors before applying terminal output.
                this._handleReadFailure(payload); // Process a failed read response.
                return; // Stop this path after scheduling failure handling.
            }
            this.readFailures = 0; // Reset transient read failure count after a successful read.
            this._applyReadPayload(payload); // Apply terminal output and metadata from the read response.
            if (FINAL_STATES.indexOf(payload.state) !== -1) { // Finish the session when the backend reports a final state.
                this._finish(payload); // Apply final-state cleanup and notification.
                return; // Stop after final-state cleanup.
            }
            this._scheduleRead(payload.data ? 0 : this._emptyReadDelayMs()); // Read again immediately after data, or wait briefly when idle.
        }

        _applyReadPayload(payload) { // Apply terminal output and metadata to the page.
            this.readOnly = payload.read_only === true; // Trust the backend read-only flag for the current session.
            if (this.term) this.term.options.disableStdin = this.inputBlocked(); // Disable xterm input whenever the session is blocked.
            this._applyReadOnlyUi(); // Refresh controls after read-only state changes.
            if (payload.data) this.term.write(this._base64Bytes(payload.data)); // Write decoded output bytes into xterm.
            this.nextPosition = payload.next === undefined ? this.nextPosition : payload.next; // Advance the next read position when the backend supplies it.
            this._showGap(payload.gap || 0); // Show a gap warning when the backend dropped old bytes.
            this._showExpiry(payload.expires_at); // Update the expiry warning from the backend timestamp.
            this.setStatus(this._statusText(payload)); // Refresh the footer with state and size.
            this._notifyState(payload, false); // Notify the page that the session is still live.
        }

        _handleReadFailure(payload) { // Handle terminal read failures.
            this.readFailures += 1; // Count this read failure for throttled error display.
            if (payload.code === 'not_found' || payload.code === 'not_terminal') { // Stop permanently when the backend rejects the session identity.
                this.showError(payload); // Show the unrecoverable session error.
                this.stopped = true; // Stop further reads for a missing terminal session.
                this.inputClosed = true; // Block input because no backend session can receive it.
                this._applyReadOnlyUi(); // Disable paste controls after unrecoverable read failure.
                if (this.term) this.term.options.disableStdin = true; // Disable xterm input after the session disappears.
                this.sendQueue.close(); // Discard queued input after unrecoverable read failure.
                if (this.resizeObserver) this.resizeObserver.disconnect(); // Stop resize observation after the terminal session disappears.
                return; // Stop this path after unrecoverable cleanup.
            }
            if (this.readFailures >= MAX_READ_FAILURES) this.showError(payload); // Show repeated read failures after the threshold.
            this._scheduleRead(1000); // Retry reading after a short delay.
        }

        _finish(payload) { // Finish a terminal session.
            this.stopped = true; // Stop the read loop after final state.
            this.inputClosed = true; // Close input while keeping shell warning text accurate.
            if (this.term) this.term.options.disableStdin = true; // Disable xterm input after session completion.
            this._applyReadOnlyUi(); // Refresh controls for the final state.
            this.setStatus(this._statusText(payload)); // Show final state details in the footer.
            this._notifyState(payload, true); // Notify the page that this terminal is no longer live.
            this.sendQueue.close(); // Drop queued input after session completion.
            if (this.resizeObserver) this.resizeObserver.disconnect(); // Stop resize observation for the completed session.
        }

        _notifyState(payload, final) { // Notify the host page of terminal state.
            this.onState({ // Send a compact state object to the host page.
                state: payload.state || 'live', // Report live when the backend omits a state.
                reason: payload.reason || '', // Pass through the backend finish reason when present.
                read_only: this.readOnly, // Report whether the current session is read-only.
                live: !final, // Mark the session live until final cleanup runs.
                terminal_next: this.nextPosition // Report the next read position to the host page.
            });
        }

        _fitAndResize(force) { // Fit the shell terminal and post geometry changes.
            if (this.readOnly) return; // Keep screen commands at the fixed Mist screen size.
            if (!this.fitAddon || !this.term) return; // Wait until xterm and fit support are both ready.
            this.fitAddon.fit(); // Fit the shell to the visible panel.
            if (this.inputClosed) return; // Skip resize POSTs after input closes.
            if (force || this.term.cols !== this.lastSize.cols || this.term.rows !== this.lastSize.rows) { // Send geometry only when it changed or is forced.
                this.lastSize = { cols: this.term.cols, rows: this.term.rows }; // Remember the posted shell geometry.
                this._postResize(this.term.cols, this.term.rows); // Post the new shell geometry to the backend.
            }
        }

        _startResizeObserver() { // Start watching shell terminal size changes.
            if (this.readOnly) return; // Skip resize watching for fixed screen sessions.
            if (!window.ResizeObserver) return; // Skip resize watching when the browser lacks observer support.
            this.resizeObserver = new ResizeObserver(function() { // Watch shell panel size changes after xterm attaches.
                if (this.resizeTimer) window.clearTimeout(this.resizeTimer); // Cancel the previous debounce before scheduling a new fit.
                this.resizeTimer = window.setTimeout(function() { this._fitAndResize(false); }.bind(this), 120); // Debounce resize updates so the backend gets stable geometry.
            }.bind(this)); // Keep this bound inside the resize observer callback.
            this.resizeObserver.observe(this.screen); // Observe only the terminal screen element.
        }

        _readWaitSeconds() { // Return the read long-poll wait value.
            return testHookValue('readWaitSeconds', READ_WAIT_SECONDS); // Allow tests to shorten the long-poll wait.
        }

        _emptyReadDelayMs() { // Return the idle read delay value.
            return testHookValue('emptyLiveReadDelayMs', EMPTY_LIVE_READ_DELAY_MS); // Allow tests to shorten idle-read delay.
        }

        _postResize(cols, rows) { // Send shell terminal geometry to the backend.
            if (!this.session || this.inputBlocked()) return; // Skip resize POSTs without a writable active session.
            this._postJson('/api/websockets/sessions/' + encodeURIComponent(this.session.session_id) + '/resize', { // Post shell geometry to the session resize route.
                cols: cols, // Send the current column count.
                rows: rows // Send the current row count.
            }).then(function(answer) { // Inspect the resize response for backend errors.
                if (answer && answer.error) this.showError(answer); // Show resize errors in the terminal footer.
            }.bind(this)); // Keep this bound inside the resize response callback.
        }

        _postJson(url, body) { // Send a JSON request to the portal.
            return fetch(url, { // Send a JSON POST to the portal.
                method: 'POST', // Use POST for terminal input and resize routes.
                headers: { // Send JSON headers with the CSRF token.
                    'Content-Type': 'application/json', // Tell the backend that the request body is JSON.
                    'X-CSRFToken': this._csrfToken() // Protect the request with the current CSRF token.
                },
                body: JSON.stringify(body) // Serialize the body before fetch sends it.
            }).then(readJsonAnswer).catch(function() { // Decode the JSON response through the shared helper.
                return { error: 'The portal did not answer. Check the network, then try again.', code: 'network' }; // Return a network error object when fetch fails.
            });
        }

        _csrfToken() { // Read the CSRF token for portal POST requests.
            if (window.getCsrfToken) return window.getCsrfToken(); // Use the global CSRF helper when the page supplies one.
            var meta = document.querySelector('meta[name="csrf-token"]'); // Find the CSRF meta tag as a fallback.
            return meta ? meta.getAttribute('content') : ''; // Return the meta tag token or an empty token.
        }

        _base64Bytes(data) { // Decode base64 terminal output bytes.
            var binary = window.atob(data); // Decode base64 text from the terminal read route.
            var bytes = new Uint8Array(binary.length); // Allocate a byte array for decoded terminal output.
            for (var index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index); // Copy decoded byte values in order for xterm.
            return bytes; // Return bytes that xterm can write directly.
        }

        _showGap(count) { // Show a warning when output bytes are missing.
            this.gap.textContent = count > 0 ? 'The portal no longer holds ' + count + ' terminal bytes.' : ''; // Show how many output bytes are no longer available.
            this.gap.classList.toggle('d-none', count <= 0); // Hide the gap notice when no bytes are missing.
        }

        _showExpiry(value) { // Show a near-expiration terminal warning.
            if (!value) { // Hide expiry notice when the backend sends no timestamp.
                this.expiry.classList.add('d-none'); // Hide old expiry text when no expiry value exists.
                return; // Stop after clearing the missing expiry notice.
            }
            var remaining = Date.parse(value) - Date.now(); // Compute time left until the backend expires the session.
            this.expiry.textContent = remaining <= 120000 && remaining > 0 ? 'This terminal expires at ' + value + '.' : ''; // Show expiry text only during the final two minutes.
            this.expiry.classList.toggle('d-none', !this.expiry.textContent); // Hide the expiry notice when no warning text is set.
        }

        _statusText(payload) { // Build footer status text.
            var size = this.term ? 'Size: ' + this.term.cols + ' x ' + this.term.rows : ''; // Read xterm size when a terminal exists.
            var stateValue = payload.state || 'live'; // Treat missing state as live for optimistic display.
            var stateLabel = this.stateText[stateValue] || stateValue; // Translate backend state with labels from the page.
            var state = 'State: ' + stateLabel; // Build the state portion of the footer.
            var reason = payload.reason ? 'Reason: ' + payload.reason : ''; // Add a reason only when the backend supplies one.
            return [state, size, reason].filter(Boolean).join(' | '); // Join non-empty footer parts for compact status text.
        }

        _errorMessage(answer) { // Convert backend error codes into operator messages.
            var messages = { // Define operator messages for known backend error codes.
                bad_request: 'The portal refused the terminal request.', // Explain a malformed terminal request.
                csrf_expired: 'The form token expired. Reload the page.', // Explain an expired form token.
                input_full: 'The terminal input queue is full.', // Explain a full input queue.
                network: 'The portal did not answer. Check the network, then try again.', // Explain a missing portal response.
                not_found: 'The terminal session is no longer available.', // Explain a missing terminal session.
                not_open: 'The terminal session is not open.', // Explain a session that is not open.
                not_terminal: 'This session has no terminal.', // Explain that the selected session has no terminal.
                rate_limited: 'The terminal is receiving input too quickly.', // Explain that input arrived faster than the backend accepts.
                read_only: 'This terminal is read-only.', // Explain that this terminal cannot accept input.
                too_large: 'The terminal input is too large.' // Explain that input exceeded the backend size limit.
            };
            return messages[answer.code] || answer.error || 'The terminal request failed.'; // Prefer known code text, then backend text, then a generic failure.
        }

        _loadSettings() { // Load saved toolbar settings.
            this.elements.copyOnSelect.checked = !!this.prefs.get('copyOnSelect'); // Reflect the saved copy-on-select setting in the checkbox.
            this.elements.confirmPaste.checked = !!this.prefs.get('confirmPaste'); // Reflect the saved paste-confirmation setting in the checkbox.
        }

        _saveSettings() { // Save toolbar settings.
            this.prefs.set('copyOnSelect', this.elements.copyOnSelect.checked); // Save the copy-on-select checkbox value.
            this.prefs.set('confirmPaste', this.elements.confirmPaste.checked); // Save the paste-confirmation checkbox value.
            this.showToast('Terminal settings saved.'); // Tell the operator that settings were saved.
            this.focusTerminal(); // Return focus to xterm after saving settings.
        }

        _changeFont(delta) { // Change the terminal font size.
            var next = Math.max(10, Math.min(28, Number(this.prefs.get('fontSize')) + delta)); // Limit font size to a usable range.
            this.prefs.set('fontSize', next); // Save the new terminal font size.
            if (this.term) { // Apply font changes only when xterm exists.
                this.term.options.fontSize = next; // Update the active terminal font size.
                this._fitAndResize(true); // Refit after font changes because columns can change.
            }
        }

        _copyOnSelect() { // Copy selected text after mouse selection.
            if (this.prefs.get('copyOnSelect') && this.term && this.term.hasSelection()) { // Copy selected text when the preference is active.
                this.clipboard.copySelection({ clearSelection: false }); // Copy without clearing the selected highlight.
            }
        }

        _dialogKey(event) { // Handle keys inside the paste dialog.
            if (event.key === 'Escape') this.pasteFlow.cancelPending(); // Cancel the paste dialog when Escape is pressed.
        }

        _downloadHistory() { // Download visible terminal history.
            if (!this.term || !this.session) return; // Skip history download when no terminal session is active.
            var buffer = this.term.buffer.active; // Read the active xterm scrollback buffer.
            var lines = []; // Collect terminal history lines for the file.
            for (var index = 0; index < buffer.length; index += 1) { // Walk each buffer row in order.
                var line = buffer.getLine(index); // Read one row from the xterm buffer.
                if (line) lines.push(line.translateToString(true)); // Add non-empty rows to the download text.
            }
            var blob = new Blob([lines.join('\n') + '\n'], { type: 'text/plain' }); // Build a text file from collected terminal lines.
            var link = document.createElement('a'); // Create a temporary link for browser download.
            link.href = URL.createObjectURL(blob); // Create a local object URL for the history file.
            link.download = this._downloadName(); // Set a safe file name for the download.
            document.body.appendChild(link); // Attach the link only long enough to click it.
            link.click(); // Start the local history download.
            URL.revokeObjectURL(link.href); // Release the object URL after download starts.
            document.body.removeChild(link); // Remove the temporary download link from the page.
            this.focusTerminal(); // Return focus to xterm after starting the download.
        }

        _downloadName() { // Build a safe terminal history file name.
            var label = (this.session.title || this.session.key || 'terminal').replace(/[^A-Za-z0-9_.-]+/g, '-'); // Sanitize the session title for a file name.
            var stamp = new Date().toISOString().replace(/[:.]/g, '-'); // Create a timestamp that is safe in file names.
            return label + '-' + stamp + '.txt'; // Return the sanitized terminal history file name.
        }

        _showPanel(visible) { // Show or hide the terminal panel.
            this.panel.classList.toggle('d-none', !visible); // Show or hide the terminal panel.
            this._applyReadOnlyUi(); // Refresh controls for the visible panel state.
            this.showToast(''); // Clear old toast text during panel visibility changes.
            this.hidePasteProgress(); // Hide any stale paste progress during panel changes.
            this.hidePasteDialog(); // Close paste dialog when the panel visibility changes.
        }
    }

    window.MistWebSocketTerminal = { // Expose the terminal controller to the operations portal.
        TerminalController: TerminalController, // Export the controller constructor for page code.
        testSupport: { // Expose small pure helpers for browser tests.
            splitText: function(text, limit) { // Expose input splitting for focused tests.
                var queue = new TerminalSendQueue({ session: null }); // Create a minimal queue for split tests.
                return queue._splitText(text, limit || SEND_PART_LIMIT); // Return split chunks with the production byte limit by default.
            },
            lineCount: function(text) { // Expose line counting for paste dialog tests.
                return terminalLineCount(text); // Return the same line count used by paste review.
            }
        }
    };
})();
