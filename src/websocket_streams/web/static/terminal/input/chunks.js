(function() { // Add UTF-8 safe input chunk helpers.
    'use strict'; // Fail fast when a name is misspelled.

    var terminal = window.MistWebSocketTerminal; // Read the shared terminal namespace.

    function utf8Length(text) { // Measure input in backend byte units.
        return new TextEncoder().encode(text).length; // Match the bytes that fetch sends.
    }

    function codePointLength(codePoint) { // Measure one Unicode code point.
        if (codePoint <= 0x7f) return 1; // ASCII uses one UTF-8 byte.
        if (codePoint <= 0x7ff) return 2; // This range uses two UTF-8 bytes.
        if (codePoint <= 0xffff) return 3; // This range uses three UTF-8 bytes.
        return 4; // Remaining code points use four UTF-8 bytes.
    }

    function splitUnicode(text, limit) { // Split mixed-byte text without breaking a character.
        var chunks = []; // Collect chunks in input order.
        var start = 0; // Mark the current chunk start.
        var currentLength = 0; // Count current chunk bytes.
        for (var index = 0; index < text.length;) { // Walk by Unicode code point.
            var codePoint = text.codePointAt(index); // Read the complete next character.
            var units = codePoint > 0xffff ? 2 : 1; // Advance over surrogate pairs together.
            var length = codePointLength(codePoint); // Measure this character before adding it.
            if (index > start && currentLength + length > limit) { // Close a full chunk before overflow.
                chunks.push(text.slice(start, index)); // Keep the complete chunk.
                start = index; // Start the next chunk at this character.
                currentLength = 0; // Reset the byte count.
            }
            currentLength += length; // Count this character in the active chunk.
            index += units; // Move to the next character boundary.
        }
        if (start < text.length) chunks.push(text.slice(start)); // Keep the final partial chunk.
        return chunks; // Return all chunks in source order.
    }

    function splitText(text, limit) { // Split terminal input within the request limit.
        if (/^[\x00-\x7F]*$/.test(text)) { // Use direct slicing for ASCII input.
            var chunks = []; // Collect fixed-size ASCII chunks.
            for (var index = 0; index < text.length; index += limit) chunks.push(text.slice(index, index + limit)); // Each ASCII character is one byte.
            return chunks; // Return ASCII chunks in input order.
        }
        return splitUnicode(text, limit); // Use character-safe splitting for other text.
    }

    terminal.Internal.inputChunks = { splitText: splitText, utf8Length: utf8Length }; // Publish input byte helpers.
    terminal.testSupport.splitText = function(text, limit) { // Expose production splitting for focused browser tests.
        return splitText(text, limit || terminal.constants.sendPartLimit); // Use the backend limit by default.
    };
})();
