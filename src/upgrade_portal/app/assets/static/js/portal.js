/*
 * portal.js - Upgrade Capture Portal shared browser helpers
 *
 * This file gives three things and nothing more.
 *   1. A helper that reads the cross-site request forgery token and puts it on
 *      a request.
 *   2. A small JSON fetch wrapper.
 *   3. A flash message region updater.
 *
 * The content security policy is 'self' only. The policy blocks an inline
 * script, so a page cannot call a function from a script attribute. Every
 * helper therefore hangs off one global object. A template attaches an event
 * with an external script only.
 *
 * The global object is `window.upgradePortal`. A later script adds a poller to
 * the same object.
 *
 * This file uses plain ES2020. It needs no bundler and no build step. It
 * imports nothing.
 */

(function () {
    "use strict";

    /* The server renders the token into this meta tag. The contract fixes both
     * the tag name and the header name. */
    var CSRF_META_NAME = "csrf-token";
    var CSRF_HEADER_NAME = "X-CSRFToken";

    /* The flash region carries this test identifier. The identifier contract
     * fixes the value, and a browser test selects by it. */
    var FLASH_REGION_TESTID = "flash-message";

    /* portal.css defines one class for each level. A level that is not in this
     * list falls back to `info`. */
    var FLASH_LEVEL_CLASSES = {
        info: "flash-info",
        success: "flash-success",
        warning: "flash-warning",
        danger: "flash-danger"
    };

    /* A GET request and a HEAD request never change state, so they need no
     * token. Every other method carries one. */
    var SAFE_METHODS = ["GET", "HEAD", "OPTIONS"];

    /**
     * Reads the cross-site request forgery token from the page.
     *
     * Why: The server never puts the token in a cookie that a script can read.
     * The server renders the token into a meta tag instead. Every caller needs
     * one place to find it, because a wrong tag name produces a 400 response
     * with the code `csrf_missing` and no other clue.
     *
     * @returns {string} The token value. Returns an empty string when the page
     *     holds no token tag.
     */
    function getCsrfToken() {
        var meta = document.querySelector('meta[name="' + CSRF_META_NAME + '"]');
        if (!meta) {
            return "";
        }
        return meta.getAttribute("content") || "";
    }

    /**
     * Copies a header set and adds the cross-site request forgery header.
     *
     * Why: A caller must not change the object it received. This helper returns
     * a new object, so a caller can reuse one header set for several requests.
     *
     * @param {Object} [headers] The headers to copy. May be undefined.
     * @returns {Object} A new header object that holds the token header.
     */
    function withCsrf(headers) {
        var result = Object.assign({}, headers || {});
        result[CSRF_HEADER_NAME] = getCsrfToken();
        return result;
    }

    /**
     * Builds an Error that carries the fields of the portal error envelope.
     *
     * Why: A caller needs the stable `code` value to decide what to do. A
     * caller must never match on the message text, because the message is a
     * plain sentence for the operator and can change. The status and the
     * details ride along for a log line.
     *
     * @param {number} status The HTTP status code.
     * @param {Object} [envelope] The parsed response body, if the body was JSON.
     * @returns {Error} An Error with `code`, `status`, and `details` properties.
     */
    function buildRequestError(status, envelope) {
        var payload = (envelope && envelope.error) || {};
        var code = payload.code || "request_failed";
        var message = payload.message || "The request failed.";
        var error = new Error(message);
        error.code = code;
        error.status = status;
        error.details = payload.details || null;
        return error;
    }

    /**
     * Sends a JSON request and returns the parsed body.
     *
     * Why: Every JSON call in this portal repeats the same four steps. It sends
     * the session cookie, it asks for JSON, it adds the token on a state
     * change, and it turns the error envelope into a thrown Error. One wrapper
     * keeps those four steps identical across every page, so a caller cannot
     * forget the token and cannot read the wrong error shape.
     *
     * @param {string} url The endpoint path.
     * @param {Object} [options] Extra fetch options. `method` defaults to GET.
     *     Pass a plain object as `body` and the wrapper serializes it.
     * @returns {Promise<Object|null>} The parsed body. Resolves to null when the
     *     response holds no content.
     * @throws {Error} An Error with a `code` property when the response status
     *     is not in the 200 range, or when the body is not valid JSON.
     */
    function fetchJson(url, options) {
        var settings = Object.assign({}, options || {});
        var method = (settings.method || "GET").toUpperCase();
        var headers = Object.assign({ Accept: "application/json" }, settings.headers || {});

        if (SAFE_METHODS.indexOf(method) === -1) {
            headers = withCsrf(headers);
        }

        /* A plain object becomes a JSON string here, so a caller never repeats
         * the serialize step and never forgets the content type. A caller that
         * already holds a string or a FormData keeps control of the body. */
        var body = settings.body;
        if (body && typeof body === "object" && !(body instanceof FormData)) {
            body = JSON.stringify(body);
            headers["Content-Type"] = "application/json";
        }

        settings.method = method;
        settings.headers = headers;
        settings.body = body;
        /* The session cookie must ride along. Without it every endpoint answers
         * 401 with the code `not_authenticated`. */
        settings.credentials = settings.credentials || "same-origin";

        return fetch(url, settings).then(function (response) {
            return response.text().then(function (text) {
                var parsed = null;
                if (text) {
                    try {
                        parsed = JSON.parse(text);
                    } catch (parseError) {
                        /* A proxy or a fault page can return HTML. The status
                         * alone then tells the caller what happened. */
                        if (response.ok) {
                            var badBody = new Error("The response was not JSON.");
                            badBody.code = "bad_response";
                            badBody.status = response.status;
                            badBody.details = null;
                            throw badBody;
                        }
                        throw buildRequestError(response.status, null);
                    }
                }
                if (!response.ok) {
                    throw buildRequestError(response.status, parsed);
                }
                return parsed;
            });
        });
    }

    /**
     * Finds the flash message region on the current page.
     *
     * Why: Every page renders the region with the same test identifier. One
     * lookup keeps the selector in a single place, so a template change needs
     * one edit here and no edit in a caller.
     *
     * @returns {Element|null} The region element, or null when the page holds
     *     no region.
     */
    function getFlashRegion() {
        return document.querySelector('[data-testid="' + FLASH_REGION_TESTID + '"]');
    }

    /**
     * Removes every message from the flash region.
     *
     * Why: A poller writes a new message every 30 seconds. Without a clear step
     * the region grows without limit and pushes the page content down.
     *
     * @returns {void}
     */
    function clearFlash() {
        var region = getFlashRegion();
        if (!region) {
            return;
        }
        region.textContent = "";
    }

    /**
     * Puts one message into the flash region.
     *
     * Why: The portal reports a lock takeover, a partial capture, and a stop
     * outcome from a script, not from a page reload. The operator needs the
     * same look for a message from a script and a message from the server. The
     * region carries an ARIA live value in the template, so a screen reader
     * reads the new text without a page change.
     *
     * @param {string} message The sentence for the operator.
     * @param {string} [level] One of `info`, `success`, `warning`, or `danger`.
     *     Defaults to `info`.
     * @param {boolean} [append] Set true to keep the messages that are already
     *     there. Defaults to false, which replaces them.
     * @returns {Element|null} The new message element, or null when the page
     *     holds no region or the message is empty.
     */
    function showFlash(message, level, append) {
        var region = getFlashRegion();
        if (!region || !message) {
            return null;
        }

        if (!append) {
            region.textContent = "";
        }

        var levelClass = FLASH_LEVEL_CLASSES[level] || FLASH_LEVEL_CLASSES.info;
        var item = document.createElement("div");
        item.className = "flash-item " + levelClass;
        /* The text goes in as text, never as markup. A message can hold a site
         * name or an error string from the cloud, and neither is trusted. */
        item.textContent = String(message);
        region.appendChild(item);
        return item;
    }

    /**
     * Shows a thrown request error in the flash region.
     *
     * Why: Almost every caller of fetchJson ends with the same two lines. This
     * helper keeps the wording and the level consistent, so one failed call
     * never looks different from another.
     *
     * @param {Error} error An Error from fetchJson.
     * @returns {Element|null} The new message element, or null when the page
     *     holds no region.
     */
    function showRequestError(error) {
        var text = (error && error.message) || "The request failed.";
        return showFlash(text, "danger");
    }

    /* The namespace is the only global this file creates. A later script adds
     * a poller to the same object. */
    window.upgradePortal = window.upgradePortal || {};
    window.upgradePortal.getCsrfToken = getCsrfToken;
    window.upgradePortal.withCsrf = withCsrf;
    window.upgradePortal.fetchJson = fetchJson;
    window.upgradePortal.getFlashRegion = getFlashRegion;
    window.upgradePortal.showFlash = showFlash;
    window.upgradePortal.showRequestError = showRequestError;
    window.upgradePortal.clearFlash = clearFlash;
})();
