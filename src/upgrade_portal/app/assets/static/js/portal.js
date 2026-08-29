/*
 * portal.js - Upgrade Capture Portal shared browser helpers
 *
 * This file gives nine things and nothing more.
 *   1. A helper that reads the cross-site request forgery token and puts it on
 *      a request.
 *   2. A small JSON fetch wrapper.
 *   3. A flash message region updater.
 *   4. A browser-side table filter for the site list.
 *   5. A capture status poll that runs every 30 seconds, with a manual refresh.
 *   6. A run status poll that runs every 30 seconds, with a manual refresh.
 *   7. A typed-word gate that unlocks a button only for an exact word.
 *   8. The upgrade option save, the upgrade start, and the run stop.
 *   9. The site lock: the take, the takeover, the release, and a heartbeat that
 *      runs every 60 seconds.
 *
 * The content security policy is 'self' only. The policy blocks an inline
 * script, so a page cannot call a function from a script attribute. Every
 * helper therefore hangs off one global object, and this file attaches every
 * event listener itself.
 *
 * The global object is `window.upgradePortal`.
 *
 * The poll uses no server-sent event. Decision D3 of the plan fixes a 30-second
 * poll, because the existing event bus caps at 10 subscribers.
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

    /* The identifier contract fixes every value below. A browser test selects
     * by the same values. */
    var CAPTURE_PROGRESS_TESTID = "capture-progress";
    var CAPTURE_PERCENT_TESTID = "capture-progress-percent";
    var CAPTURE_START_TESTID = "capture-start-button";
    var CAPTURE_REFRESH_TESTID = "capture-refresh-button";
    var CAPTURE_TIER_TESTID = "capture-tier-select";
    var CAPTURE_VERIFIED_TESTID = "capture-verified-badge";
    var CAPTURE_PARTIAL_TESTID = "capture-partial-warning";
    var CAPTURE_IDENTIFIER_TESTID = "capture-identifier";
    var CAPTURE_SIZE_TESTID = "capture-size-bytes";
    var CAPTURE_ERROR_TESTID = "capture-error";
    /* Delta U1 adds the two controls below. contracts/ui-testids.md lines
     * 120-121 fix both values. The button starts a run for the site of the
     * verified pre-check, and the region names a refusal. */
    var CAPTURE_START_UPGRADE_TESTID = "capture-start-upgrade-button";
    var CAPTURE_START_UPGRADE_ERROR_TESTID = "capture-start-upgrade-error";

    /* The upgrade identifiers. The `Upgrade` section of contracts/ui-testids.md
     * fixes every value below. Delta U2 turned three controls into radio groups. */
    var UPGRADE_VERSION_TYPE_TESTIDS = [
        "upgrade-version-select-ap",
        "upgrade-version-select-switch",
        "upgrade-version-select-gateway"
    ];
    var UPGRADE_REBOOT_GROUP_TESTID = "upgrade-reboot-group";
    var UPGRADE_JUNOS_GROUP_TESTID = "upgrade-junos-file-action-group";
    var UPGRADE_STRATEGY_GROUP_TESTID = "upgrade-strategy-group";
    var UPGRADE_WARNING_TESTID = "upgrade-warning-list";
    var UPGRADE_SAVE_TESTID = "upgrade-options-save-button";
    var UPGRADE_CONFIRM_TESTID = "upgrade-confirm-input";
    var UPGRADE_START_TESTID = "upgrade-start-button";
    var UPGRADE_STATE_TESTID = "upgrade-state";
    var UPGRADE_REFRESH_TESTID = "upgrade-refresh-button";

    /* The stop identifiers. contracts/ui-testids.md lines 117-125 fix every
     * value except the third list, which FR-038f needs and the contract omits. */
    var STOP_BUTTON_TESTID = "stop-button";
    var STOP_INPUT_TESTID = "stop-confirm-input";
    var STOP_SUBMIT_TESTID = "stop-confirm-submit";
    var STOP_OUTCOME_TESTID = "stop-outcome";
    var STOP_MESSAGE_TESTID = "stop-outcome-message";
    var STOP_CANCELLED_TESTID = "stop-outcome-cancelled";
    var STOP_WRITING_TESTID = "stop-outcome-writing";
    var STOP_NO_CANCEL_TESTID = "stop-outcome-no-cancel";

    /* The lock identifiers. contracts/ui-testids.md lines 77-82 fix every value
     * below. */
    var LOCK_BANNER_TESTID = "lock-banner";
    var LOCK_TAKE_TESTID = "lock-take-button";
    var LOCK_INPUT_TESTID = "lock-confirm-input";
    var LOCK_SUBMIT_TESTID = "lock-confirm-submit";
    var LOCK_RELEASE_TESTID = "lock-release-button";
    var LOCK_ERROR_TESTID = "lock-error";

    /* contracts/site-lock.md line 92 fixes 60 seconds for the browser beat. The
     * lock lives 300 seconds, so four beats may fail before the lock expires. */
    var HEARTBEAT_SECONDS = 60;

    /* The three refusals the lock banner answers itself. Every other code falls
     * through to the shared flash region. */
    var LOCK_LOST_CODE = "lock_lost";
    var LOCK_CONFIRM_CODE = "confirmation_required";
    var LOCK_HELD_CODE = "site_locked";

    /* The two refusals that a run creation returns. The capture page names the
     * holder for the first and the live run for the second. upgrade.py lines
     * 140-162 fix both code strings. */
    var RUN_SITE_LOCKED_CODE = "site_locked";
    var RUN_ALREADY_RUNNING_CODE = "upgrade_already_running";

    /* The poll stops on these three states. The capture then never changes
     * again, so a further read would add load and would report the same body. */
    var FINISHED_STATES = ["verified", "failed", "write_failed"];

    /* The run poll stops on these three states. data-model.md section 4.1 ends
     * every path at one of them. */
    var RUN_FINISHED_STATES = ["complete", "stopped", "failed"];

    /* Each device cell of the run table carries one of these field names. The
     * value is the text to show when the run reports no value yet. The same
     * words sit in upgrade/progress.html, so a paint never changes the wording
     * that the first render used. */
    var RUN_DEVICE_FIELDS = {
        state: "pending",
        version_before: "unknown",
        version_target: "none",
        version_after: "not yet"
    };

    /* The version check badge of FR-051. upgrade/progress.html holds the same
     * two maps under the names version_check_class and version_check_text, so a
     * paint never changes the wording that the first render used. The three
     * words also sit in contracts/ui-testids.md line 135, because a test reads
     * the word and never the class. */
    var RUN_VERSION_CHECK_CLASSES = {
        version_match: "badge-verified",
        version_mismatch: "badge-failed",
        version_pending: "badge-partial"
    };
    var RUN_VERSION_CHECK_WORDS = {
        version_match: "Version matches",
        version_mismatch: "Version mismatch",
        version_pending: "Awaiting version"
    };

    /* The fallback of the badge. A token the page does not know reads as a
     * pending check, never as a match, because a wrong match would tell an
     * operator that a device carries firmware it does not carry. */
    var RUN_VERSION_PENDING = "version_pending";

    /* The status body carries the key lock only after the run loses the site
     * lock. runtime/runs.py copies the state word, the sentence, and the time,
     * and copies no other value. */
    var RUN_LOCK_LOST_STATE = "lost";

    /* The banner the run region builds for a lost lock. The attribute is a
     * script hook, so a second paint finds the first banner and adds no second
     * one. The identifier is a test hook. */
    var RUN_LOCK_BANNER_ATTR = "data-run-lock-banner";
    var RUN_LOCK_BANNER_TESTID = "upgrade-lock-banner";

    /* The sentence for a lock report that carries no sentence of its own. The
     * banner always needs words, because color is never the only signal. The
     * second half states that the work continues. A lost lock stops the portal
     * from writing to the site, and it never stops the upgrade. */
    var RUN_LOCK_LOST_TEXT =
        "This run no longer holds the site lock. The upgrade continues in the cloud, and the devices still reboot.";

    /* Decision D3 fixes 30 seconds. A page may name another value in the
     * attribute data-poll-seconds, which carries the deployment setting. */
    var DEFAULT_POLL_SECONDS = 30;
    var MILLISECONDS_PER_SECOND = 1000;
    var NOT_FOUND_STATUS = 404;

    /* A section name and a count name reach a CSS selector. The portal builds
     * both from a response body, so this pattern refuses any other character
     * before the name reaches the selector. */
    var SAFE_KEY = /^[a-z0-9_]+$/;

    /* A device MAC address reaches a CSS selector in the same way. data-model.md
     * section 3.3 writes the address in lower case with no separator. The
     * pattern also allows a separator, because a later release may keep one. It
     * allows no quotation mark and no bracket, so no value can end the selector
     * early. */
    var SAFE_DEVICE_KEY = /^[a-z0-9:._-]+$/;

    /* The interval handle of the running poll, or null. One page shows one
     * capture, so one handle is enough and a second start replaces the first. */
    var pollTimer = null;

    /* The interval handle of the run poll, or null. One page shows one run. */
    var runPollTimer = null;

    /* The interval handle of the lock heartbeat, or null. One page drives one
     * site, so one handle is enough and a second start replaces the first. */
    var lockBeatTimer = null;

    /* The count of beats that failed in a row. A single failure can be a passing
     * network fault, so the beat stops only after a run of them. */
    var lockBeatFailures = 0;

    /* Three failures span about three minutes at the 60 second beat, which is
     * long enough to ride out a brief fault and short enough that an operator
     * learns before the lock expires. */
    var LOCK_BEAT_FAILURE_LIMIT = 3;

    var LOCK_BEAT_STOPPED_MESSAGE =
        "The portal stopped renewing this site, because three renewals failed. Reload the page and take the site again.";

    /* The stored size needs one extra read, and the value never changes after
     * the capture is verified. This flag keeps that read to one call. */
    var storedSizeLoaded = false;

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

    /**
     * Finds one element by its test identifier.
     *
     * Why: The identifier contract fixes every value, so a test and this script
     * read the same attribute. One helper keeps the selector text in a single
     * place and stops a typing mistake in each caller.
     *
     * @param {string} name The test identifier value.
     * @param {Element|Document} [root] Where to search. Defaults to the document.
     * @returns {Element|null} The element, or null when the page holds none.
     */
    function byTestId(name, root) {
        var scope = root || document;
        return scope.querySelector('[data-testid="' + name + '"]');
    }

    /**
     * Writes plain text into an element, and does nothing when it is absent.
     *
     * Why: Every paint step below reads an element that a page may not hold.
     * A guard in each step would repeat the same two lines many times. The text
     * goes in as text, never as markup, because a value can carry a site name
     * or an error string from the cloud and neither is trusted.
     *
     * @param {Element|null} element The target element.
     * @param {*} value The value to show.
     * @returns {void}
     */
    function setText(element, value) {
        if (!element) {
            return;
        }
        element.textContent = String(value);
    }

    /**
     * Turns a percent value from the server into a whole number from 0 to 100.
     *
     * Why: The bar width and the ARIA value must stay inside the range that the
     * progress role allows. A value outside the range makes a screen reader
     * report a wrong position, and a width above 100 breaks the track.
     *
     * @param {*} value The percent value from the status body.
     * @returns {number} A whole number from 0 to 100. Returns 0 for a value
     *     that is not a number.
     */
    function clampPercent(value) {
        var number = Number(value);
        if (!isFinite(number) || number < 0) {
            return 0;
        }
        if (number > 100) {
            return 100;
        }
        return Math.round(number);
    }

    /**
     * Paints the state word of each capture section.
     *
     * Why: The status body names six sections, and the page renders one list
     * item for each. The list item identifier appends the section key without
     * any change, so this function needs no translation table.
     *
     * @param {Element} region The capture progress region.
     * @param {Object} [sections] The section map from the status body.
     * @returns {void}
     */
    function paintSections(region, sections) {
        if (!region || !sections) {
            return;
        }
        Object.keys(sections).forEach(function (key) {
            /* The key reaches a selector, and the key comes from a response
             * body. This test refuses any character that could change the
             * meaning of that selector. */
            if (!SAFE_KEY.test(key)) {
                return;
            }
            var item = byTestId("capture-section-" + key, region);
            if (!item) {
                return;
            }
            setText(item.querySelector("[data-section-state]"), sections[key]);
        });
    }

    /**
     * Paints the nine count values of the capture.
     *
     * Why: The operator compares these numbers against the inventory page
     * before an upgrade starts. A count that the body does not carry keeps the
     * value the server rendered, so the page never replaces a real number with
     * a zero.
     *
     * @param {Element} region The capture progress region.
     * @param {Object} [counts] The count map from the status body.
     * @returns {void}
     */
    function paintCounts(region, counts) {
        if (!region || !counts) {
            return;
        }
        Object.keys(counts).forEach(function (key) {
            /* The same selector guard as paintSections. See the note there. */
            if (!SAFE_KEY.test(key)) {
                return;
            }
            setText(region.querySelector('[data-capture-count="' + key + '"]'), counts[key]);
        });
    }

    /**
     * Paints the verified badge with a word and a color together.
     *
     * Why: WCAG 1.4.1 forbids color as the only signal. The badge therefore
     * changes its text and its class in the same step, so the two can never
     * disagree.
     *
     * @param {boolean} verified True when the portal read the capture back.
     * @returns {void}
     */
    function paintVerified(verified) {
        var badge = byTestId(CAPTURE_VERIFIED_TESTID);
        if (!badge) {
            return;
        }
        var isVerified = verified === true;
        badge.className = "portal-badge " + (isVerified ? "badge-verified" : "badge-partial");
        badge.textContent = isVerified ? "Verified" : "Not verified";

        /* FR-101 reveals the upgrade path once the capture verifies. The button
         * ships hidden, so a fresh capture that verifies through the poll shows
         * the control with no reload. A not-verified poll hides it again. */
        var upgradeButton = byTestId(CAPTURE_START_UPGRADE_TESTID);
        if (upgradeButton) {
            upgradeButton.hidden = !isVerified;
        }
    }

    /**
     * Shows or hides the partial capture caution, and lists each reason.
     *
     * Why: A partial capture still writes a document, so nothing stops the
     * operator. The operator must know which section is short before a
     * comparison uses this capture.
     *
     * @param {Array} [reasons] The partial reason list. Each entry may hold
     *     `section`, `reason`, and `http_status`.
     * @returns {void}
     */
    function paintPartial(reasons) {
        var box = byTestId(CAPTURE_PARTIAL_TESTID);
        if (!box) {
            return;
        }
        var items = Array.isArray(reasons) ? reasons : [];
        /* The hidden property is a DOM property, not a style attribute. The
         * content security policy blocks the attribute in the markup only. */
        box.hidden = items.length === 0;

        var list = box.querySelector("[data-partial-list]");
        if (!list) {
            return;
        }
        list.textContent = items
            .map(function (entry) {
                if (!entry || typeof entry !== "object") {
                    return String(entry);
                }
                var section = entry.section || "unknown section";
                var reason = entry.reason || "no reason";
                return section + ": " + reason + ".";
            })
            .join(" ");
    }

    /**
     * Shows one fault message in the capture error region.
     *
     * Why: A failed poll must not go into the flash region. The flash region
     * carries a page message, and the fault belongs next to the capture it
     * describes. The stylesheet prepends the signal word "Warning:", so the
     * text here states the consequence only.
     *
     * @param {string} text The sentence for the operator.
     * @returns {void}
     */
    function showCaptureError(text) {
        var box = byTestId(CAPTURE_ERROR_TESTID);
        if (!box) {
            return;
        }
        box.textContent = String(text);
        box.hidden = false;
    }

    /**
     * Hides the capture error region and empties it.
     *
     * Why: A poll that works after a failed poll must clear the old fault.
     * Without this step the page keeps a stale message that no longer holds.
     *
     * @returns {void}
     */
    function clearCaptureError() {
        var box = byTestId(CAPTURE_ERROR_TESTID);
        if (!box) {
            return;
        }
        box.textContent = "";
        box.hidden = true;
    }

    /**
     * Paints one status body onto the capture page.
     *
     * Why: The server renders the same seven fields when the page loads, and
     * the poll paints the same seven fields after that. One function covers
     * every field, so a server render and a poll can never disagree.
     *
     * @param {Element} region The capture progress region.
     * @param {Object} status The body of GET /api/captures/<id>/status.
     * @returns {void}
     */
    function paintCaptureStatus(region, status) {
        if (!region || !status) {
            return;
        }

        setText(region.querySelector('[data-capture-field="state"]'), status.state || "pending");

        var percent = clampPercent(status.percent);
        setText(byTestId(CAPTURE_PERCENT_TESTID, region), percent + "%");

        var track = region.querySelector('[data-capture-field="track"]');
        if (track) {
            track.setAttribute("aria-valuenow", String(percent));
        }

        var bar = region.querySelector('[data-capture-field="bar"]');
        if (bar) {
            /* The style property of an element is not the style attribute of
             * the markup. The content security policy blocks the attribute and
             * leaves this property alone. */
            bar.style.width = percent + "%";
        }

        paintSections(region, status.sections);
        paintCounts(region, status.counts);
        setText(region.querySelector('[data-capture-field="message"]'), status.message || "");
        paintPartial(status.partial_reasons);
        paintVerified(status.verified);

        if (status.capture_id) {
            /* The identifier field sits in the Result card, and that card sits
             * outside this region. A search of the region finds nothing, so
             * this read covers the whole document, as the stored size does. */
            setText(byTestId(CAPTURE_IDENTIFIER_TESTID), status.capture_id);
        }
    }

    /**
     * Reads the capture identifier that the page carries.
     *
     * Why: The page holds no identifier before the operator starts a capture.
     * The poll must then stay quiet, because a request with an empty identifier
     * answers 404 every 30 seconds.
     *
     * @param {Element} region The capture progress region.
     * @returns {string} The identifier, or an empty string.
     */
    function readCaptureId(region) {
        if (!region) {
            return "";
        }
        return (region.getAttribute("data-capture-id") || "").trim();
    }

    /**
     * Reads the poll period of the page in milliseconds.
     *
     * Why: Decision D3 fixes 30 seconds, and a deployment may need another
     * value. The page carries the value, so no rebuild of this file is needed
     * to change it.
     *
     * @param {Element} region The capture progress region.
     * @returns {number} The period in milliseconds.
     */
    function readPollMilliseconds(region) {
        var seconds = DEFAULT_POLL_SECONDS;
        if (region) {
            var declared = Number(region.getAttribute("data-poll-seconds"));
            if (isFinite(declared) && declared > 0) {
                seconds = declared;
            }
        }
        return seconds * MILLISECONDS_PER_SECOND;
    }

    /**
     * Stops the running capture poll.
     *
     * Why: The poll must end when the capture reaches a final state and when
     * the capture is gone. A poll that never stops holds a timer for as long as
     * the page stays open and asks the server for a body that never changes.
     *
     * @returns {void}
     */
    function stopCapturePoll() {
        if (pollTimer !== null) {
            window.clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    /**
     * Reads the stored size of a verified capture and paints it.
     *
     * Why: FR-032b asks the portal to record the stored size, because retention
     * is unlimited. The status body does not carry the size, so the page needs
     * one more read. The whole capture endpoint answers 409 while the capture is
     * not verified, so this read waits for the verified state and then runs once.
     *
     * @param {string} captureId The capture identifier.
     * @returns {Promise<null>} Resolves after the paint. Never rejects.
     */
    function loadStoredSize(captureId) {
        if (storedSizeLoaded || !captureId) {
            return Promise.resolve(null);
        }
        storedSizeLoaded = true;
        return fetchJson("/api/captures/" + encodeURIComponent(captureId))
            .then(function (capture) {
                if (capture && capture.stored_size_bytes !== undefined) {
                    setText(byTestId(CAPTURE_SIZE_TESTID), capture.stored_size_bytes);
                }
                return null;
            })
            .catch(function (error) {
                /* The size is extra information. A failed read must not hide
                 * the capture result, so the page keeps the rendered value.
                 * The log carries the stable code and the status only. It
                 * carries no session value and no email address. */
                console.error("The stored size read failed.", error && error.code, error && error.status);
                storedSizeLoaded = false;
                return null;
            });
    }

    /**
     * Reads the capture status once and paints the page.
     *
     * Why: The manual refresh control and the 30-second poll must do the same
     * work. One function covers both, so the two can never drift apart.
     *
     * @param {Element} region The capture progress region.
     * @returns {Promise<Object|null>} The status body, or null on a fault.
     */
    function refreshCaptureStatus(region) {
        var captureId = readCaptureId(region);
        if (!captureId) {
            return Promise.resolve(null);
        }
        return fetchJson("/api/captures/" + encodeURIComponent(captureId) + "/status")
            .then(function (status) {
                clearCaptureError();
                paintCaptureStatus(region, status);
                if (status && FINISHED_STATES.indexOf(status.state) !== -1) {
                    stopCapturePoll();
                    /* A capture that failed leaves nothing to compare, so the
                     * operator must be able to start a second one. */
                    if (status.state !== "verified") {
                        var startButton = byTestId(CAPTURE_START_TESTID);
                        if (startButton) {
                            startButton.disabled = false;
                        }
                    }
                }
                if (status && status.verified === true) {
                    return loadStoredSize(captureId).then(function () {
                        return status;
                    });
                }
                return status;
            })
            .catch(function (error) {
                /* The log carries the stable code and the status only. It
                 * carries no session value and no email address. */
                console.error("The capture status read failed.", error && error.code, error && error.status);
                showCaptureError((error && error.message) || "The portal cannot read the capture state.");
                /* A capture that is gone never returns, so a further read
                 * would fail in the same way every 30 seconds. */
                if (error && error.status === NOT_FOUND_STATUS) {
                    stopCapturePoll();
                }
                return null;
            });
    }

    /**
     * Starts the 30-second capture poll.
     *
     * Why: The portal sends no server-sent event. Decision D3 of the plan fixes
     * a poll, because the existing event bus caps at 10 subscribers. A second
     * call replaces the first timer, so a restart never leaves two timers.
     *
     * @param {Element} region The capture progress region.
     * @returns {void}
     */
    function startCapturePoll(region) {
        stopCapturePoll();
        if (!region || !readCaptureId(region)) {
            return;
        }
        pollTimer = window.setInterval(function () {
            refreshCaptureStatus(region);
        }, readPollMilliseconds(region));
    }

    /**
     * Starts a capture and begins the poll.
     *
     * Why: The endpoint answers 202 with the new identifier, so the page must
     * read the body. A plain form would move the browser to a new page and
     * would lose that body. The button carries the three body fields, so this
     * function reads no page state of its own.
     *
     * @param {Element} button The start button.
     * @param {Element} region The capture progress region.
     * @returns {Promise<Object|null>} The 202 body, or null on a fault.
     */
    function startCapture(button, region) {
        var siteId = (button.getAttribute("data-site-id") || "").trim();
        if (!siteId) {
            showCaptureError("The page names no site, so the capture cannot start.");
            return Promise.resolve(null);
        }

        var tierSelect = byTestId(CAPTURE_TIER_TESTID);
        var runId = (button.getAttribute("data-run-id") || "").trim();
        var payload = {
            tier: tierSelect ? Number(tierSelect.value) : 2,
            run_id: runId || null,
            role: button.getAttribute("data-role") || "pre"
        };

        /* The button stays disabled until the answer arrives. A second click
         * would start a second capture of the same site. */
        button.disabled = true;
        clearCaptureError();

        return fetchJson("/api/sites/" + encodeURIComponent(siteId) + "/captures", {
            method: "POST",
            body: payload
        })
            .then(function (created) {
                if (region && created && created.capture_id) {
                    region.setAttribute("data-capture-id", created.capture_id);
                    /* The identifier field sits outside this region, so the
                     * read covers the whole document. The operator then reads
                     * the name of the capture before the first poll answers. */
                    setText(byTestId(CAPTURE_IDENTIFIER_TESTID), created.capture_id);
                    storedSizeLoaded = false;
                    refreshCaptureStatus(region);
                    startCapturePoll(region);
                }
                if (created && created.lock) {
                    /* The start took the site lock on this call, so the banner
                     * must show the hold and the beat must begin. FR-107 and
                     * FR-110 ask for both with no reload. A read-only page has
                     * no banner, so the paint runs only when the region exists. */
                    var lockRegion = getLockRegion();
                    if (lockRegion) {
                        paintLockHeld(lockRegion, created.lock);
                        paintLockCooldown(lockRegion, 0);
                        startLockBeat(lockRegion);
                    }
                }
                showFlash("The capture started. The page reads the state every 30 seconds.", "success");
                return created;
            })
            .catch(function (error) {
                /* The log carries the stable code and the status only. It
                 * carries no session value and no email address. */
                console.error("The capture start failed.", error && error.code, error && error.status);
                button.disabled = false;
                showCaptureError((error && error.message) || "The capture did not start.");
                return null;
            });
    }

    /**
     * Writes one refusal into the start-upgrade error region.
     *
     * Why: FR-104 and FR-105 ask the region to name the cause. The region sits
     * beside the button, so the operator reads the refusal next to the control
     * that caused it and not in the shared flash region.
     *
     * @param {string} text The sentence for the operator.
     * @returns {void}
     */
    function showCaptureUpgradeError(text) {
        var box = byTestId(CAPTURE_START_UPGRADE_ERROR_TESTID);  /* One region for the two refusals. */
        if (!box) {  /* A page with no verified capture renders no region. */
            return;  /* Nothing to write, so the call ends. */
        }
        box.textContent = String(text);  /* Text, never markup, so a holder address stays inert. */
    }

    /**
     * Builds the sentence that a run-creation refusal shows.
     *
     * Why: FR-104 names the holder and FR-105 names the live run. The server
     * message stays generic, and the identifier rides in the details, so this
     * helper joins the two into one sentence the operator can act on.
     *
     * @param {Error} error An Error from fetchJson.
     * @returns {string} The sentence for the region.
     */
    function nameCaptureUpgradeRefusal(error) {
        var code = (error && error.code) || "";  /* The stable code decides the wording. */
        var details = (error && error.details) || {};  /* The identifier rides here, not in the message. */
        var message = (error && error.message) || "The upgrade could not start.";  /* The generic sentence. */
        if (code === RUN_SITE_LOCKED_CODE && details.actor_email) {  /* A second operator holds the site. */
            return message + " The holder is " + details.actor_email + ".";  /* FR-104 names that operator. */
        }
        if (code === RUN_ALREADY_RUNNING_CODE && details.run_id) {  /* One run of this site has not finished. */
            return message + " The open run is " + details.run_id + ".";  /* FR-105 names that run. */
        }
        return message;  /* Any other fault keeps the plain server sentence. */
    }

    /**
     * Creates a run for the site of this capture and opens the options page.
     *
     * Why: FR-101 offers an upgrade from a verified pre-check. FR-102 asks the
     * portal to create the run through the site endpoint and to carry the new
     * run identifier to the options page. The server adopts the pre-check, so
     * the browser sends no capture identifier.
     *
     * @param {Element} button The start-upgrade button. It names the site.
     * @returns {Promise<Object|null>} The 201 body, or null on a refusal.
     */
    function startUpgradeFromCapture(button) {
        var siteId = (button.getAttribute("data-site-id") || "").trim();  /* The path names the site. */
        if (!siteId) {  /* A page with no site cannot post the run. */
            showCaptureUpgradeError("The page names no site, so the upgrade cannot start.");  /* The operator reads why. */
            return Promise.resolve(null);  /* No call runs without a site. */
        }

        button.disabled = true;  /* A second click would create a second run of the same site. */
        showCaptureUpgradeError("");  /* A fresh try clears the last refusal. */

        return fetchJson("/api/sites/" + encodeURIComponent(siteId) + "/runs", {
            method: "POST",  /* The create endpoint reads no body beyond the token header. */
            body: {}  /* The server adopts the pre-check, so the browser sends no fields. */
        })
            .then(function (created) {  /* The 201 body carries the new run identifier. */
                var runId = (created && created.run_id) || "";  /* FR-102 carries this value onward. */
                if (runId) {  /* A run with an identifier owns an options page. */
                    window.location.assign("/runs/" + encodeURIComponent(runId) + "/options");  /* Opens that page. */
                    return created;  /* The browser leaves this page, so nothing else runs. */
                }
                button.disabled = false;  /* A body with no run leaves the button ready to retry. */
                showCaptureUpgradeError("The portal created no run, so the upgrade did not start.");  /* States the gap. */
                return created;  /* The caller sees the empty answer. */
            })
            .catch(function (error) {  /* A 409 or a 503 lands here as an Error. */
                /* The log carries the stable code and the status only. It
                 * carries no session value and no email address. */
                console.error("The upgrade start failed.", error && error.code, error && error.status);  /* No address. */
                button.disabled = false;  /* The refusal leaves the button ready to retry. */
                showCaptureUpgradeError(nameCaptureUpgradeRefusal(error));  /* Names the holder or the live run. */
                return null;  /* The caller reads the failure. */
            });
    }

    /**
     * Hides each table row that does not match the search text.
     *
     * Why: The site list of one organization fits in one page. A server filter
     * would cost one round trip for each key press. contracts/http-api.md keeps
     * the `q` argument on GET /api/sites available for a later list that does
     * not fit in one page.
     *
     * The row carries the text to match in data-filter-text, so the filter never
     * reads the markup of a cell and a hidden column can still match.
     *
     * @param {Element} input The search field. It names the table in
     *     data-filter-target.
     * @returns {void}
     */
    function applyTableFilter(input) {
        var targetId = input.getAttribute("data-filter-target");
        var target = targetId ? document.getElementById(targetId) : null;
        if (!target) {
            return;
        }

        var needle = (input.value || "").trim().toLowerCase();
        var rows = target.querySelectorAll("[data-filter-text]");
        var shown = 0;

        Array.prototype.forEach.call(rows, function (row) {
            var haystack = (row.getAttribute("data-filter-text") || "").toLowerCase();
            var matches = !needle || haystack.indexOf(needle) !== -1;
            /* The hidden property is a DOM property, not a style attribute. */
            row.hidden = !matches;
            if (matches) {
                shown += 1;
            }
        });

        /* The empty row explains an empty table. It stays hidden when the table
         * holds no row at all, because the table then shows its own note. */
        var empty = target.querySelector("[data-filter-empty]");
        if (empty) {
            empty.hidden = shown !== 0 || rows.length === 0;
        }
    }

    /**
     * Arms every search field that names a table.
     *
     * Why: The content security policy blocks an inline script, so a page
     * cannot carry an oninput attribute. This file must attach every listener.
     *
     * @returns {void}
     */
    function initTableFilters() {
        var inputs = document.querySelectorAll("[data-filter-target]");
        Array.prototype.forEach.call(inputs, function (input) {
            input.addEventListener("input", function () {
                applyTableFilter(input);
            });
            /* A browser can restore a typed value after a back step, so the
             * filter runs once at load and the list matches the field. */
            applyTableFilter(input);
        });
    }

    /**
     * Arms the capture page controls and starts the poll.
     *
     * Why: The same reason as initTableFilters. The page carries no script
     * attribute, so this file attaches the start listener, the refresh
     * listener, and the timer.
     *
     * @returns {void}
     */
    function initCapturePage() {
        var region = byTestId(CAPTURE_PROGRESS_TESTID);
        if (!region) {
            return;
        }

        var startButton = byTestId(CAPTURE_START_TESTID);
        if (startButton) {
            startButton.addEventListener("click", function () {
                startCapture(startButton, region);
            });
        }

        /* FR-040 requires a manual refresh control. The poll waits 30 seconds,
         * and this control reads the state at once. */
        var refreshButton = byTestId(CAPTURE_REFRESH_TESTID);
        if (refreshButton) {
            refreshButton.addEventListener("click", function () {
                refreshCaptureStatus(region);
            });
        }

        /* FR-101 offers the upgrade path once the capture verifies. The button
         * renders for a verified capture alone, so a page that never verified
         * carries no listener here. */
        var startUpgradeButton = byTestId(CAPTURE_START_UPGRADE_TESTID);
        if (startUpgradeButton) {
            startUpgradeButton.addEventListener("click", function () {
                startUpgradeFromCapture(startUpgradeButton);
            });
        }

        startCapturePoll(region);
    }

    /**
     * Writes the reason a typed-word gate stays locked.
     *
     * Why: The stylesheet shows the typed text in capital letters. An operator
     * who types lower case therefore sees capital letters and gets no clue why
     * the button stays locked. FR-034 rejects a different letter case, so the
     * page must say that plainly. An empty field needs no message, because the
     * operator has typed nothing yet.
     *
     * @param {Element} input The confirmation field.
     * @param {string} typed The text the operator typed.
     * @param {string} word The word that unlocks the button.
     * @param {boolean} matches True when the typed text equals the word.
     * @returns {void}
     */
    function paintConfirmHint(input, typed, word, matches) {
        var hintId = input.getAttribute("data-confirm-hint-for") || "";
        var hint = hintId ? document.getElementById(hintId) : null;
        if (!hint) {
            return;
        }
        if (matches || typed === "") {
            setText(hint, "");
            return;
        }
        if (typed.toUpperCase() === word.toUpperCase()) {
            setText(hint, "Type the word in capital letters.");
            return;
        }
        setText(hint, "The typed word does not match " + word + ".");
    }

    /**
     * Locks or unlocks the button that one confirmation field guards.
     *
     * Why: FR-033 and FR-034 ask for an exact word before a state change. The
     * customer asked for a box the operator must type a word into before a
     * shaded-out begin button unlocks. The word sits in the markup, so this
     * function holds no word of its own and one page can hold two gates with
     * two different words.
     *
     * A disabled field means the page locked the gate for another reason, such
     * as a missing pre-check capture. The button then stays locked and the
     * server-rendered reason stays on the page.
     *
     * @param {Element} input The confirmation field. It names the word in
     *     data-confirm-word and the button in data-confirm-target.
     * @returns {boolean} True when the button is now unlocked.
     */
    function applyConfirmGate(input) {
        var button = byTestId(input.getAttribute("data-confirm-target") || "");
        if (!button) {
            return false;
        }
        if (input.disabled) {
            button.disabled = true;
            return false;
        }

        var word = (input.getAttribute("data-confirm-word") || "").trim();
        var typed = input.value || "";
        var matches = word !== "" && typed === word;
        button.disabled = !matches;
        paintConfirmHint(input, typed, word, matches);
        return matches;
    }

    /**
     * Arms every typed-word gate on the page.
     *
     * Why: The content security policy blocks an inline script, so a page
     * cannot carry an oninput attribute. The gate also runs once at load,
     * because a browser can restore a typed value after a back step and the
     * button must then match the field.
     *
     * @returns {void}
     */
    function initConfirmGates() {
        var inputs = document.querySelectorAll("[data-confirm-word]");
        Array.prototype.forEach.call(inputs, function (input) {
            input.addEventListener("input", function () {
                applyConfirmGate(input);
            });
            applyConfirmGate(input);
        });
    }

    /**
     * Writes one version into every device that offers it.
     *
     * Why: A site holds many devices of the same model. Choosing one version
     * for each device by hand is slow and invites a mistake. A device whose
     * model does not offer the version keeps its own value, because the cloud
     * refuses a version that the model cannot take.
     *
     * @param {Element} allSelect The apply-to-every-device control.
     * @returns {number} The count of devices that took the version.
     */
    function applyVersionToDeviceType(typeSelect) {
        var wanted = (typeSelect.value || "").trim();
        var deviceType = (typeSelect.getAttribute("data-version-type") || "").trim();
        if (!wanted) {
            return 0;
        }

        var changed = 0;
        var selects = document.querySelectorAll("[data-version-for]");
        Array.prototype.forEach.call(selects, function (select) {
            if (select.getAttribute("data-device-type") !== deviceType) {
                return;
            }
            var offered = false;
            Array.prototype.forEach.call(select.options, function (option) {
                if (option.value === wanted) {
                    offered = true;
                }
            });
            if (offered) {
                select.value = wanted;
                changed += 1;
            }
        });
        return changed;
    }

    /**
     * Collects the target list for the upgrade option body.
     *
     * Why: contracts/http-api.md lines 209-216 fix the body shape. A device
     * with an empty version leaves the list, because an empty version means
     * that the operator does not want to upgrade that device.
     *
     * @returns {Array<Object>} One entry for each device to upgrade.
     */
    function collectUpgradeTargets() {
        var targets = [];
        var selects = document.querySelectorAll("[data-version-for]");
        Array.prototype.forEach.call(selects, function (select) {
            var version = (select.value || "").trim();
            var mac = (select.getAttribute("data-version-for") || "").trim();
            if (version && mac) {
                targets.push({ mac: mac, version_target: version });
            }
        });
        return targets;
    }

    /**
     * Replaces the plan warning list with the sentences from an answer.
     *
     * Why: The plan warns about a mixed family and a mixed version. Each
     * sentence enters as text and never as markup, because a warning can carry
     * a model name from the cloud and that name is not trusted.
     *
     * @param {Array<string>} warnings The sentences from the answer.
     * @returns {void}
     */
    function paintUpgradeWarnings(warnings) {
        var list = byTestId(UPGRADE_WARNING_TESTID);
        if (!list) {
            return;
        }

        var lines = Array.isArray(warnings) ? warnings : [];
        list.textContent = "";
        if (lines.length === 0) {
            var empty = document.createElement("li");
            empty.textContent = "The plan found no warning.";
            list.appendChild(empty);
            return;
        }
        lines.forEach(function (line) {
            var item = document.createElement("li");
            item.textContent = String(line);
            list.appendChild(item);
        });
    }

    /**
     * Reads the value of the checked radio inside a group.
     *
     * Why: Delta U2 turned three single-choice controls into radio groups. A
     * group shows every choice at once, and the browser keeps exactly one radio
     * checked. The saved body still needs the one chosen value, so this helper
     * reads it. A group with no checked radio returns the fallback, so a save
     * never sends an empty choice.
     *
     * @param {string} groupTestId The data-testid of the radio group container.
     * @param {string} fallback The default value when no radio is checked.
     * @returns {string} The value of the checked radio, or the fallback.
     */
    function checkedRadioValue(groupTestId, fallback) {
        var group = byTestId(groupTestId);  /* The fieldset holds the radios of one choice. */
        if (!group) {
            return fallback;  /* The page drew no group, so the caller keeps the default. */
        }
        var chosen = group.querySelector('input[type="radio"]:checked');  /* The DOM marks one radio. */
        return chosen ? chosen.value : fallback;  /* The one checked option, or the default. */
    }

    /**
     * Saves the upgrade options and moves to the confirmation page.
     *
     * Why: The endpoint answers with the planned targets and the warnings, so
     * the page must read the body. A plain form would move the browser at once
     * and would lose that body.
     *
     * @param {Element} button The save button. It carries data-run-id and
     *     data-next-url.
     * @returns {Promise<Object|null>} The answer body, or null on a fault.
     */
    function saveUpgradeOptions(button) {
        var runId = (button.getAttribute("data-run-id") || "").trim();
        if (!runId) {
            showFlash("The page names no run, so the options cannot be saved.", "danger");
            return Promise.resolve(null);
        }

        var rebootChoice = checkedRadioValue(UPGRADE_REBOOT_GROUP_TESTID, "yes");  /* Reboot defaults to yes. */
        var junosChoice = checkedRadioValue(UPGRADE_JUNOS_GROUP_TESTID, "no");  /* Junos action defaults to no. */
        var strategyChoice = checkedRadioValue(UPGRADE_STRATEGY_GROUP_TESTID, "big_bang");  /* Strategy defaults to big bang. */
        var payload = {
            targets: collectUpgradeTargets(),
            reboot: rebootChoice === "yes",  /* The saved field stays a boolean. */
            junos_file_action: junosChoice === "yes",  /* The saved field stays a boolean. */
            strategy: strategyChoice  /* The saved field stays the strategy string. */
        };

        /* The button stays disabled until the answer arrives. A second click
         * would send a second plan for the same run. */
        button.disabled = true;

        return fetchJson("/api/runs/" + encodeURIComponent(runId) + "/options", {
            method: "POST",
            body: payload
        })
            .then(function (answer) {
                paintUpgradeWarnings(answer && answer.warnings);
                var nextUrl = (button.getAttribute("data-next-url") || "").trim();
                if (nextUrl) {
                    window.location.assign(nextUrl);
                    return answer;
                }
                button.disabled = false;
                showFlash("The portal saved the upgrade options.", "success");
                return answer;
            })
            .catch(function (error) {
                /* The log carries the stable code and the status only. It
                 * carries no session value and no email address. */
                console.error("The option save failed.", error && error.code, error && error.status);
                button.disabled = false;
                showRequestError(error);
                return null;
            });
    }

    /**
     * Arms the upgrade options page.
     *
     * Why: The content security policy blocks an inline script, so this file
     * attaches the two listeners the page needs.
     *
     * @returns {void}
     */
    function initUpgradeOptionsPage() {
        var saveButton = byTestId(UPGRADE_SAVE_TESTID);
        if (saveButton) {
            saveButton.addEventListener("click", function () {
                saveUpgradeOptions(saveButton);
            });
        }

        UPGRADE_VERSION_TYPE_TESTIDS.forEach(function (testId) {
            var typeSelect = byTestId(testId);
            if (typeSelect) {
                typeSelect.addEventListener("change", function () {
                    applyVersionToDeviceType(typeSelect);
                });
                applyVersionToDeviceType(typeSelect);
            });
        });
    }

    /**
     * Starts the upgrade and moves to the run page.
     *
     * Why: contracts/http-api.md line 294 fixes the body as the confirm field
     * with the word CONFIRM. The typed text goes to the server as it stands, so
     * the server checks the word a second time. A gate in a browser is a
     * courtesy and never a control.
     *
     * @param {Element} button The begin button.
     * @param {Element} input The confirmation field.
     * @returns {Promise<Object|null>} The 202 body, or null on a fault.
     */
    function startUpgrade(button, input) {
        var runId = (button.getAttribute("data-run-id") || "").trim();
        if (!runId) {
            showFlash("The page names no run, so the upgrade cannot start.", "danger");
            return Promise.resolve(null);
        }

        /* The button locks again at once. A second click would send a second
         * start for the same run. */
        button.disabled = true;

        return fetchJson("/api/runs/" + encodeURIComponent(runId) + "/start", {
            method: "POST",
            body: { confirm: input ? input.value || "" : "" }
        })
            .then(function (started) {
                var runUrl = (button.getAttribute("data-progress-url") || "").trim();
                if (runUrl) {
                    window.location.assign(runUrl);
                    return started;
                }
                showFlash("The upgrade started.", "success");
                return started;
            })
            .catch(function (error) {
                /* The log carries the stable code and the status only. It
                 * carries no session value and no email address. */
                console.error("The upgrade start failed.", error && error.code, error && error.status);
                showRequestError(error);
                /* The gate decides the button state again, so a correct word
                 * still unlocks the button after a failed start. */
                if (input) {
                    applyConfirmGate(input);
                }
                return null;
            });
    }

    /**
     * Arms the upgrade confirmation page.
     *
     * Why: The gate itself comes from initConfirmGates, which serves every
     * typed-word box. This step adds the one listener that starts the work.
     *
     * @returns {void}
     */
    function initUpgradeConfirmPage() {
        var startButton = byTestId(UPGRADE_START_TESTID);
        var confirmInput = byTestId(UPGRADE_CONFIRM_TESTID);
        if (!startButton) {
            return;
        }
        startButton.addEventListener("click", function () {
            startUpgrade(startButton, confirmInput);
        });
    }

    /**
     * Reads the run identifier of the run status region.
     *
     * Why: The region carries the identifier, so no function below needs a
     * global and a test can point the poll at another run.
     *
     * @param {Element} region The run status region.
     * @returns {string} The identifier, or an empty string.
     */
    function readRunId(region) {
        if (!region) {
            return "";
        }
        return (region.getAttribute("data-run-id") || "").trim();
    }

    /**
     * Builds the settled count sentence of one phase.
     *
     * Why: A bare pair of numbers does not say what the numbers count. A phase
     * that reports no total needs its own words, because a division by zero
     * would show a wrong percent. upgrade/progress.html renders the same three
     * sentences, so the first render and every paint agree.
     *
     * @param {Object} phase One entry of the phases list.
     * @returns {string} The sentence for the count cell.
     */
    function phaseProgressText(phase) {
        var total = Number(phase.total);
        var settled = Number(phase.settled);
        if (isFinite(total) && total > 0) {
            if (!isFinite(settled)) {
                settled = 0;
            }
            return settled + " of " + total + " settled";
        }
        if (phase.state === "settled") {
            return "All settled";
        }
        return "Not started";
    }

    /**
     * Paints the state, the count, and the note of each cascade phase.
     *
     * Why: The cascade order is fixed and the page already holds one row for
     * each phase. A paint that rebuilt the rows would move the focus of an
     * operator who is reading the list. The phase name reaches a selector, so
     * the name passes the safe pattern first.
     *
     * The note writes empty text when the phase carries none. An empty element
     * matches the `:empty` rule and leaves the grid, so a phase that met no
     * fault shows no note row.
     *
     * @param {Element} region The run status region.
     * @param {Object} status The status body.
     * @returns {void}
     */
    function paintRunPhases(region, status) {
        var phases = (status && status.phases) || [];
        if (!Array.isArray(phases)) {
            return;
        }
        phases.forEach(function (phase) {
            var name = phase && phase.name;
            if (!name || !SAFE_KEY.test(name)) {
                return;
            }
            var prefix = '[data-run-phase="' + name + '"]';
            setText(region.querySelector(prefix + '[data-run-field="state"]'), phase.state || "waiting");
            setText(region.querySelector(prefix + '[data-run-field="progress"]'), phaseProgressText(phase));
            setText(region.querySelector(prefix + '[data-run-field="note"]'), phase.note || "");
        });
    }

    /**
     * Paints the state and the versions of each device in the run.
     *
     * Why: FR-041 asks for the state of each device and FR-050 asks for the
     * version before and after. The page already holds one row for each device,
     * so the paint writes into the cells and never rebuilds the table. The MAC
     * address reaches a selector, so the address passes the safe pattern first.
     *
     * @param {Element} region The run status region.
     * @param {Object} status The status body.
     * @returns {void}
     */
    function paintRunTargets(region, status) {
        var targets = (status && status.targets) || [];
        if (!Array.isArray(targets)) {
            return;
        }
        targets.forEach(function (device) {
            var mac = device && device.mac;
            if (!mac || !SAFE_DEVICE_KEY.test(mac)) {
                return;
            }
            var prefix = '[data-run-device="' + mac + '"]';
            Object.keys(RUN_DEVICE_FIELDS).forEach(function (field) {
                var cell = region.querySelector(prefix + '[data-run-field="' + field + '"]');
                var value = device[field];
                if (value === null || value === undefined || value === "") {
                    value = RUN_DEVICE_FIELDS[field];
                }
                setText(cell, value);
            });
        });
    }

    /**
     * Returns one version string in the form the comparison needs.
     *
     * Why: A device may report " 23.4R2.13 " with a space at each end, and the
     * cloud may change the letter case between two reads. upgrade/gate.py runs
     * the same two steps in normalize_version, and upgrade/progress.html runs
     * them with the filters trim and lower. All three must agree, or a device
     * that carries the right firmware reads as a mismatch.
     *
     * @param {*} value The version value from the status body.
     * @returns {string} The version in lower case with no space at either end.
     */
    function normalizeVersion(value) {
        if (value === null || value === undefined) {
            return "";
        }
        return String(value).trim().toLowerCase();
    }

    /**
     * Returns the version check token of one device.
     *
     * Why: The settle gate writes version_outcome onto the row once it reads a
     * version, and writes nothing before that. A run that started before the
     * gate ran still needs the badge, so the painter falls back to the same
     * comparison that upgrade/progress.html makes at page load. Without the
     * fallback the badge would read one word on the first render and another
     * on the first poll.
     *
     * @param {Object} device One target row of the status body.
     * @returns {string} One of the three version check tokens.
     */
    function runVersionOutcome(device) {
        if (device.version_outcome) {
            return String(device.version_outcome);
        }
        var requested = normalizeVersion(device.version_target);
        var reported = normalizeVersion(device.version_after);
        if (!requested || !reported) {
            return RUN_VERSION_PENDING;
        }
        return requested === reported ? "version_match" : "version_mismatch";
    }

    /**
     * Paints the version check badge of each device in the run.
     *
     * Why: FR-051 asks the page to compare the version a device reports against
     * the version the run asked for. A device can report the job complete and
     * still return on its old firmware. The badge is not a field cell, because
     * a field paint replaces the whole text of a cell and would drop the badge.
     * The badge therefore needs this painter of its own. Without it the badge
     * holds its page-load word until a full reload, so a device that finished
     * during a poll keeps reading "Awaiting version".
     *
     * @param {Element} region The run status region.
     * @param {Object} status The status body.
     * @returns {void}
     */
    function paintRunVersionChecks(region, status) {
        var targets = (status && status.targets) || [];
        if (!Array.isArray(targets)) {
            return;
        }
        targets.forEach(function (device) {
            var mac = device && device.mac;
            if (!mac || !SAFE_DEVICE_KEY.test(mac)) {
                return;
            }
            var badge = region.querySelector('[data-run-version-check="' + mac + '"]');
            if (!badge) {
                return;
            }
            var outcome = runVersionOutcome(device);
            badge.className = "portal-badge " + (RUN_VERSION_CHECK_CLASSES[outcome] || "badge-partial");
            badge.textContent = RUN_VERSION_CHECK_WORDS[outcome] || RUN_VERSION_CHECK_WORDS.version_pending;
        });
    }

    /**
     * Returns the banner of the run region, and builds it on the first call.
     *
     * Why: upgrade/progress.html holds no banner for a lost lock, and the
     * content security policy blocks an inline script that could add one. The
     * painter therefore builds the element. The two classes are the ones
     * portal.css already styles, so the banner reads "Warning:" before the
     * sentence and never signals with color alone. The banner opens the region,
     * because an operator who lost the site must read that before the phases.
     *
     * @param {Element} region The run status region.
     * @returns {Element} The banner element.
     */
    function runLockBanner(region) {
        var banner = region.querySelector("[" + RUN_LOCK_BANNER_ATTR + "]");
        if (banner) {
            return banner;
        }
        banner = document.createElement("div");
        banner.setAttribute(RUN_LOCK_BANNER_ATTR, "");
        banner.setAttribute("data-testid", RUN_LOCK_BANNER_TESTID);
        /* The role alert makes a reader announce the banner at once. The region
         * itself is polite, which would hold the note until the reader rests. */
        banner.setAttribute("role", "alert");
        /* The banner warns, and it never reports a failure. A lost lock stops
         * the portal from writing to the site. It does not stop the upgrade,
         * because the cloud already holds the order. A red banner reads as a
         * failed upgrade, and the operator then walks away from devices that
         * still reboot. */
        banner.className = "flash-item flash-warning";
        region.insertBefore(banner, region.firstChild);
        return banner;
    }

    /**
     * Returns the sentence the lock banner shows.
     *
     * Why: The server writes one sentence for a takeover and another sentence
     * for a lock store that stopped answering. The banner repeats the sentence
     * of the server, so the two never disagree. A report with no sentence still
     * needs words, so a fallback sentence covers it.
     *
     * The time rides in a sentence that names no second loss. Both server
     * sentences already state that the run lost the lock, and a repeat of that
     * fact would read as a second fault.
     *
     * @param {Object} lock The lock report of the status body.
     * @returns {string} One sentence for the operator.
     */
    function runLockSentence(lock) {
        var text = String(lock.message || RUN_LOCK_LOST_TEXT);
        var at = String(lock.at || "");
        if (!at) {
            return text;
        }
        return text + " The portal recorded the loss at " + at + ".";
    }

    /**
     * Paints the banner that reports a lost site lock.
     *
     * Why: The driver notes the loss on the run record when another operator
     * takes the site, or when the lock store stops answering. Nothing showed
     * that note, so an operator whose site was taken read a run that looked
     * healthy. A run that still holds its lock builds no element at all, so a
     * healthy page carries no empty banner.
     *
     * @param {Element} region The run status region.
     * @param {Object} status The status body.
     * @returns {void}
     */
    function paintRunLock(region, status) {
        var lock = status && status.lock;
        var lost = !!lock && lock.state === RUN_LOCK_LOST_STATE;
        var banner = region.querySelector("[" + RUN_LOCK_BANNER_ATTR + "]");
        if (!lost && !banner) {
            return;
        }
        banner = banner || runLockBanner(region);
        banner.textContent = lost ? runLockSentence(lock) : "";
        banner.hidden = !lost;
    }

    /**
     * Paints the whole run status region from one status body.
     *
     * Why: The manual refresh control and the 30-second poll must paint the
     * same way. One function covers both, so the two can never drift apart.
     *
     * @param {Element} region The run status region.
     * @param {Object} status The status body.
     * @returns {void}
     */
    function paintRunStatus(region, status) {
        if (!region || !status) {
            return;
        }

        setText(byTestId(UPGRADE_STATE_TESTID, region), status.state || "created");
        setText(region.querySelector('[data-run-field="message"]'), status.message || "");
        setText(region.querySelector('[data-run-field="pre_capture_id"]'), status.pre_capture_id || "None saved");
        setText(region.querySelector('[data-run-field="post_capture_id"]'), status.post_capture_id || "None saved");

        paintRunPhases(region, status);
        paintRunTargets(region, status);
        paintRunVersionChecks(region, status);
        paintRunLock(region, status);

        /* A run that finished answers 409 to a stop, so the two stop controls
         * lock. A control that leads only to an error is worse than no control. */
        if (RUN_FINISHED_STATES.indexOf(status.state) !== -1) {
            var stopButton = byTestId(STOP_BUTTON_TESTID);
            if (stopButton) {
                stopButton.disabled = true;
            }
            var stopSubmit = byTestId(STOP_SUBMIT_TESTID);
            if (stopSubmit) {
                stopSubmit.disabled = true;
            }
        }
    }

    /**
     * Stops the running run poll.
     *
     * Why: A run in a final state never changes again, so a further read would
     * add load and would report the same body.
     *
     * @returns {void}
     */
    function stopRunPoll() {
        if (runPollTimer !== null) {
            window.clearInterval(runPollTimer);
            runPollTimer = null;
        }
    }

    /**
     * Reads the run status once and paints the page.
     *
     * Why: FR-039 asks for a refresh every 30 seconds and FR-040 asks for a
     * manual refresh. Both call this function.
     *
     * @param {Element} region The run status region.
     * @returns {Promise<Object|null>} The status body, or null on a fault.
     */
    function refreshRunStatus(region) {
        var runId = readRunId(region);
        if (!runId) {
            return Promise.resolve(null);
        }
        return fetchJson("/api/runs/" + encodeURIComponent(runId) + "/status")
            .then(function (status) {
                paintRunStatus(region, status);
                if (status && RUN_FINISHED_STATES.indexOf(status.state) !== -1) {
                    stopRunPoll();
                }
                return status;
            })
            .catch(function (error) {
                /* The log carries the stable code and the status only. It
                 * carries no session value and no email address. */
                console.error("The run status read failed.", error && error.code, error && error.status);
                showRequestError(error);
                /* A run that is gone never returns, so a further read would
                 * fail in the same way every 30 seconds. */
                if (error && error.status === NOT_FOUND_STATUS) {
                    stopRunPoll();
                }
                return null;
            });
    }

    /**
     * Starts the 30-second run poll.
     *
     * Why: The portal sends no server-sent event. Decision D3 of the plan fixes
     * a poll, because the existing event bus caps at 10 subscribers. A second
     * call replaces the first timer, so a restart never leaves two timers.
     *
     * @param {Element} region The run status region.
     * @returns {void}
     */
    function startRunPoll(region) {
        stopRunPoll();
        if (!region || !readRunId(region)) {
            return;
        }
        runPollTimer = window.setInterval(function () {
            refreshRunStatus(region);
        }, readPollMilliseconds(region));
    }

    /**
     * Arms the run page controls and starts the poll.
     *
     * Why: The content security policy blocks an inline script, so this file
     * attaches the refresh listener and the timer.
     *
     * @returns {void}
     */
    function initRunPage() {
        var region = document.querySelector("[data-run-region]");
        if (!region) {
            return;
        }

        /* FR-040 requires a manual refresh control. The poll waits 30 seconds,
         * and this control reads the state at once. */
        var refreshButton = byTestId(UPGRADE_REFRESH_TESTID);
        if (refreshButton) {
            refreshButton.addEventListener("click", function () {
                refreshRunStatus(region);
            });
        }

        startRunPoll(region);
    }

    /**
     * Fills one list of MAC addresses in the stop outcome.
     *
     * Why: The three lists paint in the same way, and an empty list needs a
     * sentence of its own. An empty list with no text reads as a fault. Each
     * address enters as text and never as markup.
     *
     * @param {Element|null} list The list element.
     * @param {Array<string>} values The addresses from the answer.
     * @param {string} emptyText The sentence for an empty list.
     * @returns {void}
     */
    function paintMacList(list, values, emptyText) {
        if (!list) {
            return;
        }
        var items = Array.isArray(values) ? values : [];
        list.textContent = "";
        if (items.length === 0) {
            var empty = document.createElement("li");
            empty.textContent = emptyText;
            list.appendChild(empty);
            return;
        }
        items.forEach(function (value) {
            var item = document.createElement("li");
            item.className = "cell-mono";
            item.textContent = String(value);
            list.appendChild(item);
        });
    }

    /**
     * Paints the outcome of a stop and opens the outcome region.
     *
     * Why: The cloud states that a cancel is best effort. FR-038e and FR-038f
     * ask the portal to name each device it cancelled, each device that keeps
     * writing, and each device with no cancel path. The plain sentence from the
     * server leads, because it says the whole result in one line.
     *
     * @param {Object} outcome The outcome object from the answer.
     * @returns {void}
     */
    function paintStopOutcome(outcome) {
        var region = byTestId(STOP_OUTCOME_TESTID);
        if (!region || !outcome) {
            return;
        }

        setText(byTestId(STOP_MESSAGE_TESTID, region), outcome.message || "");
        paintMacList(byTestId(STOP_CANCELLED_TESTID, region), outcome.cancelled, "The portal canceled no device.");
        paintMacList(byTestId(STOP_WRITING_TESTID, region), outcome.already_writing, "No device writes firmware.");
        paintMacList(
            byTestId(STOP_NO_CANCEL_TESTID, region),
            outcome.no_cancel_available,
            "Every device has a cancel path."
        );

        /* The hidden property is a DOM property, not a style attribute. The
         * content security policy blocks a style attribute. */
        region.hidden = false;
    }

    /**
     * Asks the server to stop the run and paints the outcome.
     *
     * Why: contracts/http-api.md line 268 fixes the body as the confirm field
     * with the word STOP. The typed text goes to the server as it stands, so
     * the server checks the word a second time.
     *
     * @param {Element} button The stop submit button.
     * @param {Element} input The stop confirmation field.
     * @returns {Promise<Object|null>} The answer body, or null on a fault.
     */
    function requestRunStop(button, input) {
        var runId = (button.getAttribute("data-run-id") || "").trim();
        if (!runId) {
            showFlash("The page names no run, so the stop cannot be sent.", "danger");
            return Promise.resolve(null);
        }

        /* The button locks again at once. A second click would send a second
         * stop for the same run. */
        button.disabled = true;

        return fetchJson("/api/runs/" + encodeURIComponent(runId) + "/stop", {
            method: "POST",
            body: { confirm: input ? input.value || "" : "" }
        })
            .then(function (answer) {
                paintStopOutcome(answer && answer.outcome);
                if (answer && answer.state) {
                    setText(byTestId(UPGRADE_STATE_TESTID), answer.state);
                }
                var openButton = byTestId(STOP_BUTTON_TESTID);
                if (openButton) {
                    openButton.disabled = true;
                }
                showFlash("The portal sent the stop request.", "warning");
                return answer;
            })
            .catch(function (error) {
                /* The log carries the stable code and the status only. It
                 * carries no session value and no email address. */
                console.error("The stop request failed.", error && error.code, error && error.status);
                showRequestError(error);
                /* The gate decides the button state again, so a correct word
                 * still unlocks the button after a failed stop. */
                if (input) {
                    applyConfirmGate(input);
                }
                return null;
            });
    }

    /**
     * Arms the stop control of the run page.
     *
     * Why: FR-038a asks for a stop control while the run is live. The first
     * press only opens the box that holds the typed word, so one press starts
     * no work. The gate itself comes from initConfirmGates.
     *
     * @returns {void}
     */
    function initStopControl() {
        var region = document.querySelector("[data-stop-region]");
        if (!region) {
            return;
        }

        var openButton = byTestId(STOP_BUTTON_TESTID, region);
        var box = region.querySelector("[data-stop-form]");
        var input = byTestId(STOP_INPUT_TESTID, region);
        if (openButton && box) {
            openButton.addEventListener("click", function () {
                box.hidden = false;
                openButton.setAttribute("aria-expanded", "true");
                if (input) {
                    input.focus();
                }
            });
        }

        var submitButton = byTestId(STOP_SUBMIT_TESTID, region);
        if (submitButton) {
            submitButton.addEventListener("click", function () {
                requestRunStop(submitButton, input);
            });
        }
    }

    /**
     * Finds the lock banner of the current page.
     *
     * Why: A page that only reads carries no banner, and contracts/site-lock.md
     * line 128 states that a read needs no lock. Every lock helper therefore
     * starts here and does nothing when the banner is absent.
     *
     * @returns {Element|null} The banner element, or null.
     */
    function getLockRegion() {
        return document.querySelector("[data-lock-region]");
    }

    /**
     * Writes one lock refusal into the banner, or clears the region.
     *
     * Why: A lock refusal belongs beside the control that caused it. The shared
     * flash region is wrong for it, because another part of the page may call
     * clearFlash and erase the reason the button stays locked.
     *
     * @param {Element} region The lock banner.
     * @param {string} message The sentence to show. An empty string hides it.
     * @returns {void}
     */
    function showLockError(region, message) {
        var target = byTestId(LOCK_ERROR_TESTID, region);
        if (!target) {
            return;
        }
        setText(target, message);
        /* The hidden property is a DOM property, not a style attribute. The
         * content security policy blocks a style attribute. */
        target.hidden = message === "";
    }

    /**
     * Builds the lock path of one site.
     *
     * Why: The three lock calls share one path, and contracts/http-api.md
     * section 3 fixes it. The site identifier reaches a URL, so it goes through
     * encodeURIComponent and never into the path unchanged.
     *
     * @param {Element} region The lock banner. It names the site.
     * @returns {string} The path, or an empty string when the site is unknown.
     */
    function lockPath(region) {
        var siteId = (region.getAttribute("data-site-id") || "").trim();
        if (!siteId) {
            return "";
        }
        return "/api/sites/" + encodeURIComponent(siteId) + "/lock";
    }

    /**
     * Paints the banner for a lock this browser now holds.
     *
     * Why: The take button and the release button never both apply. The token
     * also lands on the banner, because the heartbeat reads it from there and
     * needs no closure of its own.
     *
     * @param {Element} region The lock banner.
     * @param {Object} grant The answer of a granted lock.
     * @returns {void}
     */
    function paintLockHeld(region, grant) {
        region.setAttribute("data-lock-state", "held");
        region.setAttribute("data-lock-token", (grant && grant.lock_token) || "");
        setText(region.querySelector("[data-lock-message]"), "You hold this site.");
        showLockError(region, "");

        var takeButton = byTestId(LOCK_TAKE_TESTID, region);
        if (takeButton) {
            takeButton.hidden = true;
        }
        var releaseButton = byTestId(LOCK_RELEASE_TESTID, region);
        if (releaseButton) {
            releaseButton.hidden = false;
        }
        var box = region.querySelector("[data-lock-confirm-box]");
        if (box) {
            box.hidden = true;
        }
    }

    /**
     * Paints the banner for a site this browser no longer holds.
     *
     * Why: A lost lock and a released lock leave the page in the same state.
     * One painter therefore serves both, and the heartbeat stops in both cases
     * because the token is gone.
     *
     * @param {Element} region The lock banner.
     * @param {string} message The sentence to show in the banner.
     * @returns {void}
     */
    function paintLockFree(region, message) {
        region.setAttribute("data-lock-state", "free");
        region.setAttribute("data-lock-token", "");
        setText(region.querySelector("[data-lock-message]"), message);

        var takeButton = byTestId(LOCK_TAKE_TESTID, region);
        if (takeButton) {
            takeButton.hidden = false;
        }
        var releaseButton = byTestId(LOCK_RELEASE_TESTID, region);
        if (releaseButton) {
            releaseButton.hidden = true;
        }
        stopLockBeat();
    }

    /**
     * Opens the typed-word box and names the word the server asked for.
     *
     * Why: FR-079 asks a different operator for the word CONFIRM. FR-080 asks
     * the same operator, returning to an abandoned session, for the word
     * continue. The server names the word in details.needed_text, so the page
     * shows the word the server will accept and never a guess.
     *
     * @param {Element} region The lock banner.
     * @param {string} word The word the server named.
     * @returns {void}
     */
    function openLockConfirm(region, word) {
        var box = region.querySelector("[data-lock-confirm-box]");
        var input = byTestId(LOCK_INPUT_TESTID, region);
        if (!box || !input) {
            return;
        }
        if (word) {
            input.setAttribute("data-confirm-word", word);
            setText(region.querySelector("[data-lock-word]"), word);
        }
        box.hidden = false;
        var takeButton = byTestId(LOCK_TAKE_TESTID, region);
        if (takeButton) {
            takeButton.setAttribute("aria-expanded", "true");
        }
        /* The typed value may already sit in the field after a back step, so the
         * gate runs once against the word the server just named. */
        applyConfirmGate(input);
        input.focus();
    }

    /**
     * Shows how long the wait lasts before a takeover becomes possible.
     *
     * Why: FR-078 gives an abandoned session a 5 minute cooldown. An operator
     * who waits with no number on the page reloads over and over, which adds
     * load and tells that operator nothing.
     *
     * @param {Element} region The lock banner.
     * @param {number} seconds The seconds left. Zero hides the region.
     * @returns {void}
     */
    function paintLockCooldown(region, seconds) {
        var note = region.querySelector("[data-lock-cooldown]");
        if (!note) {
            return;
        }
        var value = Number(seconds) || 0;
        setText(region.querySelector("[data-lock-cooldown-value]"), String(value));
        note.hidden = value <= 0;
    }

    /**
     * Turns one lock refusal into the banner state it names.
     *
     * Why: Three refusals need three different answers on the page. A
     * confirmation_required refusal opens the typed-word box. A site_locked
     * refusal names the holder and the wait. A lock_lost refusal means this
     * browser holds nothing, so the beat must stop.
     *
     * @param {Element} region The lock banner.
     * @param {Error} error The error that fetchJson threw.
     * @returns {void}
     */
    function handleLockRefusal(region, error) {
        var code = (error && error.code) || "";
        var details = (error && error.details) || {};
        showLockError(region, (error && error.message) || "The lock request failed.");

        if (code === LOCK_CONFIRM_CODE) {
            openLockConfirm(region, details.needed_text || "");
            return;
        }
        if (code === LOCK_HELD_CODE) {
            region.setAttribute("data-lock-state", "locked");
            paintLockCooldown(region, details.cooldown_remaining);
            return;
        }
        if (code === LOCK_LOST_CODE) {
            paintLockFree(region, "You no longer hold this site. Take the site again.");
        }
    }

    /**
     * Asks the server for the lock on this site.
     *
     * Why: FR-076 gives the site to exactly one session owner. One call serves
     * the plain take, the resume, and the takeover, because the server reads the
     * typed word and decides which of the three applies.
     *
     * @param {Element} region The lock banner.
     * @param {string} [confirmText] The word the operator typed, if any.
     * @returns {Promise<Object|null>} The grant, or null on a refusal.
     */
    function requestSiteLock(region, confirmText) {
        var path = lockPath(region);
        if (!path) {
            showLockError(region, "The page names no site, so the lock cannot be taken.");
            return Promise.resolve(null);
        }

        return fetchJson(path, { method: "POST", body: { confirm: confirmText || "" } })
            .then(function (grant) {
                paintLockHeld(region, grant);
                paintLockCooldown(region, 0);
                startLockBeat(region);
                return grant;
            })
            .catch(function (error) {
                /* The log carries the stable code and the status only. It
                 * carries no lock token and no email address. */
                console.error("The lock request failed.", error && error.code, error && error.status);
                handleLockRefusal(region, error);
                return null;
            });
    }

    /**
     * Gives the site back at once.
     *
     * Why: contracts/site-lock.md line 105 releases the lock when a run finishes.
     * A release also serves an operator who stops early, because the next
     * operator then waits no cooldown at all.
     *
     * @param {Element} region The lock banner.
     * @returns {Promise<Object|null>} The answer body, or null on a refusal.
     */
    function releaseSiteLock(region) {
        var path = lockPath(region);
        var token = region.getAttribute("data-lock-token") || "";
        if (!path || !token) {
            paintLockFree(region, "This browser holds no lock on this site.");
            return Promise.resolve(null);
        }

        stopLockBeat();
        return fetchJson(path, { method: "DELETE", body: { lock_token: token } })
            .then(function (answer) {
                paintLockFree(region, "You released this site. Another operator may take it now.");
                showLockError(region, "");
                return answer;
            })
            .catch(function (error) {
                console.error("The lock release failed.", error && error.code, error && error.status);
                handleLockRefusal(region, error);
                return null;
            });
    }

    /**
     * Sends one heartbeat for the lock this browser holds.
     *
     * Why: contracts/site-lock.md line 92 asks the browser for a beat every 60
     * seconds. The beat is what tells the portal that the session is alive, and
     * FR-078 treats a silent session as abandoned after 5 minutes.
     *
     * A lock store that does not answer leaves the beat running, because the
     * failure table retries for 60 seconds before it stops. A lock_lost
     * answer stops the beat, because this browser then holds nothing to renew.
     *
     * @param {Element} region The lock banner.
     * @returns {Promise<Object|null>} The answer body, or null on a refusal.
     */
    function beatSiteLock(region) {
        var path = lockPath(region);
        var token = region.getAttribute("data-lock-token") || "";
        if (!path || !token) {
            stopLockBeat();
            return Promise.resolve(null);
        }

        return fetchJson(path + "/heartbeat", { method: "POST", body: { lock_token: token } })
            .then(function (answer) {
                lockBeatFailures = 0;  /* A good beat clears the count, so only a run of failures stops the beat. */
                showLockError(region, "");
                return answer;
            })
            .catch(function (error) {
                console.error("The lock heartbeat failed.", error && error.code, error && error.status);
                lockBeatFailures += 1;  /* Count this failure, because one bad beat may be a passing network fault. */
                handleLockRefusal(region, error);
                /* A beat that fails this many times in a row cannot recover on
                 * its own. It would otherwise post every 60 seconds forever
                 * while the banner still promised a renewal. Issue #2110
                 * records a log that held 228 such posts. */
                if (lockBeatFailures >= LOCK_BEAT_FAILURE_LIMIT) {
                    stopLockBeat();
                    paintLockFree(region, LOCK_BEAT_STOPPED_MESSAGE);
                }
                return null;
            });
    }

    /**
     * Stops the running heartbeat.
     *
     * Why: A beat for a lock this browser lost would ask the server the same
     * question every 60 seconds and would always get the same refusal.
     *
     * @returns {void}
     */
    function stopLockBeat() {
        if (lockBeatTimer !== null) {
            window.clearInterval(lockBeatTimer);
            lockBeatTimer = null;
        }
    }

    /**
     * Starts the 60-second heartbeat for the lock this browser holds.
     *
     * Why: One page drives one site, so a second start replaces the first and
     * two timers never run together. A banner with no token starts nothing,
     * because there is no lock to renew.
     *
     * @param {Element} region The lock banner.
     * @returns {void}
     */
    function startLockBeat(region) {
        stopLockBeat();
        lockBeatFailures = 0;  /* A fresh beat starts with a clean count, so an earlier run never stops this one. */
        if (!region || !(region.getAttribute("data-lock-token") || "")) {
            return;
        }
        lockBeatTimer = window.setInterval(function () {
            beatSiteLock(region);
        }, HEARTBEAT_SECONDS * MILLISECONDS_PER_SECOND);
    }

    /**
     * Arms the lock banner of the current page.
     *
     * Why: The content security policy blocks an inline script, so the banner
     * carries no event attribute. A page that renders with a token already held
     * starts the beat at once, because a page reload must not drop a live lock.
     *
     * @returns {void}
     */
    function initLockBanner() {
        var region = getLockRegion();
        if (!region) {
            return;
        }

        var takeButton = byTestId(LOCK_TAKE_TESTID, region);
        if (takeButton) {
            takeButton.addEventListener("click", function () {
                requestSiteLock(region, "");
            });
        }

        var submitButton = byTestId(LOCK_SUBMIT_TESTID, region);
        var input = byTestId(LOCK_INPUT_TESTID, region);
        if (submitButton) {
            submitButton.addEventListener("click", function () {
                requestSiteLock(region, input ? input.value || "" : "");
            });
        }

        var releaseButton = byTestId(LOCK_RELEASE_TESTID, region);
        if (releaseButton) {
            releaseButton.addEventListener("click", function () {
                releaseSiteLock(region);
            });
        }

        startLockBeat(region);
    }

    /**
     * Arms every control of the current page.
     *
     * Why: One entry point keeps the load order clear. Each init step tests for
     * its own element first, so one file can serve every page.
     *
     * @returns {void}
     */
    function initPortal() {
        initTableFilters();
        initCapturePage();
        /* The gates run before the pages that hold them. A page then starts
         * with a button state that matches the field. */
        initConfirmGates();
        initUpgradeOptionsPage();
        initUpgradeConfirmPage();
        initRunPage();
        initStopControl();
        initLockBanner();
    }

    /* The script tag sits at the end of the body, so the document is often
     * ready already. The test covers both orders. */
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initPortal);
    } else {
        initPortal();
    }

    /* The namespace is the only global this file creates. A test drives the
     * poll through these names, because a timer alone is hard to drive. */
    window.upgradePortal = window.upgradePortal || {};
    window.upgradePortal.getCsrfToken = getCsrfToken;
    window.upgradePortal.withCsrf = withCsrf;
    window.upgradePortal.fetchJson = fetchJson;
    window.upgradePortal.getFlashRegion = getFlashRegion;
    window.upgradePortal.showFlash = showFlash;
    window.upgradePortal.showRequestError = showRequestError;
    window.upgradePortal.clearFlash = clearFlash;
    window.upgradePortal.applyTableFilter = applyTableFilter;
    window.upgradePortal.paintCaptureStatus = paintCaptureStatus;
    window.upgradePortal.refreshCaptureStatus = refreshCaptureStatus;
    window.upgradePortal.startCapturePoll = startCapturePoll;
    window.upgradePortal.stopCapturePoll = stopCapturePoll;
    window.upgradePortal.applyConfirmGate = applyConfirmGate;
    window.upgradePortal.applyVersionToEveryDevice = applyVersionToEveryDevice;
    window.upgradePortal.collectUpgradeTargets = collectUpgradeTargets;
    window.upgradePortal.paintUpgradeWarnings = paintUpgradeWarnings;
    window.upgradePortal.saveUpgradeOptions = saveUpgradeOptions;
    window.upgradePortal.startUpgrade = startUpgrade;
    window.upgradePortal.phaseProgressText = phaseProgressText;
    window.upgradePortal.normalizeVersion = normalizeVersion;
    window.upgradePortal.runVersionOutcome = runVersionOutcome;
    window.upgradePortal.paintRunVersionChecks = paintRunVersionChecks;
    window.upgradePortal.runLockSentence = runLockSentence;
    window.upgradePortal.paintRunLock = paintRunLock;
    window.upgradePortal.paintRunStatus = paintRunStatus;
    window.upgradePortal.refreshRunStatus = refreshRunStatus;
    window.upgradePortal.startRunPoll = startRunPoll;
    window.upgradePortal.stopRunPoll = stopRunPoll;
    window.upgradePortal.paintStopOutcome = paintStopOutcome;
    window.upgradePortal.requestRunStop = requestRunStop;
    window.upgradePortal.getLockRegion = getLockRegion;
    window.upgradePortal.showLockError = showLockError;
    window.upgradePortal.paintLockHeld = paintLockHeld;
    window.upgradePortal.paintLockFree = paintLockFree;
    window.upgradePortal.paintLockCooldown = paintLockCooldown;
    window.upgradePortal.openLockConfirm = openLockConfirm;
    window.upgradePortal.handleLockRefusal = handleLockRefusal;
    window.upgradePortal.requestSiteLock = requestSiteLock;
    window.upgradePortal.releaseSiteLock = releaseSiteLock;
    window.upgradePortal.beatSiteLock = beatSiteLock;
    window.upgradePortal.startLockBeat = startLockBeat;
    window.upgradePortal.stopLockBeat = stopLockBeat;
})();
