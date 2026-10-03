/* global readJsonAnswer */ // Declare the shared JSON helper for browser checks.

(function() { // Create the shared terminal namespace before leaf modules load.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal = { Internal: {}, testSupport: {} }; // Expose one stable terminal namespace.
    terminal.constants = { // Keep terminal limits in one dependency-free leaf.
        emptyReadDelayMs: 250, // Back off after an empty live read.
        finalStates: ['stopped', 'finished', 'timed_out', 'failed'], // Stop reads only for final states.
        maxReadFailures: 5, // Hide transient read failures until the threshold.
        noOutputNoticeSeconds: 20, // Warn when a live device stays silent.
        pasteLimit: 256 * 1024, // Refuse paste text above 256 KiB.
        pasteProgressLimit: 16 * 1024, // Show progress for large paste operations.
        preferenceKey: 'misthelper.wsTerminal.prefs', // Use one local storage key.
        readWaitSeconds: 20, // Let terminal reads wait for device output.
        sendPartLimit: 4096, // Keep each input request within the backend limit.
        waitingNotice: 'The portal waits for the first output from the device.' // Explain the first output wait.
    };
    terminal.Internal.testHookValue = function(name, fallback) { // Read optional browser test timing overrides.
        var hooks = window.MistWebSocketTerminalTestHooks || {}; // Use an empty object outside tests.
        return hooks[name] === undefined ? fallback : hooks[name]; // Prefer an explicit test value.
    };
    terminal.Internal.lineCount = function(text) { // Count terminal paste lines consistently.
        if (!text) return 0; // Treat empty text as zero lines.
        return text.replace(/\r\n|\r|\n$/, '').split(/\r\n|\r|\n/).length; // Ignore one trailing line end.
    };
    terminal.testSupport.lineCount = terminal.Internal.lineCount; // Expose the production line counter for browser tests.
})();
