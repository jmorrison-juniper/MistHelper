/* global getCsrfToken, readJsonAnswer */

(function() {
    'use strict';

    var state = {
        catalog: { channels: [], utilities: [], ready: false, reason: '' },
        selectedEntry: null,
        selectedSession: null,
        nextAfter: 0,
        paused: false,
        pollTimer: null,
        messages: [],
        labels: {}
    };

    function byId(id) {
        return document.getElementById(id);
    }

    function show(element, visible) {
        if (!element) return;
        element.classList.toggle('d-none', !visible);
    }

    function setText(id, value) {
        var element = byId(id);
        if (element) element.textContent = value || '';
    }

    function clearNode(node) {
        if (!node) return;
        while (node.firstChild) node.removeChild(node.firstChild);
    }

    function make(tag, className, text) {
        var element = document.createElement(tag);
        if (className) element.className = className;
        if (text !== undefined) element.textContent = text;
        return element;
    }

    function apiJson(url, options) {
        var request = options || {};
        request.headers = request.headers || {};
        if (request.method && request.method !== 'GET') request.headers['X-CSRFToken'] = getCsrfToken();
        if (request.body && !request.headers['Content-Type']) request.headers['Content-Type'] = 'application/json';
        return fetch(url, request).then(readJsonAnswer);
    }

    function init() {
        if (!byId('wsCatalog')) return;
        wireStaticEvents();
        loadCatalog();
        loadSessions();
    }

    function wireStaticEvents() {
        byId('wsStartForm').addEventListener('submit', startSelected);
        byId('wsCatalogFilter').addEventListener('input', renderCatalog);
        byId('wsPauseButton').addEventListener('click', pausePolling);
        byId('wsResumeButton').addEventListener('click', resumePolling);
        byId('wsClearButton').addEventListener('click', clearMessages);
        byId('wsStopButton').addEventListener('click', stopSelectedSession);
        byId('wsMessageFilter').addEventListener('input', renderMessages);
        byId('wsShellSend').addEventListener('click', sendShellLine);
        document.querySelectorAll('[data-ws-key]').forEach(function(button) {
            button.addEventListener('click', function() { sendShellKey(button.getAttribute('data-ws-key')); });
        });
    }

    function loadCatalog() {
        apiJson('/api/websockets/catalog').then(function(payload) {
            state.catalog = payload;
            renderReadyState(payload);
            renderCatalog();
        });
    }

    function renderReadyState(payload) {
        var alert = byId('wsReadyAlert');
        show(alert, !payload.ready);
        if (!payload.ready) alert.textContent = payload.reason || 'The WebSocket engine is not ready.';
        setText('wsCatalogCount', String((payload.channels || []).length + (payload.utilities || []).length));
    }

    function renderCatalog() {
        var container = byId('wsCatalog');
        var filter = (byId('wsCatalogFilter').value || '').toLowerCase();
        clearNode(container);
        renderChannelGroups(container, filter);
        renderUtilityGroups(container, filter);
    }

    function renderChannelGroups(container, filter) {
        var groups = groupBy(state.catalog.channels || [], 'scope');
        Object.keys(groups).forEach(function(scope) {
            appendGroup(container, 'Channels: ' + scope, groups[scope], filter, 'channel');
        });
    }

    function renderUtilityGroups(container, filter) {
        var groups = groupBy(state.catalog.utilities || [], 'family');
        Object.keys(groups).forEach(function(family) {
            appendGroup(container, 'Utilities: ' + family.toUpperCase(), groups[family], filter, 'utility');
        });
    }

    function groupBy(entries, key) {
        var groups = {};
        entries.forEach(function(entry) {
            var name = entry[key] || 'other';
            if (!groups[name]) groups[name] = [];
            groups[name].push(entry);
        });
        return groups;
    }

    function appendGroup(container, title, entries, filter, type) {
        var card = make('div', 'ws-catalog-group mb-2');
        card.appendChild(make('h6', 'text-muted', title));
        entries.forEach(function(entry) {
            if (!matchesFilter(entry, filter)) return;
            card.appendChild(catalogButton(entry, type));
        });
        container.appendChild(card);
    }

    function matchesFilter(entry, filter) {
        if (!filter) return true;
        return ((entry.name || '') + ' ' + (entry.description || '') + ' ' + (entry.key || '')).toLowerCase().indexOf(filter) >= 0;
    }

    function catalogButton(entry, type) {
        var button = make('button', 'btn btn-sm btn-outline-secondary ws-catalog-entry w-100 text-start mb-1');
        button.type = 'button';
        button.dataset.testid = 'ws-catalog-entry-' + entry.key;
        button.appendChild(make('span', 'fw-semibold', entry.name || entry.key));
        button.appendChild(make('span', 'badge bg-secondary ms-2', type));
        if (entry.safety) button.appendChild(make('span', 'badge bg-info ms-1', entry.safety));
        if (entry.locked) button.appendChild(make('span', 'badge bg-warning text-dark ms-1', 'Locked'));
        button.appendChild(make('div', 'small text-muted', entry.description || ''));
        button.addEventListener('click', function() { selectEntry(entry, type); });
        return button;
    }

    function selectEntry(entry, type) {
        state.selectedEntry = Object.assign({ entryType: type }, entry);
        setText('wsSelectedTitle', entry.name || entry.key);
        setText('wsSelectedDescription', entry.description || '');
        renderSafety(entry);
        renderStartForm(entry);
    }

    function renderSafety(entry) {
        var warning = byId('wsSafetyWarning');
        var needsWarning = entry.safety === 'change' || entry.safety === 'shell';
        show(warning, needsWarning || entry.locked);
        if (entry.locked) warning.textContent = 'Warning: This stream is locked by ' + lockName(entry) + '.';
        else if (needsWarning) warning.textContent = 'Warning: This stream can change device state or open a shell.';
    }

    function lockName(entry) {
        if (entry.safety === 'shell') return 'PORTAL_WS_ENABLE_SHELL';
        if (entry.safety === 'change') return 'PORTAL_WS_ENABLE_CHANGES';
        return 'a safety flag';
    }

    function renderStartForm(entry) {
        var targetBox = byId('wsTargetFields');
        var paramBox = byId('wsParameterFields');
        clearNode(targetBox);
        clearNode(paramBox);
        (entry.identifiers || entry.targets || []).forEach(function(field) { targetBox.appendChild(fieldControl(field, true)); });
        (entry.fields || []).forEach(function(field) { paramBox.appendChild(fieldControl(field, false)); });
        show(byId('wsConfirmationGroup'), entry.safety === 'change' || entry.safety === 'shell');
        byId('wsStartButton').disabled = !state.catalog.ready || entry.locked;
    }

    function fieldControl(field, isTarget) {
        var group = make('div', 'mb-3');
        var label = make('label', 'form-label', field.label || field.name);
        var input = make(field.picker ? 'select' : 'input', 'form-control');
        input.id = 'wsField-' + field.name;
        input.dataset.wsField = field.name;
        input.dataset.wsTarget = isTarget ? '1' : '0';
        input.dataset.wsKind = field.kind || 'text';
        input.dataset.wsPicker = field.picker || '';
        input.dataset.testid = 'ws-field-' + field.name;
        if (field.picker) configurePicker(input, field);
        else configureInput(input, field);
        label.setAttribute('for', input.id);
        group.appendChild(label);
        group.appendChild(input);
        if (field.hint) group.appendChild(make('div', 'form-text', field.hint));
        return group;
    }

    function configureInput(input, field) {
        input.type = field.kind === 'integer' ? 'number' : 'text';
        if (field.minimum !== null && field.minimum !== undefined) input.min = String(field.minimum);
        if (field.maximum !== null && field.maximum !== undefined) input.max = String(field.maximum);
        if (field.default !== null && field.default !== undefined) input.value = String(field.default);
        if (field.required) input.required = true;
        if (field.kind === 'boolean') input.type = 'checkbox';
    }

    function configurePicker(input, field) {
        input.classList.add('form-select');
        if (field.name === state.selectedEntry.repeatable) input.multiple = true;
        if (field.required) input.required = true;
        input.addEventListener('change', function() { onPickerChanged(input); });
        loadPickerOptions(input, field);
    }

    function onPickerChanged(input) {
        state.labels[input.value] = input.options[input.selectedIndex] ? input.options[input.selectedIndex].textContent : input.value;
        document.querySelectorAll('select[data-ws-picker]').forEach(function(select) {
            if (select === input) return;
            if (select.dataset.wsPicker === 'devices' || select.dataset.wsPicker === 'maps') loadPickerOptions(select, fieldFromSelect(select));
            if (select.dataset.wsPicker === 'sdkclients') loadPickerOptions(select, fieldFromSelect(select));
        });
    }

    function fieldFromSelect(select) {
        return { name: select.dataset.wsField, picker: select.dataset.wsPicker, required: select.required };
    }

    function loadPickerOptions(select, field) {
        var url = pickerUrl(field.picker);
        clearNode(select);
        select.appendChild(new Option('Loading...', ''));
        if (!url) {
            clearNode(select);
            select.appendChild(new Option('Choose the parent value first.', ''));
            return;
        }
        apiJson(url).then(function(payload) {
            fillPicker(select, payload.rows || payload.sites || [], payload.reason);
        });
    }

    function pickerUrl(name) {
        var site = valueOf('site_id');
        var map = valueOf('map_id');
        if (name === 'sites') return '/api/operations/sites';
        if (name === 'devices' && site) return '/api/websockets/sites/' + encodeURIComponent(site) + '/devices';
        if (name === 'maps' && site) return '/api/websockets/sites/' + encodeURIComponent(site) + '/maps';
        if (name === 'assets' && site) return '/api/websockets/sites/' + encodeURIComponent(site) + '/assets';
        if (name === 'sdkclients' && site && map) return '/api/websockets/sites/' + encodeURIComponent(site) + '/maps/' + encodeURIComponent(map) + '/sdkclients';
        if (name === 'mxedges') return '/api/websockets/mxedges' + (site ? '?site_id=' + encodeURIComponent(site) : '');
        return '';
    }

    function fillPicker(select, rows, reason) {
        clearNode(select);
        if (!rows.length) select.appendChild(new Option(reason || 'No rows are available.', ''));
        rows.forEach(function(row) {
            var option = new Option(row.label || row.name || row.id, row.id);
            option.dataset.family = row.family || '';
            option.dataset.detail = row.detail || '';
            select.appendChild(option);
            state.labels[row.id] = option.textContent;
        });
    }

    function valueOf(name) {
        var input = document.querySelector('[data-ws-field="' + name + '"]');
        return input ? input.value : '';
    }

    function startSelected(event) {
        event.preventDefault();
        if (!state.selectedEntry) return;
        var body = buildStartBody();
        apiJson('/api/websockets/sessions', { method: 'POST', body: JSON.stringify(body) }).then(function(payload) {
            if (payload.error) return showStartError(payload);
            showStartError(null);
            loadSessions(payload.session_id);
            selectSession(payload);
        });
    }

    function buildStartBody() {
        var entry = state.selectedEntry;
        var targets = collectValues('1');
        var parameters = collectValues('0');
        var kind = entry.entryType === 'channel' ? 'channel' : (entry.safety === 'shell' ? 'shell' : 'utility');
        return { kind: kind, key: entry.key, targets: targets, parameters: parameters, confirmation: byId('wsConfirmation').value || null, labels: state.labels };
    }

    function collectValues(targetFlag) {
        var values = {};
        document.querySelectorAll('[data-ws-target="' + targetFlag + '"]').forEach(function(input) {
            var name = input.dataset.wsField;
            if (input.type === 'checkbox') values[name] = input.checked;
            else if (input.multiple) values[name] = Array.from(input.selectedOptions).map(function(option) { return option.value; }).filter(Boolean);
            else if (input.value !== '') values[name] = input.value;
        });
        return values;
    }

    function showStartError(payload) {
        var alert = byId('wsStartError');
        show(alert, !!payload);
        if (payload) alert.textContent = limitText(payload);
    }

    function limitText(payload) {
        if (payload.code === 'limit_reached' && payload.live) return payload.error + ' Live sessions: ' + payload.live.join(', ');
        return payload.error || 'The portal refused the request.';
    }

    function loadSessions(selectId) {
        apiJson('/api/websockets/sessions').then(function(payload) {
            renderSessions(payload.sessions || [], payload.limits || {});
            if (selectId) return;
            restoreSelectedSession(payload.sessions || []);
        });
    }

    function renderSessions(sessions, limits) {
        var box = byId('wsSessionList');
        clearNode(box);
        setText('wsSessionLimit', String(limits.live_count || 0) + ' / ' + String(limits.max_sessions || 0));
        if (!sessions.length) box.appendChild(make('div', 'text-muted', 'No session is available.'));
        sessions.forEach(function(session) { box.appendChild(sessionButton(session)); });
    }

    function sessionButton(session) {
        var button = make('button', 'btn btn-outline-secondary w-100 text-start mb-2');
        button.type = 'button';
        button.dataset.testid = 'ws-session-' + session.session_id;
        button.appendChild(make('div', 'fw-semibold', session.title || session.key));
        button.appendChild(make('div', 'small', (session.state || '') + ' - ' + countersText(session)));
        button.addEventListener('click', function() { selectSession(session); });
        return button;
    }

    function restoreSelectedSession(sessions) {
        var saved = localStorage.getItem('misthelper-websocket-session');
        var session = sessions.find(function(item) { return item.session_id === saved; });
        if (session) selectSession(session);
    }

    function selectSession(session) {
        state.selectedSession = session;
        state.nextAfter = 0;
        state.messages = [];
        localStorage.setItem('misthelper-websocket-session', session.session_id);
        show(byId('wsMessagePanel'), true);
        updateSessionHeader(session);
        renderMessages();
        startPollTimer();
    }

    function updateSessionHeader(session) {
        setText('wsSessionTitle', session.title || session.key);
        setText('wsSessionState', 'State: ' + (session.state || 'unknown'));
        setText('wsSessionReason', session.reason || '');
        setText('wsCounters', countersText(session));
        byId('wsDownloadLink').href = '/api/websockets/sessions/' + encodeURIComponent(session.session_id) + '/download';
        show(byId('wsTerminalInput'), session.output === 'terminal');
    }

    function countersText(session) {
        var counters = session.counters || {};
        return 'Messages: ' + (counters.received || 0) + ', dropped: ' + (counters.dropped || 0) + ', rate: ' + (session.rate_per_second || 0) + '/s';
    }

    function startPollTimer() {
        if (state.pollTimer) window.clearInterval(state.pollTimer);
        pollSelectedSession();
        state.pollTimer = window.setInterval(pollSelectedSession, 1000);
    }

    function pollSelectedSession() {
        var session = state.selectedSession;
        if (!session || state.paused) return;
        var url = '/api/websockets/sessions/' + encodeURIComponent(session.session_id) + '/messages?after=' + state.nextAfter + '&limit=200';
        apiJson(url).then(function(payload) {
            if (payload.error) return;
            state.selectedSession = payload.session || session;
            state.nextAfter = payload.next_after || state.nextAfter;
            state.messages = state.messages.concat(payload.messages || []);
            updateSessionHeader(state.selectedSession);
            renderMessages();
            if (!state.selectedSession.live && state.pollTimer) window.clearInterval(state.pollTimer);
        });
    }

    function renderMessages() {
        var output = byId('wsOutput');
        var filter = (byId('wsMessageFilter').value || '').toLowerCase();
        clearNode(output);
        var messages = state.messages.filter(function(message) { return messageText(message).toLowerCase().indexOf(filter) >= 0; });
        if (state.selectedSession && state.selectedSession.output === 'screen') renderScreen(output, messages);
        else if (state.selectedSession && state.selectedSession.output === 'terminal') renderTerminal(output, messages);
        else if (state.selectedSession && state.selectedSession.output === 'packets') renderPackets(output, messages);
        else renderRows(output, messages);
    }

    function renderRows(output, messages) {
        messages.forEach(function(message) {
            var row = make('div', 'ws-message-row');
            row.appendChild(make('div', 'small text-muted', '#' + message.seq + ' ' + (message.source || '') + ' ' + (message.received_at || '')));
            row.appendChild(make('pre', 'mb-0', messageText(message)));
            output.appendChild(row);
        });
    }

    function renderScreen(output, messages) {
        var newest = messages[messages.length - 1];
        output.appendChild(make('pre', 'ws-screen mb-0', newest ? messageText(newest) : 'No screen output yet.'));
    }

    function renderPackets(output, messages) {
        messages.forEach(function(message) {
            output.appendChild(make('div', 'ws-packet-row', message.summary || messageText(message)));
        });
    }

    function renderTerminal(output, messages) {
        var terminal = make('pre', 'ws-terminal mb-0');
        terminal.dataset.testid = 'ws-terminal';
        terminal.textContent = messages.map(messageText).join('\n') || 'The terminal has no output yet.';
        output.appendChild(terminal);
    }

    function messageText(message) {
        if (message.summary) return message.summary;
        if (typeof message.content === 'string') return message.content;
        return JSON.stringify(message.content, null, 2);
    }

    function pausePolling() {
        state.paused = true;
        show(byId('wsPauseButton'), false);
        show(byId('wsResumeButton'), true);
    }

    function resumePolling() {
        state.paused = false;
        show(byId('wsPauseButton'), true);
        show(byId('wsResumeButton'), false);
        pollSelectedSession();
    }

    function clearMessages() {
        state.messages = [];
        renderMessages();
    }

    function stopSelectedSession() {
        if (!state.selectedSession) return;
        apiJson('/api/websockets/sessions/' + encodeURIComponent(state.selectedSession.session_id) + '/stop', { method: 'POST' }).then(function(payload) {
            if (!payload.error) selectSession(payload);
            loadSessions();
        });
    }

    function sendShellLine() {
        var input = byId('wsShellLine');
        sendShellPayload({ line: input.value });
        input.value = '';
    }

    function sendShellKey(key) {
        sendShellPayload({ key: key });
    }

    function sendShellPayload(payload) {
        if (!state.selectedSession) return;
        apiJson('/api/websockets/sessions/' + encodeURIComponent(state.selectedSession.session_id) + '/input', { method: 'POST', body: JSON.stringify(payload) });
    }

    document.addEventListener('DOMContentLoaded', init);
})();
