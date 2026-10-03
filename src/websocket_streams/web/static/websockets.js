/* global getCsrfToken, readJsonAnswer, MistWebSocketTerminal */

/*
 * The WebSockets page of the Operations portal (issue #3551).
 *
 * The page lists the Mist WebSocket channels and device utilities. It builds
 * the start form for one entry and shows the messages of one session. It reads
 * new messages every second. It refreshes the session list every five seconds
 * while the browser tab is visible.
 */

(function() {
    'use strict';  // Refuse silent errors in this page script.

    var PAGE_MESSAGE_LIMIT = 500;  // Keep no more rows than the default server buffer holds.
    var POLL_MS = 1000;  // Read the new messages of the selected session every second.
    var SESSION_REFRESH_MS = 5000;  // Refresh the counters of all sessions every five seconds.
    var SESSION_KEY = 'misthelper-websocket-session';  // Browser storage key of the last selected session.
    var NETWORK_ERROR = 'The portal did not answer. Check the network, then try again.';  // Text for a failed request.
    var NUMBER_KINDS = ['integer', 'vlan'];  // Field kinds that hold a whole number.
    var SCOPE_TITLES = {
        organization: 'Organization channels',
        site: 'Site channels',
        location: 'Location channels',
        diagnostics: 'Diagnostic channels'
    };  // Plain titles for the channel groups.
    var FAMILY_TITLES = {
        ap: 'AP utilities',
        ex: 'EX switch utilities',
        srx: 'SRX gateway utilities',
        ssr: 'SSR router utilities',
        mxedge: 'Mist Edge utilities'
    };  // Plain titles for the utility groups.
    var FAMILY_NAMES = { ap: 'AP', ex: 'EX switch', srx: 'SRX gateway', ssr: 'SSR router' };  // Device names for the empty list text.
    var SAFETY_BADGES = {
        read: ['Read only', 'bg-success'],
        capture: ['Capture', 'bg-info text-dark'],
        change: ['Changes device', 'bg-warning text-dark'],
        shell: ['Shell', 'bg-danger']
    };  // Badge text and color for each safety class.
    var STATE_TEXT = {
        connecting: 'Connecting',
        live: 'Live',
        stopping: 'Stopping',
        stopped: 'Stopped',
        finished: 'Finished',
        timed_out: 'Timed out',
        failed: 'Failed'
    };  // Plain names for the session states.
    var FINAL_STATES = ['stopped', 'finished', 'timed_out', 'failed'];  // Final terminal states cannot stop again.
    var PICKER_TEXT = {
        sites: 'Choose a site.',
        devices: 'Choose a device.',
        maps: 'Choose a map.',
        assets: 'Choose an asset.',
        sdkclients: 'Choose an SDK client.',
        mxedges: 'Choose a Mist Edge.'
    };  // The first option of a single-choice picker.
    var PICKER_PARENTS = {
        devices: ['sites'],
        maps: ['sites'],
        assets: ['sites'],
        sdkclients: ['sites', 'maps'],
        mxedges: ['sites']
    };  // A change of a parent picker reloads each child picker.
    var BAND_LABELS = { '24': '2.4 GHz', '5': '5 GHz', '6': '6 GHz' };  // Plain radio band names.
    var START_LABELS = { channel: 'Start stream', capture: 'Start capture', shell: 'Open shell', utility: 'Run utility' };  // Start button text.

    var state = {
        catalog: { channels: [], utilities: [], ready: false, reason: '' },  // The catalog payload from the server.
        selectedEntry: null,  // The catalog entry of the start form.
        selectedSession: null,  // The session of the message panel.
        nextAfter: 0,  // The newest message number that the page holds.
        paused: false,  // True while the operator paused the message view.
        polling: false,  // True while one message read runs.
        pollTimer: null,  // The timer that reads new messages.
        sessionTimer: null,  // The timer that refreshes the session list.
        pickerLoads: 0,  // A counter that marks the newest picker read.
        messages: [],  // The messages of the selected session, oldest first.
        labels: {},  // Picker labels by identifier, for the session title.
        terminalController: null  // The xterm.js controller for terminal sessions.
    };

    function byId(id) {
        return document.getElementById(id);  // Find one fixed page element.
    }

    function show(element, visible) {
        if (!element) return;  // A missing element needs no change.
        element.classList.toggle('d-none', !visible);  // Bootstrap hides an element with d-none.
    }

    function setText(id, value) {
        var element = byId(id);  // Find the target element.
        if (element) element.textContent = value || '';  // Plain text keeps Mist data out of the markup.
    }

    function clearNode(node) {
        if (!node) return;  // A missing element needs no change.
        while (node.firstChild) node.removeChild(node.firstChild);  // Remove each child element.
    }

    function make(tag, className, text) {
        var element = document.createElement(tag);  // Build the element.
        if (className) element.className = className;  // Apply the Bootstrap classes.
        if (text !== undefined) element.textContent = text;  // Plain text keeps Mist data out of the markup.
        return element;  // The caller adds the element to the page.
    }

    function hasValue(value) {
        return value !== null && value !== undefined;  // Zero and false are real values.
    }

    function apiJson(url, options) {
        var request = options || {};  // A GET request needs no options.
        request.headers = request.headers || {};  // The code below adds headers.
        if (request.method && request.method !== 'GET') request.headers['X-CSRFToken'] = getCsrfToken();  // Flask-WTF checks this header.
        if (request.body && !request.headers['Content-Type']) request.headers['Content-Type'] = 'application/json';  // The API reads JSON.
        return fetch(url, request).then(readJsonAnswer).catch(function() {
            return { error: NETWORK_ERROR };  // A failed request resolves with a reason, like a refused request.
        });
    }

    function init() {
        if (!byId('wsCatalog')) return;  // Other portal pages load no WebSockets code.
        wireStaticEvents();  // Connect the fixed buttons and inputs.
        loadCatalog();  // Read the channels and the utilities.
        loadSessions(false);  // Read the sessions and show the last selected session.
        startSessionTimer();  // Keep the session counters current.
    }

    function wireStaticEvents() {
        byId('wsStartForm').addEventListener('submit', startSelected);  // Start the selected entry.
        byId('wsCatalogFilter').addEventListener('input', renderCatalog);  // Filter the catalog while the operator types.
        byId('wsPauseButton').addEventListener('click', function() { setPaused(true); });  // Freeze the message view.
        byId('wsResumeButton').addEventListener('click', resumePolling);  // Read the new messages again.
        byId('wsClearButton').addEventListener('click', clearMessages);  // Empty the message view.
        byId('wsStopButton').addEventListener('click', stopSelectedSession);  // Stop the selected session.
        byId('wsMessageFilter').addEventListener('input', renderMessages);  // Filter the messages while the operator types.
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden) loadSessions(true);  // Show the current counters when the tab is visible again.
        });
    }

    function loadCatalog() {
        apiJson('/api/websockets/catalog').then(function(payload) {
            var failed = { channels: [], utilities: [], ready: false, reason: payload.error };  // Show the reason instead of an empty page.
            state.catalog = payload.error ? failed : payload;  // Keep the catalog for the filter and the form.
            renderReadyState(state.catalog);  // Show the engine state and the entry count.
            renderCatalog();  // Draw the entry groups.
        });
    }

    function renderReadyState(catalog) {
        var alert = byId('wsReadyAlert');  // The engine state box.
        show(alert, !catalog.ready);  // Show the box only when the engine cannot start streams.
        if (!catalog.ready) alert.textContent = catalog.reason || 'The WebSocket engine is not ready.';  // Plain reason.
        setText('wsCatalogCount', String((catalog.channels || []).length + (catalog.utilities || []).length));  // Entry count.
    }

    function renderCatalog() {
        var container = byId('wsCatalog');  // The catalog list element.
        var filter = (byId('wsCatalogFilter').value || '').trim().toLowerCase();  // Match without case.
        var shown = 0;  // Count the entries that match the filter.
        clearNode(container);  // Remove the old list and the loading text.
        shown += appendGroups(container, groupBy(state.catalog.channels || [], 'scope'), SCOPE_TITLES, filter, 'channel');  // Channels first.
        shown += appendGroups(container, groupBy(state.catalog.utilities || [], 'family'), FAMILY_TITLES, filter, 'utility');  // Then utilities.
        if (!shown) container.appendChild(make('div', 'text-muted py-2', emptyCatalogText(filter)));  // Say why the list is empty.
    }

    function emptyCatalogText(filter) {
        if (filter) return 'No catalog entry matches the filter.';  // The filter hides every entry.
        return state.catalog.reason || 'The catalog has no entry.';  // The engine gave no entries.
    }

    function groupBy(entries, key) {
        var groups = {};  // Entries by group name, in catalog order.
        entries.forEach(function(entry) {
            var name = entry[key] || 'other';  // An entry without a group goes to "other".
            if (!groups[name]) groups[name] = [];  // Start a new group.
            groups[name].push(entry);  // Keep the catalog order inside the group.
        });
        return groups;  // The caller draws one card for each group.
    }

    function appendGroups(container, groups, titles, filter, type) {
        var shown = 0;  // Count the matching entries of all groups.
        Object.keys(groups).forEach(function(name) {
            var entries = groups[name].filter(function(entry) { return matchesFilter(entry, filter); });  // Keep matches only.
            if (!entries.length) return;  // Skip a group with no match, so no empty title shows.
            container.appendChild(groupCard(titles[name] || name, entries, type));  // Draw one group.
            shown += entries.length;  // Add the group matches to the total.
        });
        return shown;  // The caller shows an empty-list text for zero.
    }

    function groupCard(title, entries, type) {
        var card = make('div', 'ws-catalog-group mb-2');  // One group of entries.
        card.appendChild(make('h6', 'text-muted', title + ' (' + entries.length + ')'));  // Title with the match count.
        entries.forEach(function(entry) { card.appendChild(catalogButton(entry, type)); });  // One button for each entry.
        return card;  // The caller adds the card to the list.
    }

    function matchesFilter(entry, filter) {
        if (!filter) return true;  // An empty filter shows every entry.
        var text = (entry.name || '') + ' ' + (entry.description || '') + ' ' + (entry.key || '');  // Search the visible text and the key.
        return text.toLowerCase().indexOf(filter) >= 0;  // Match without case.
    }

    function catalogButton(entry, type) {
        var button = make('button', 'btn btn-sm btn-outline-secondary ws-catalog-entry w-100 text-start mb-1');  // One entry button.
        button.type = 'button';  // A plain button does not submit a form.
        button.dataset.testid = 'ws-catalog-entry-' + entry.key;  // Stable test hook.
        button.dataset.key = entry.key;  // The select code finds the button by key.
        button.classList.toggle('active', !!state.selectedEntry && state.selectedEntry.key === entry.key);  // Show the chosen entry.
        button.appendChild(make('span', 'fw-semibold', entry.name || entry.key));  // Entry name.
        appendBadges(button, entry);  // Show the safety class and the lock.
        button.appendChild(make('div', 'small ws-entry-description', entry.description || ''));  // Plain sentence.
        button.addEventListener('click', function() { selectEntry(entry, type); });  // Build the start form.
        return button;  // The caller adds the button to the group.
    }

    function appendBadges(button, entry) {
        var badge = SAFETY_BADGES[entry.safety];  // Channels have no safety class.
        if (badge) button.appendChild(make('span', 'badge ms-2 ' + badge[1], badge[0]));  // Safety class of a utility.
        if (entry.locked) button.appendChild(make('span', 'badge bg-secondary ms-1', 'Locked'));  // Lock state.
    }

    function selectEntry(entry, type) {
        state.selectedEntry = Object.assign({ entryType: type }, entry);  // Keep the type with the entry.
        setText('wsSelectedTitle', entry.name || entry.key);  // Form title.
        setText('wsSelectedDescription', entry.description || '');  // Form sentence.
        markSelectedEntry(entry.key);  // Show the chosen entry in the catalog.
        renderSafety(entry);  // Show the warning and the lock text.
        renderStartForm(state.selectedEntry);  // Build the fields for this entry.
    }

    function markSelectedEntry(key) {
        document.querySelectorAll('.ws-catalog-entry').forEach(function(button) {
            button.classList.toggle('active', button.dataset.key === key);  // Only the chosen entry is active.
        });
    }

    function renderSafety(entry) {
        var warning = byId('wsSafetyWarning');  // The warning box of the start form.
        var text = safetyText(entry);  // Empty for a read-only entry.
        show(warning, !!text);  // Show the box only when a warning applies.
        warning.textContent = text;  // Plain text keeps Mist data out of the markup.
    }

    function safetyText(entry) {
        var base = '';  // A read-only entry has no warning.
        if (entry.safety === 'change') base = 'Warning: This utility changes the device state and can interrupt traffic.';  // Change risk.
        if (entry.safety === 'shell') base = 'Warning: A remote shell gives full command access to the device. A wrong command can stop the device or drop traffic.';  // Shell risk.
        if (entry.locked) return (base ? base + ' ' : '') + 'The portal locks this utility. To unlock it, set ' + lockName(entry) + ' to true and restart the portal.';  // Unlock steps.
        return base;  // The confirmation field under the form asks for the device name.
    }

    function lockName(entry) {
        if (entry.safety === 'shell') return 'PORTAL_WS_ENABLE_SHELL';  // The shell flag.
        if (entry.safety === 'change') return 'PORTAL_WS_ENABLE_CHANGES';  // The change flag.
        return 'the safety flag';  // A future lock without a known flag.
    }

    function renderStartForm(entry) {
        var targetBox = byId('wsTargetFields');  // Identifier fields, such as the site and the device.
        var paramBox = byId('wsParameterFields');  // Parameter fields of the utility.
        var button = byId('wsStartButton');  // The start button of the form.
        clearNode(targetBox);  // Remove the fields of the last entry.
        clearNode(paramBox);  // Remove the fields of the last entry.
        (entry.identifiers || entry.targets || []).forEach(function(field) { targetBox.appendChild(fieldControl(field, true)); });  // Targets first.
        (entry.fields || []).forEach(function(field) { paramBox.appendChild(fieldControl(field, false)); });  // Then the parameters.
        show(byId('wsConfirmationGroup'), needsConfirmation(entry));  // A locked entry cannot start, so it needs no confirmation.
        byId('wsConfirmation').value = '';  // One confirmation applies to one start only.
        button.textContent = startLabel(entry);  // Name the action of this entry.
        button.disabled = !state.catalog.ready || !!entry.locked;  // A locked entry cannot start.
    }

    function needsConfirmation(entry) {
        return (entry.safety === 'change' || entry.safety === 'shell') && !entry.locked;  // Only a start that can run needs the name.
    }

    function startLabel(entry) {
        if (entry.entryType === 'channel') return START_LABELS.channel;  // A channel starts a stream.
        return START_LABELS[entry.safety] || START_LABELS.utility;  // A capture and a shell use their own verbs.
    }

    function fieldControl(field, isTarget) {
        var input = createInput(field);  // A select, a check box, or a text input.
        tagField(input, field, isTarget);  // Add the id and the data attributes before any list loads.
        configureControl(input, field);  // Add the options, the limits, and the default value.
        return input.type === 'checkbox' ? checkboxGroup(input, field) : inputGroup(input, field);  // Wrap the input with its label.
    }

    function createInput(field) {
        if (field.picker || field.kind === 'choice') return make('select', 'form-select');  // A list of values uses a select.
        var input = make('input', field.kind === 'boolean' ? 'form-check-input' : 'form-control');  // Other values use an input.
        if (field.kind === 'boolean') input.type = 'checkbox';  // A yes-or-no value uses a check box.
        return input;  // The caller configures the input.
    }

    function tagField(input, field, isTarget) {
        input.id = 'wsField-' + field.name;  // The label points at this id.
        input.dataset.wsField = field.name;  // The start body uses this name.
        input.dataset.wsTarget = isTarget ? '1' : '0';  // Targets and parameters go to separate body keys.
        input.dataset.wsKind = field.kind || 'text';  // Keep the field kind on the input.
        input.dataset.wsPicker = field.picker || '';  // The picker reload code reads this name.
        input.dataset.testid = 'ws-field-' + field.name;  // Stable test hook.
        if (field.required) input.required = true;  // The browser blocks an empty required value.
    }

    function configureControl(input, field) {
        if (field.picker) configurePicker(input, field);  // Load the live Mist rows.
        else if (field.kind === 'choice') configureChoice(input, field);  // Add the fixed values.
        else if (input.type === 'checkbox') input.checked = field.default === true;  // Use the catalog default.
        else configureInput(input, field);  // Add the limits and the default value.
    }

    function configureInput(input, field) {
        var number = NUMBER_KINDS.indexOf(field.kind) >= 0;  // A number uses a number input with a range.
        input.type = number ? 'number' : 'text';  // Numbers show the number keyboard on a tablet.
        if (number && hasValue(field.minimum)) input.min = String(field.minimum);  // Lowest accepted number.
        if (number && hasValue(field.maximum)) input.max = String(field.maximum);  // Highest accepted number.
        if (!number && hasValue(field.maximum)) input.maxLength = field.maximum;  // Longest accepted text.
        if (hasValue(field.default)) input.value = String(field.default);  // Catalog default.
    }

    function configureChoice(select, field) {
        select.appendChild(new Option(field.required ? 'Choose a value.' : 'Not set', ''));  // An optional choice can stay empty.
        (field.choices || []).forEach(function(value) {
            select.appendChild(new Option(field.name === 'band' ? (BAND_LABELS[value] || value) : value, value));  // One option for each value.
        });
        if (hasValue(field.default)) select.value = String(field.default);  // Catalog default.
    }

    function configurePicker(select, field) {
        if (field.name === state.selectedEntry.repeatable) select.multiple = true;  // A repeatable identifier takes more than one value.
        if (select.multiple) select.size = 6;  // Show six rows, so the operator sees that more than one row can be chosen.
        select.addEventListener('change', function() { onPickerChanged(select); });  // Reload the pickers that depend on this one.
        loadPickerOptions(select);  // Read the live rows.
    }

    function inputGroup(input, field) {
        var group = make('div', 'mb-3');  // One labeled field.
        var label = make('label', 'form-label', field.required ? (field.label || field.name) + ' (required)' : (field.label || field.name));  // Field name.
        label.setAttribute('for', input.id);  // A click on the label moves the focus to the input.
        group.appendChild(label);  // Label above the input.
        group.appendChild(input);  // The input itself.
        hintTexts(field, input).forEach(function(text) { group.appendChild(make('div', 'form-text', text)); });  // Help under the input.
        return group;  // The caller adds the group to the form.
    }

    function hintTexts(field, input) {
        var hints = [];  // Zero, one, or two help lines.
        if (field.hint) hints.push(field.hint);  // The catalog hint.
        if (input.multiple) hints.push('To choose more than one item, hold Ctrl and click each item.');  // Multiple-choice help.
        if (input.type === 'number' && hasValue(field.minimum) && hasValue(field.maximum)) {
            hints.push('Type a number from ' + field.minimum + ' to ' + field.maximum + '.');  // The accepted range.
        }
        return hints;  // The caller adds one line for each hint.
    }

    function checkboxGroup(input, field) {
        var group = make('div', 'form-check mb-3');  // Bootstrap check box layout.
        var label = make('label', 'form-check-label', field.label || field.name);  // The name of the value.
        label.setAttribute('for', input.id);  // A click on the label changes the box.
        group.appendChild(input);  // The box comes first.
        group.appendChild(label);  // The label follows the box.
        if (field.hint) group.appendChild(make('div', 'form-text', field.hint));  // Optional help text.
        return group;  // The caller adds the group to the form.
    }

    function onPickerChanged(select) {
        var parent = select.dataset.wsPicker;  // The picker that the operator changed.
        document.querySelectorAll('select[data-ws-picker]').forEach(function(child) {
            var parents = PICKER_PARENTS[child.dataset.wsPicker] || [];  // The pickers that this list depends on.
            if (child !== select && parents.indexOf(parent) >= 0) loadPickerOptions(child);  // Reload a dependent list only.
        });
    }

    function loadPickerOptions(select) {
        var name = select.dataset.wsPicker;  // The picker name, such as "devices".
        var url = pickerUrl(name);  // Empty when a parent value is missing.
        var serial = String(++state.pickerLoads);  // Mark this read, so a slow old answer cannot replace a newer list.
        select.dataset.wsLoad = serial;  // Keep the newest read mark on the select.
        setSingleOption(select, url ? 'Loading...' : parentText(name));  // Show the state until the rows arrive.
        if (!url) return;  // Wait for the operator to choose the parent value.
        apiJson(url).then(function(payload) {
            if (select.dataset.wsLoad !== serial) return;  // A newer read replaced this one.
            fillPicker(select, payload.rows || payload.sites || [], payload.reason || payload.error);  // Show the rows or the reason.
        });
    }

    function setSingleOption(select, text) {
        var option = new Option(text, '');  // A note that holds no value.
        clearNode(select);  // Remove the old rows.
        if (select.multiple) option.disabled = true;  // A note in a multiple-choice list cannot be chosen.
        select.appendChild(option);  // Show the note.
    }

    function parentText(name) {
        if (name === 'sdkclients' && valueOf('site_id')) return 'Choose a map first.';  // The SDK client list needs a map.
        return 'Choose a site first.';  // All other child lists need a site.
    }

    function pickerUrl(name) {
        var site = valueOf('site_id');  // The chosen site, or an empty text.
        var map = valueOf('map_id');  // The chosen map, or an empty text.
        var siteBase = '/api/websockets/sites/' + encodeURIComponent(site);  // The site part of each site-scoped list.
        if (name === 'sites') return '/api/operations/sites';  // The site list needs no parent.
        if (name === 'mxedges') return '/api/websockets/mxedges' + (site ? '?site_id=' + encodeURIComponent(site) : '');  // A site narrows the list.
        if (!site) return '';  // Every other list needs a site.
        if (name === 'devices' || name === 'maps' || name === 'assets') return siteBase + '/' + name;  // Site-scoped lists.
        if (name === 'sdkclients' && map) return siteBase + '/maps/' + encodeURIComponent(map) + '/sdkclients';  // The SDK clients of one map.
        return '';  // The parent map is missing.
    }

    function fillPicker(select, rows, reason) {
        var usable = rows.filter(function(row) { return rowFitsEntry(select, row); });  // Keep the devices of the utility family only.
        if (!usable.length) {
            setSingleOption(select, emptyPickerText(rows, reason));  // Say why the list is empty.
            return;  // No row can be chosen.
        }
        clearNode(select);  // Remove the loading text.
        if (!select.multiple) select.appendChild(new Option(PICKER_TEXT[select.dataset.wsPicker] || 'Choose a value.', ''));  // Placeholder first.
        usable.forEach(function(row) { select.appendChild(pickerOption(row)); });  // One option for each row.
    }

    function rowFitsEntry(select, row) {
        var family = state.selectedEntry && state.selectedEntry.family;  // Only utilities name a device family.
        if (select.dataset.wsPicker !== 'devices' || !family) return true;  // Other lists show all rows.
        return row.family === family;  // A utility runs only on a device of its family.
    }

    function emptyPickerText(rows, reason) {
        var family = state.selectedEntry && state.selectedEntry.family;  // Set for a utility entry only.
        if (reason) return reason;  // The server named the cause.
        if (rows.length && family) return 'No ' + (FAMILY_NAMES[family] || family) + ' is at this site.';  // Rows exist, but none fits.
        return 'No rows are available.';  // The list is empty.
    }

    function pickerOption(row) {
        var label = row.label || row.name || row.id;  // Operators read names first.
        var option = new Option(row.detail ? label + ' (' + row.detail + ')' : label, row.id);  // The detail tells similar names apart.
        option.dataset.family = row.family || '';  // Keep the family for later checks.
        state.labels[row.id] = label;  // The session title uses the plain name.
        return option;  // The caller adds the option to the select.
    }

    function valueOf(name) {
        var input = document.querySelector('[data-ws-field="' + name + '"]');  // The field names are catalog constants.
        return input ? input.value : '';  // A missing field has no value.
    }

    function startSelected(event) {
        var button = byId('wsStartButton');  // Block a second start while the request runs.
        event.preventDefault();  // The page sends JSON instead of a form post.
        if (!state.selectedEntry) return;  // No entry means nothing to start.
        button.disabled = true;  // One click starts one session.
        apiJson('/api/websockets/sessions', { method: 'POST', body: JSON.stringify(buildStartBody()) }).then(function(payload) {
            button.disabled = !state.catalog.ready || !!state.selectedEntry.locked;  // Allow the next start.
            showStartError(payload.error ? payload : null);  // Show a refusal, or hide an old one.
            if (payload.error) return;  // A refused start has no session.
            loadSessions(true);  // Add the new session to the list.
            selectSession(payload);  // Show the messages of the new session.
            byId('wsMessagePanel').scrollIntoView({ behavior: 'smooth', block: 'start' });  // Move the view to the output.
        });
    }

    function buildStartBody() {
        var entry = state.selectedEntry;  // The entry of the start form.
        var targets = collectValues('1');  // Identifier values, such as the site.
        return {
            kind: entryKind(entry),  // The server picks the runner from this value.
            key: entry.key,  // The catalog key.
            targets: targets,  // The server checks each value.
            parameters: collectValues('0'),  // The server checks each value.
            confirmation: byId('wsConfirmation').value || null,  // The typed device name, when the entry needs it.
            labels: chosenLabels(targets)  // Plain names for the session title.
        };
    }

    function entryKind(entry) {
        if (entry.entryType === 'channel') return 'channel';  // A channel uses the channel runner.
        return entry.safety === 'shell' ? 'shell' : 'utility';  // A shell uses the shell runner.
    }

    function chosenLabels(targets) {
        var labels = {};  // Send only the labels of the chosen values.
        Object.keys(targets).forEach(function(name) {
            [].concat(targets[name]).forEach(function(value) {
                if (state.labels[value]) labels[value] = state.labels[value];  // Keep a known label only.
            });
        });
        return labels;  // A small map keeps the request short.
    }

    function collectValues(targetFlag) {
        var values = {};  // Values by field name.
        document.querySelectorAll('[data-ws-target="' + targetFlag + '"]').forEach(function(input) {
            var name = input.dataset.wsField;  // The body key of this field.
            if (input.type === 'checkbox') values[name] = input.checked;  // A check box sends true or false.
            else if (input.multiple) values[name] = Array.from(input.selectedOptions).map(function(option) { return option.value; }).filter(Boolean);  // A list.
            else if (input.value !== '') values[name] = input.value;  // An empty optional value stays out of the body.
        });
        return values;  // The server checks each value.
    }

    function showStartError(payload) {
        var alert = byId('wsStartError');  // The refusal box of the start form.
        show(alert, !!payload);  // Show the box only for a refusal.
        if (payload) alert.textContent = limitText(payload);  // Plain reason.
    }

    function limitText(payload) {
        if (payload.code === 'limit_reached' && payload.live) return payload.error + ' Live sessions: ' + payload.live.join(', ');  // Name the live sessions.
        return payload.error || 'The portal refused the request.';  // The server reason.
    }

    function startSessionTimer() {
        if (state.sessionTimer) window.clearInterval(state.sessionTimer);  // Keep one timer only.
        state.sessionTimer = window.setInterval(function() {
            if (!document.hidden) loadSessions(true);  // A hidden tab sends no request.
        }, SESSION_REFRESH_MS);
    }

    function loadSessions(skipRestore) {
        apiJson('/api/websockets/sessions').then(function(payload) {
            if (payload.error) return;  // Keep the old list when the portal does not answer.
            renderSessions(payload.sessions || [], payload.limits || {});  // Draw the list and the limit badge.
            if (!skipRestore) restoreSelectedSession(payload.sessions || []);  // Show the last session after a reload.
        });
    }

    function renderSessions(sessions, limits) {
        var box = byId('wsSessionList');  // The session list element.
        clearNode(box);  // Remove the old list.
        setText('wsSessionLimit', String(limits.live_count || 0) + ' / ' + String(limits.max_sessions || 0));  // Live count and limit.
        if (!sessions.length) box.appendChild(make('div', 'text-muted', 'No session is available.'));  // Empty list text.
        sessions.forEach(function(session) { box.appendChild(sessionButton(session)); });  // One button for each session.
    }

    function sessionButton(session) {
        var button = make('button', 'btn btn-outline-secondary ws-session-item w-100 text-start mb-2');  // One session button.
        button.type = 'button';  // A plain button does not submit a form.
        button.dataset.testid = 'ws-session-' + session.session_id;  // Stable test hook.
        button.dataset.sessionId = session.session_id;  // The update code finds the button by id.
        button.classList.toggle('active', isSelected(session));  // Show the session of the message panel.
        button.appendChild(make('div', 'fw-semibold', session.title || session.key));  // Session title.
        button.appendChild(make('div', 'small ws-session-status', sessionStatusText(session)));  // State and counters.
        button.addEventListener('click', function() { showSessionOutput(session); });  // Show this session and its output.
        return button;  // The caller adds the button to the list.
    }

    function showSessionOutput(session) {
        selectSession(session);  // Show the chosen session in the output panel.
        byId('wsMessagePanel').scrollIntoView({ behavior: 'smooth', block: 'start' });  // Move the view to the output, as a start does.
    }

    function isSelected(session) {
        return !!state.selectedSession && state.selectedSession.session_id === session.session_id;  // Compare the ids.
    }

    function sessionStatusText(session) {
        if (isTerminalSession(session)) return stateText(session);  // Terminal session frames are not operator messages.
        return stateText(session) + ' - ' + countersText(session);  // One status line for the list.
    }

    function stateText(session) {
        return STATE_TEXT[session.state] || session.state || 'Unknown';  // Plain state name.
    }

    function updateSessionItem(session) {
        document.querySelectorAll('.ws-session-item').forEach(function(button) {
            if (button.dataset.sessionId !== session.session_id) return;  // Update the matching button only.
            var status = button.querySelector('.ws-session-status');  // The state and counter line.
            if (status) status.textContent = sessionStatusText(session);  // Keep the list equal to the panel.
        });
    }

    function markSelectedSession(sessionId) {
        document.querySelectorAll('.ws-session-item').forEach(function(button) {
            button.classList.toggle('active', button.dataset.sessionId === sessionId);  // Only the shown session is active.
        });
    }

    function restoreSelectedSession(sessions) {
        var saved = localStorage.getItem(SESSION_KEY);  // The last selected session id.
        var session = sessions.find(function(item) { return item.session_id === saved; });  // The session can be gone.
        if (session) selectSession(session);  // Show the last session again.
    }

    function selectSession(session) {
        stopTerminalController();  // Stop any terminal read loop for the previous session.
        state.selectedSession = session;  // The message panel shows this session.
        state.nextAfter = 0;  // Read the buffer from the oldest kept message.
        state.messages = [];  // Remove the messages of the last session.
        show(byId('wsMessageGap'), false);  // Remove a gap notice that belongs to the last session.
        localStorage.setItem(SESSION_KEY, session.session_id);  // Show this session again after a reload.
        markSelectedSession(session.session_id);  // Show the selection in the list.
        show(byId('wsMessagePanel'), true);  // Show the message panel.
        setPaused(false);  // A new selection shows live output.
        updateSessionHeader(session);  // Title, state, and counters.
        if (isTerminalSession(session)) {
            showTerminalSession(session);  // A terminal session uses xterm.js and terminal routes.
            return;  // The terminal read loop replaces the message poll loop.
        }
        showMessageSession();  // A non-terminal session uses the existing row view.
        renderMessages();  // Show the empty view until messages arrive.
        startPollTimer();  // Read new messages every second.
    }

    function isTerminalSession(session) {
        return session.terminal === true || session.output === 'terminal' || session.output === 'screen';  // Support new and old payloads.
    }

    function showTerminalSession(session) {
        stopPollTimer();  // Message polling is not used for a terminal session.
        show(byId('wsOutput'), false);  // Hide the old message view.
        show(byId('wsMessageFilter'), false);  // The xterm buffer has its own view.
        show(byId('wsClearButton'), false);  // The terminal menu clears local history.
        show(byId('wsDownloadLink'), false);  // The terminal toolbar owns text download.
        byId('wsPauseButton').disabled = true;  // Terminal long-poll reads do not pause here.
        byId('wsResumeButton').disabled = true;  // Terminal long-poll reads do not resume here.
        terminalController().open(session);  // Start the terminal read loop.
    }

    function updateTerminalSession(terminalState) {
        if (!state.selectedSession) return;  // No session is selected during teardown.
        Object.assign(state.selectedSession, terminalState);  // Merge the latest terminal state.
        if (FINAL_STATES.indexOf(state.selectedSession.state) >= 0) state.selectedSession.live = false;  // Final state cannot stop.
        updateSessionHeader(state.selectedSession);  // Keep the header equal to the terminal read answer.
        updateSessionItem(state.selectedSession);  // Keep the session list equal to the terminal read answer.
    }

    function showMessageSession() {
        show(byId('wsOutput'), true);  // Show rows for streams, commands, and captures.
        show(byId('wsMessageFilter'), true);  // Filtering applies only to message rows.
        show(byId('wsClearButton'), true);  // The message row view can clear local rows.
        show(byId('wsDownloadLink'), true);  // The message row view downloads JSON Lines.
        byId('wsPauseButton').disabled = false;  // The message poll can pause.
        byId('wsResumeButton').disabled = false;  // The message poll can resume.
    }

    function terminalController() {
        if (!state.terminalController) {
            state.terminalController = new MistWebSocketTerminal.TerminalController(terminalElements(), {
                onState: updateTerminalSession,  // Let terminal reads update the session header.
                stateText: STATE_TEXT  // Keep terminal footer state labels equal to page labels.
            });  // Build once with a state bridge to the page header.
        }
        return state.terminalController;  // Reuse the controller for each terminal selection.
    }

    function stopTerminalController() {
        if (state.terminalController) state.terminalController.close();  // Close the read loop and xterm instance.
    }

    function terminalElements() {
        return {
            panel: byId('wsTerminalPanel'),
            screen: byId('wsTerminalScreen'),
            warning: byId('wsTerminalWarning'),
            status: byId('wsTerminalStatus'),
            expiry: byId('wsTerminalExpiry'),
            gap: byId('wsTerminalGap'),
            copy: byId('wsTerminalCopy'),
            paste: byId('wsTerminalPaste'),
            download: byId('wsTerminalDownload'),
            fontUp: byId('wsTerminalFontUp'),
            fontDown: byId('wsTerminalFontDown'),
            copyOnSelect: byId('wsTerminalCopyOnSelect'),
            confirmPaste: byId('wsTerminalConfirmPaste'),
            menu: byId('wsTerminalMenu'),
            menuCopy: byId('wsTerminalMenuCopy'),
            menuPaste: byId('wsTerminalMenuPaste'),
            menuSelectAll: byId('wsTerminalMenuSelectAll'),
            menuClear: byId('wsTerminalMenuClear'),
            dialog: byId('wsTerminalPasteDialog'),
            pasteLines: byId('wsTerminalPasteLines'),
            pastePreview: byId('wsTerminalPastePreview'),
            pasteSend: byId('wsTerminalPasteSend'),
            pasteCancel: byId('wsTerminalPasteCancel'),
            pasteInputLabel: byId('wsTerminalPasteInputLabel'),
            pasteInput: byId('wsTerminalPasteInput'),
            progress: byId('wsTerminalProgress'),
            toast: byId('wsTerminalToast')
        };  // Keep test elements in one map for the controller.
    }

    function updateSessionHeader(session) {
        setText('wsSessionTitle', session.title || session.key);  // Session title.
        setText('wsSessionState', 'State: ' + stateText(session));  // Plain state name.
        setText('wsSessionReason', session.reason || session.notice || '');  // The end reason, or the notice of a terminal that waits for output.
        setText('wsCounters', countersText(session));  // Message counters.
        byId('wsDownloadLink').href = '/api/websockets/sessions/' + encodeURIComponent(session.session_id) + '/download';  // Buffer download.
        byId('wsStopButton').disabled = !session.live;  // A closed session cannot stop again.
    }

    function countersText(session) {
        if (isTerminalSession(session)) return 'Output: ' + (session.terminal_next || 0) + ' bytes';  // Terminal counters show bytes, not frames.
        var counters = session.counters || {};  // The server counts the messages of each session.
        var rate = Number(session.rate_per_second || 0).toFixed(1);  // One decimal place is enough for a rate.
        return 'Messages: ' + (counters.received || 0) + ', dropped: ' + (counters.dropped || 0) + ', rate: ' + rate + '/s';  // Counter line.
    }

    function startPollTimer() {
        stopPollTimer();  // Keep one timer only.
        pollSelectedSession();  // Read at once, so the view fills without a delay.
        state.pollTimer = window.setInterval(pollSelectedSession, POLL_MS);  // Then read every second.
    }

    function stopPollTimer() {
        if (state.pollTimer) window.clearInterval(state.pollTimer);  // Stop the reads of the old session.
        state.pollTimer = null;  // No timer runs now.
    }

    function pollSelectedSession() {
        var session = state.selectedSession;  // The session of the message panel.
        if (!session || state.paused || state.polling) return;  // Skip while paused or while a read runs.
        state.polling = true;  // One read at a time keeps the messages in order.
        apiJson(messagesUrl(session)).then(function(payload) {
            state.polling = false;  // Allow the next read.
            if (payload.error || !isSelected(session)) return;  // Ignore an answer for a session that the operator left.
            applyMessages(payload, session);  // Add the new messages and update the counters.
        });
    }

    function messagesUrl(session) {
        var base = '/api/websockets/sessions/' + encodeURIComponent(session.session_id) + '/messages';  // The read route.
        return base + '?after=' + state.nextAfter + '&limit=' + PAGE_MESSAGE_LIMIT;  // Read after the newest kept message.
    }

    function applyMessages(payload, session) {
        var fresh = payload.messages || [];  // The messages after the newest kept number.
        state.selectedSession = payload.session || session;  // The server sends the newest counters.
        state.nextAfter = payload.next_after || state.nextAfter;  // Continue after the newest message.
        show(byId('wsMessageGap'), payload.gap === true);  // Warn when reconnect output exceeded the bounded buffer.
        updateSessionHeader(state.selectedSession);  // Title, state, and counters.
        updateSessionItem(state.selectedSession);  // Keep the list equal to the panel.
        if (fresh.length) appendMessages(fresh);  // Draw again only when something is new.
        if (fresh.length >= PAGE_MESSAGE_LIMIT) window.setTimeout(pollSelectedSession, 0);  // A full page means more messages wait.
        else if (!state.selectedSession.live) stopPollTimer();  // A closed session with no waiting message is complete.
    }

    function appendMessages(fresh) {
        state.messages = state.messages.concat(fresh);  // Keep the arrival order.
        if (state.messages.length > PAGE_MESSAGE_LIMIT) state.messages = state.messages.slice(-PAGE_MESSAGE_LIMIT);  // Drop the oldest rows first.
        renderMessages();  // Draw the view again.
    }

    function renderMessages() {
        var output = byId('wsOutput');  // The message view.
        var follow = output.scrollHeight - output.scrollTop - output.clientHeight < 40;  // True when the operator did not scroll up.
        var filter = (byId('wsMessageFilter').value || '').toLowerCase();  // Match without case.
        var view = state.selectedSession ? state.selectedSession.output : 'lines';  // The server names the view type.
        clearNode(output);  // Remove the old rows.
        if (view === 'lines') renderLines(output, state.messages, filter);  // Join command chunks before the view or filter reads them.
        else drawMessages(output, matchingMessages(state.messages, filter), view);  // Keep record boundaries for JSON and packets.
        if (follow) output.scrollTop = output.scrollHeight;  // Keep the newest row in view.
    }

    function matchingMessages(messages, filter) {
        return messages.filter(function(message) { return messageText(message).toLowerCase().indexOf(filter) >= 0; });  // Match complete records.
    }

    function drawMessages(output, messages, view) {
        if (view === 'packets') renderPackets(output, messages);  // Show one row for each packet.
        else renderRows(output, messages);  // Show one row for each message.
    }

    function renderLines(output, messages, filter) {
        var row = make('div', 'ws-message-row');  // One command output block keeps cloud chunks invisible.
        var text = filterLineText(joinLineText(messages), filter);  // Filter complete command lines after joining chunks.
        row.appendChild(make('pre', 'mb-0', text));  // Preserve the command line and word boundaries.
        output.appendChild(row);  // Add the single command output block.
    }

    function joinLineText(messages) {
        return messages.map(messageText).join('');  // Mist chunks can split a line or a word, so add no separator.
    }

    function filterLineText(text, filter) {
        if (!filter) return text;  // An empty filter must preserve every original character.
        return text.split(/\r\n|\r|\n/).filter(function(line) {
            return line.toLowerCase().indexOf(filter) >= 0;  // Keep each complete line that contains the filter.
        }).join('\n');  // Show only the matching command lines.
    }

    function renderRows(output, messages) {
        messages.forEach(function(message) {
            var row = make('div', 'ws-message-row');  // One message.
            row.appendChild(make('div', 'small text-muted', '#' + message.seq + ' ' + (message.source || '') + ' ' + (message.received_at || '')));  // Header.
            row.appendChild(make('pre', 'mb-0', messageText(message)));  // Content.
            output.appendChild(row);  // Add the row to the view.
        });
    }

    function renderPackets(output, messages) {
        messages.forEach(function(message) {
            output.appendChild(make('div', 'ws-packet-row', message.summary || messageText(message)));  // One packet summary.
        });
    }

    function messageText(message) {
        if (message.viewText === undefined) message.viewText = buildMessageText(message);  // Build the text one time for each message.
        return message.viewText;  // The filter and the view read the same stored text.
    }

    function buildMessageText(message) {
        if (message.summary) return message.summary;  // A packet has a one-line summary.
        if (typeof message.content !== 'string') return JSON.stringify(message.content, null, 2);  // A channel message is JSON.
        var table = parseTable(message.content);  // Some device commands send a table as JSON text.
        return table ? tableText(table) : message.content;  // Show a table in columns, and show other text as it is.
    }

    function parseTable(text) {
        var trimmed = text.trim();  // The device can add white space around the JSON text.
        if (trimmed.charAt(0) !== '{') return null;  // Only a JSON object can hold a table.
        try {
            var value = JSON.parse(trimmed);  // Read the JSON object.
            return value && Array.isArray(value.columns) && Array.isArray(value.rows) ? value : null;  // A table has columns and rows.
        } catch (error) {
            return null;  // Text that is not JSON stays as it is.
        }
    }

    function tableText(table) {
        var columns = table.columns.map(columnSpec);  // The header text and the row key of each column.
        var header = columns.map(function(column) { return column.title; });  // The header cells.
        var rows = table.rows.map(function(row) { return columns.map(function(column) { return cellText(row, column); }); });  // The body cells.
        var widths = header.map(function(title, index) { return columnWidth(title, rows, index); });  // The width of each column.
        var lines = [padCells(header, widths), padCells(widths.map(function(width) { return '-'.repeat(width); }), widths)];  // The header and the rule line.
        rows.forEach(function(cells) { lines.push(padCells(cells, widths)); });  // One line for each table row.
        if (!rows.length) lines.push('The device sent an empty table.');  // Tell the operator that no row arrived.
        if (table.message) lines.push(String(table.message));  // Keep the note that the device sent.
        return lines.join('\n');  // One text block for the view and the filter.
    }

    function columnSpec(column, index) {
        var spec = column && typeof column === 'object' ? column : { id: String(column) };  // A column can be a name or an object.
        return { key: spec.id, index: index, title: String(spec.display_name || spec.id || 'Column ' + (index + 1)) };  // The header text and the row key.
    }

    function cellText(row, column) {
        var value = Array.isArray(row) ? row[column.index] : (row || {})[column.key];  // A row can be a list or an object.
        if (value === null || value === undefined) return '';  // An empty cell shows no text.
        return typeof value === 'object' ? JSON.stringify(value) : String(value);  // A nested value shows as compact JSON.
    }

    function columnWidth(title, rows, index) {
        return rows.reduce(function(width, cells) { return Math.max(width, cells[index].length); }, title.length);  // The longest cell sets the width.
    }

    function padCells(cells, widths) {
        return cells.map(function(cell, index) { return cell.padEnd(widths[index]); }).join('  ').trimEnd();  // Align each cell under its header.
    }

    function setPaused(paused) {
        state.paused = paused;  // The poll code reads this flag.
        show(byId('wsPauseButton'), !paused);  // Show the action that applies now.
        show(byId('wsResumeButton'), paused);  // Show the action that applies now.
    }

    function resumePolling() {
        setPaused(false);  // Allow reads again.
        pollSelectedSession();  // Read the waiting messages at once.
    }

    function clearMessages() {
        state.messages = [];  // The next read adds only newer messages.
        renderMessages();  // Show the empty view.
    }

    function stopSelectedSession() {
        var session = state.selectedSession;  // The session of the message panel.
        if (!session) return;  // No session means nothing to stop.
        byId('wsStopButton').disabled = true;  // One click sends one stop request.
        apiJson('/api/websockets/sessions/' + encodeURIComponent(session.session_id) + '/stop', { method: 'POST' }).then(function(payload) {
            if (payload.error) setText('wsSessionReason', payload.error);  // Show why the stop failed.
            else applyStoppedSession(payload);  // Show the stopping state.
            loadSessions(true);  // Update the list and the live count.
        });
    }

    function applyStoppedSession(session) {
        if (!isSelected(session)) return;  // The operator chose another session.
        state.selectedSession = session;  // Keep the newest state.
        updateSessionHeader(session);  // Show the stopping state.
        updateSessionItem(session);  // Keep the list equal to the panel.
        if (isTerminalSession(session)) return;  // The terminal read loop observes the final state.
        if (!state.pollTimer) startPollTimer();  // Read the last messages until the runner closes.
    }

    window.MistWebSocketOutput = Object.freeze({
        filterLineText: filterLineText,  // Let the unit test execute the production line filter.
        joinLineText: joinLineText  // Let the unit test execute the production chunk join.
    });  // Publish the pure output operations without exposing page state.

    document.addEventListener('DOMContentLoaded', init);  // Start after the page markup exists.
})();
