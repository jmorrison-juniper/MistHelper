/**
 * operations.js - MistHelper Web Portal Operations Controller
 *
 * Handles operation listing, category accordion, parameter form rendering
 * (site/device/client dropdowns, text/number/choice inputs, dependency
 * chains), execution via SSE, progress bars, and log streaming.
 */

/* global getCsrfToken, connectSSE, formatTimestamp, DataPreviewModal */

var selectedMenuNumber = null;
var selectedCategory = null;
var currentRunId = null;
var currentSSE = null;
var currentParameters = [];

// ---------------------------------------------------------------------------
// Operation Listing
// ---------------------------------------------------------------------------

function loadOperations() {
    fetch('/api/operations/list')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            renderAccordion(data.categories || []);
            document.getElementById('opLoading').classList.add('d-none');
        })
        .catch(function() {
            document.getElementById('opLoading').textContent = 'Failed to load operations.';
        });
}

function renderAccordion(categories) {
    var container = document.getElementById('operationAccordion');
    var html = '';
    categories.forEach(function(cat, index) {
        var collapseId = 'cat' + index;
        html += buildAccordionItem(cat, collapseId);
    });
    container.insertAdjacentHTML('beforeend', html);
}

function buildAccordionItem(cat, collapseId) {
    var html = '<div class="accordion-item">';
    html += '<h2 class="accordion-header">';
    html += '<button class="accordion-button collapsed" type="button" ';
    html += 'data-bs-toggle="collapse" data-bs-target="#' + collapseId + '">';
    html += escapeHtml(cat.name) + ' (' + cat.operations.length + ')';
    html += '</button></h2>';
    html += '<div id="' + collapseId + '" class="accordion-collapse collapse">';
    html += '<div class="accordion-body p-0">';
    html += '<ul class="list-group list-group-flush">';
    cat.operations.forEach(function(op) {
        html += buildOperationItem(op);
    });
    html += '</ul></div></div></div>';
    return html;
}

function buildOperationItem(op) {
    var badge = buildCategoryBadge(op.category);
    var html = '<li class="list-group-item list-group-item-action op-item" ';
    html += 'data-menu="' + op.menu_number + '" ';
    html += 'data-category="' + (op.category || 'non_interactive') + '" ';
    html += 'onclick="selectOperation(' + op.menu_number + ', this)">';
    html += '<strong class="me-2">' + op.menu_number + '</strong> ';
    html += escapeHtml(op.description) + badge;
    html += '</li>';
    return html;
}

function buildCategoryBadge(category) {
    if (category === 'interactive') {
        return ' <span class="badge bg-info badge-op-category">interactive</span>';
    }
    if (category === 'cli_only') {
        return ' <span class="badge bg-warning text-dark badge-op-category">SSH only</span>';
    }
    return '';
}

// ---------------------------------------------------------------------------
// Operation Selection
// ---------------------------------------------------------------------------

function selectOperation(menuNumber, element) {
    selectedMenuNumber = String(menuNumber);
    selectedCategory = element ? element.getAttribute('data-category') : 'non_interactive';
    highlightActiveItem(element);
    showSelectedPanel(menuNumber, element);
    resetParameterPanels();
    loadParameters(menuNumber);
    document.getElementById('runBtn').disabled = false;
}

function highlightActiveItem(element) {
    document.querySelectorAll('.op-item').forEach(function(el) {
        el.classList.remove('active');
    });
    if (element) element.classList.add('active');
}

function showSelectedPanel(menuNumber, element) {
    var panel = document.getElementById('selectedOp');
    panel.classList.remove('d-none');
    document.getElementById('selectedOpTitle').textContent = 'Menu ' + menuNumber;
    document.getElementById('selectedOpDesc').textContent = element
        ? element.textContent.trim().replace(/interactive|SSH only/g, '').trim()
        : '';
}

function resetParameterPanels() {
    document.getElementById('cliOnlyPanel').classList.add('d-none');
    document.getElementById('parameterForm').classList.add('d-none');
    document.getElementById('parameterError').classList.add('d-none');
    document.getElementById('parameterFields').innerHTML = '';
    currentParameters = [];
}

// ---------------------------------------------------------------------------
// Parameter Loading
// ---------------------------------------------------------------------------

function loadParameters(menuNumber) {
    var formDiv = document.getElementById('parameterForm');
    var fieldsDiv = document.getElementById('parameterFields');
    var loadingDiv = document.getElementById('parameterLoading');

    fieldsDiv.innerHTML = '';
    loadingDiv.classList.remove('d-none');
    formDiv.classList.remove('d-none');

    fetch('/api/operations/parameters/' + menuNumber)
        .then(function(response) { return response.json(); })
        .then(function(data) {
            loadingDiv.classList.add('d-none');
            handleParameterResponse(data, formDiv, fieldsDiv);
        })
        .catch(function(err) {
            loadingDiv.classList.add('d-none');
            showParameterError('Failed to load parameters: ' + err.message);
        });
}

function handleParameterResponse(data, formDiv, fieldsDiv) {
    var runBtn = document.getElementById('runBtn');

    if (data.category === 'cli_only') {
        showCliOnlyPanel(data.cli_only_message);
        runBtn.disabled = true;
        runBtn.classList.add('d-none');
        formDiv.classList.add('d-none');
        return;
    }

    runBtn.classList.remove('d-none');
    if (data.parameters && data.parameters.length > 0) {
        currentParameters = data.parameters;
        renderParameterFields(data.parameters, fieldsDiv);
        formDiv.classList.remove('d-none');
        validateForm();
    } else {
        formDiv.classList.add('d-none');
    }
}

function showCliOnlyPanel(message) {
    var cliPanel = document.getElementById('cliOnlyPanel');
    cliPanel.classList.remove('d-none');
    document.getElementById('cliOnlyMessage').textContent =
        message || 'This operation requires SSH access on port 2200.';
}

function retryLoadParameters() {
    document.getElementById('parameterError').classList.add('d-none');
    if (selectedMenuNumber) loadParameters(selectedMenuNumber);
}

function showParameterError(msg) {
    var errorDiv = document.getElementById('parameterError');
    document.getElementById('parameterErrorMsg').textContent = msg;
    errorDiv.classList.remove('d-none');
    document.getElementById('parameterForm').classList.remove('d-none');
}

// ---------------------------------------------------------------------------
// Parameter Field Rendering
// ---------------------------------------------------------------------------

function renderParameterFields(params, container) {
    params.forEach(function(param) {
        var div = buildParameterGroup(param);
        container.appendChild(div);
    });
}

function buildParameterGroup(param) {
    var div = document.createElement('div');
    div.className = 'mb-3';
    div.id = 'param-group-' + param.name;

    var label = buildParameterLabel(param);
    div.appendChild(label);

    var control = createParameterControl(param);
    div.appendChild(control);

    if (param.depends_on) div.classList.add('d-none');
    return div;
}

function buildParameterLabel(param) {
    var label = document.createElement('label');
    label.className = 'form-label';
    label.textContent = param.label || param.name;
    if (param.required) {
        label.innerHTML += ' <span class="text-danger">*</span>';
    }
    return label;
}

function createParameterControl(param) {
    switch (param.param_type) {
        case 'site':    return createSiteDropdown(param);
        case 'device':  return createDeviceDropdown(param);
        case 'client':  return createClientDropdown(param);
        case 'choice':  return createChoiceDropdown(param);
        case 'number':  return createNumberInput(param);
        case 'text':
        default:        return createTextInput(param);
    }
}

// ---------------------------------------------------------------------------
// Site Dropdown
// ---------------------------------------------------------------------------

function createSiteDropdown(param) {
    var select = buildSelect(param);
    select.innerHTML = '<option value="">Loading sites...</option>';
    select.disabled = true;

    select.addEventListener('change', function() {
        handleDependencyChange(param.name, select.value);
        validateForm();
    });

    fetchSites(select);
    return select;
}

function fetchSites(selectElement) {
    fetch('/api/operations/sites')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            populateSiteOptions(selectElement, data.sites || []);
        })
        .catch(function() {
            selectElement.innerHTML = '<option value="">Failed to load sites</option>';
            selectElement.disabled = false;
        });
}

function populateSiteOptions(selectElement, sites) {
    selectElement.innerHTML = '<option value="">-- Select Site --</option>';
    sites.forEach(function(site) {
        var opt = document.createElement('option');
        opt.value = site.name;
        opt.textContent = site.address ? site.name + ' (' + site.address + ')' : site.name;
        opt.dataset.siteId = site.id;
        selectElement.appendChild(opt);
    });
    selectElement.disabled = false;
    if (sites.length === 0) {
        selectElement.innerHTML = '<option value="">No sites found</option>';
    }
}

// ---------------------------------------------------------------------------
// Device Dropdown
// ---------------------------------------------------------------------------

function createDeviceDropdown(param) {
    var select = buildSelect(param);
    select.innerHTML = '<option value="">-- Select site first --</option>';
    select.disabled = true;
    select.dataset.deviceFilter = param.device_filter || 'all';

    select.addEventListener('change', function() {
        handleDependencyChange(param.name, select.value);
        validateForm();
    });

    return select;
}

function fetchDevices(siteSelect, deviceSelect) {
    var siteId = getSelectedDataAttr(siteSelect, 'siteId');
    if (!siteId) {
        deviceSelect.innerHTML = '<option value="">-- Select site first --</option>';
        deviceSelect.disabled = true;
        return;
    }

    var filter = deviceSelect.dataset.deviceFilter || 'all';
    deviceSelect.innerHTML = '<option value="">Loading devices...</option>';
    deviceSelect.disabled = true;

    var url = '/api/operations/sites/' + encodeURIComponent(siteId) + '/devices?type=' + filter;
    fetch(url)
        .then(function(response) { return response.json(); })
        .then(function(data) {
            populateDeviceOptions(deviceSelect, data.devices || []);
        })
        .catch(function() {
            deviceSelect.innerHTML = '<option value="">Failed to load devices</option>';
            deviceSelect.disabled = false;
        });
}

function populateDeviceOptions(select, devices) {
    select.innerHTML = '<option value="">-- Select Device --</option>';
    devices.forEach(function(device) {
        var opt = document.createElement('option');
        opt.value = device.name || device.mac;
        opt.textContent = buildDeviceLabel(device);
        opt.dataset.deviceId = device.id;
        opt.dataset.deviceMac = device.mac;
        select.appendChild(opt);
    });
    select.disabled = false;
    if (devices.length === 0) {
        select.innerHTML = '<option value="">No devices found</option>';
    }
}

function buildDeviceLabel(device) {
    var label = device.name || device.mac;
    if (device.model) label += ' (' + device.model + ')';
    if (device.type) label += ' [' + device.type + ']';
    return label;
}

// ---------------------------------------------------------------------------
// Client Dropdown
// ---------------------------------------------------------------------------

function createClientDropdown(param) {
    var select = buildSelect(param);
    select.innerHTML = '<option value="">-- Select site first --</option>';
    select.disabled = true;

    select.addEventListener('change', function() { validateForm(); });
    return select;
}

function fetchClients(siteSelect, clientSelect) {
    var siteId = getSelectedDataAttr(siteSelect, 'siteId');
    if (!siteId) {
        clientSelect.innerHTML = '<option value="">-- Select site first --</option>';
        clientSelect.disabled = true;
        return;
    }

    clientSelect.innerHTML = '<option value="">Loading clients...</option>';
    clientSelect.disabled = true;

    fetch('/api/operations/sites/' + encodeURIComponent(siteId) + '/clients')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            populateClientOptions(clientSelect, data.clients || []);
        })
        .catch(function() {
            clientSelect.innerHTML = '<option value="">Failed to load clients</option>';
            clientSelect.disabled = false;
        });
}

function populateClientOptions(select, clients) {
    select.innerHTML = '<option value="">-- Select Client --</option>';
    clients.forEach(function(client, idx) {
        var opt = document.createElement('option');
        opt.value = String(idx);
        opt.textContent = buildClientLabel(client);
        opt.dataset.clientMac = client.mac;
        select.appendChild(opt);
    });
    select.disabled = false;
    if (clients.length === 0) {
        select.innerHTML = '<option value="">No clients found</option>';
    }
}

function buildClientLabel(client) {
    var label = client.mac;
    if (client.hostname) label = client.hostname + ' (' + client.mac + ')';
    if (client.ip) label += ' - ' + client.ip;
    return label;
}

// ---------------------------------------------------------------------------
// Choice / Text / Number Controls
// ---------------------------------------------------------------------------

function createChoiceDropdown(param) {
    var select = buildSelect(param);
    select.innerHTML = '<option value="">-- Select --</option>';
    (param.options || []).forEach(function(opt) {
        var option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.label;
        if (param.default && opt.value === param.default) option.selected = true;
        select.appendChild(option);
    });
    select.addEventListener('change', function() { validateForm(); });
    return select;
}

function createTextInput(param) {
    var input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control form-control-sm';
    input.name = param.name;
    input.id = 'param-' + param.name;
    input.placeholder = param.placeholder || '';
    if (param.default) input.value = param.default;
    if (param.required) input.required = true;
    input.addEventListener('input', function() { validateForm(); });
    return input;
}

function createNumberInput(param) {
    var input = document.createElement('input');
    input.type = 'number';
    input.className = 'form-control form-control-sm';
    input.name = param.name;
    input.id = 'param-' + param.name;
    input.placeholder = param.placeholder || '';
    if (param.default) input.value = param.default;
    if (param.min_value !== undefined) input.min = param.min_value;
    if (param.max_value !== undefined) input.max = param.max_value;
    if (param.required) input.required = true;
    input.addEventListener('input', function() { validateForm(); });
    return input;
}

// ---------------------------------------------------------------------------
// Shared Select Builder
// ---------------------------------------------------------------------------

function buildSelect(param) {
    var select = document.createElement('select');
    select.className = 'form-select form-select-sm';
    select.name = param.name;
    select.id = 'param-' + param.name;
    if (param.required) select.required = true;
    return select;
}

function getSelectedDataAttr(select, attr) {
    var opt = select.options[select.selectedIndex];
    return opt ? (opt.dataset[attr] || '') : '';
}

// ---------------------------------------------------------------------------
// Dependency Chain Handling
// ---------------------------------------------------------------------------

function handleDependencyChange(parentName, parentValue) {
    currentParameters.forEach(function(param) {
        if (param.depends_on !== parentName) return;
        updateDependentField(param, parentValue);
    });
}

function updateDependentField(param, parentValue) {
    var group = document.getElementById('param-group-' + param.name);
    var control = document.getElementById('param-' + param.name);
    if (!group || !control) return;

    if (!parentValue) {
        group.classList.add('d-none');
        return;
    }
    group.classList.remove('d-none');

    var siteSelect = document.getElementById('param-site_id');
    if (param.param_type === 'device' && siteSelect) {
        fetchDevices(siteSelect, control);
    } else if (param.param_type === 'client' && siteSelect) {
        fetchClients(siteSelect, control);
    }
}

// ---------------------------------------------------------------------------
// Form Validation
// ---------------------------------------------------------------------------

function validateForm() {
    var valid = true;
    var runBtn = document.getElementById('runBtn');

    currentParameters.forEach(function(param) {
        if (!isFieldInvalid(param)) return;
        valid = false;
    });

    if (runBtn && selectedCategory !== 'cli_only') {
        runBtn.disabled = !valid;
    }
    return valid;
}

function isFieldInvalid(param) {
    var control = document.getElementById('param-' + param.name);
    if (!control || !param.required) return false;

    var group = document.getElementById('param-group-' + param.name);
    if (group && group.classList.contains('d-none')) return false;

    var empty = !control.value || control.value === '';
    if (empty) {
        control.classList.add('is-invalid');
    } else {
        control.classList.remove('is-invalid');
    }
    return empty;
}

// ---------------------------------------------------------------------------
// Run Operation
// ---------------------------------------------------------------------------

function runSelectedOperation() {
    if (selectedMenuNumber === null) return;
    if (selectedCategory === 'cli_only') return;
    if (currentParameters.length > 0 && !validateForm()) return;

    var inputAnswers = collectInputAnswers();
    var btn = document.getElementById('runBtn');
    btn.disabled = true;
    btn.textContent = 'Starting...';
    resetExecutionPanel();

    var body = { menu_number: selectedMenuNumber };
    if (inputAnswers.length > 0) {
        body.parameters = { input_answers: inputAnswers };
    }

    fetch('/api/operations/run', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(body)
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.error) {
            showError(data.error);
            btn.disabled = false;
            btn.textContent = 'Run Operation';
            return;
        }
        currentRunId = data.run_id;
        setStatus('running', 'Operation started');
        document.getElementById('stopBtn').classList.remove('d-none');
        startSSEStream(data.run_id);
    })
    .catch(function(err) {
        showError('Failed to start operation: ' + err.message);
        btn.disabled = false;
        btn.textContent = 'Run Operation';
    });
}

function collectInputAnswers() {
    var answers = [];
    currentParameters.forEach(function(param) {
        var control = document.getElementById('param-' + param.name);
        answers.push(control ? (control.value || '') : '');
    });
    return answers;
}

function stopRunningOperation() {
    if (!currentRunId) return;
    var btn = document.getElementById('stopBtn');
    btn.disabled = true;
    btn.textContent = 'Stopping...';

    fetch('/api/operations/stop/' + encodeURIComponent(currentRunId), {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.error) {
            appendLog('Stop request failed: ' + data.error, 'WARNING');
            btn.disabled = false;
            btn.textContent = 'Stop Operation';
        } else {
            appendLog('Stop signal sent - operation will stop after current cycle.', 'WARNING');
            setStatus('failed', 'Stopped by user');
            finishRun();
        }
    })
    .catch(function(err) {
        appendLog('Stop request error: ' + err.message, 'WARNING');
        btn.disabled = false;
        btn.textContent = 'Stop Operation';
    });
}

// ---------------------------------------------------------------------------
// SSE Streaming
// ---------------------------------------------------------------------------

function startSSEStream(runId) {
    if (currentSSE) {
        currentSSE.close();
    }

    var url = '/api/operations/stream?run_id=' + encodeURIComponent(runId);
    var source = new EventSource(url);
    currentSSE = source;

    source.addEventListener('log', function(event) {
        var data = JSON.parse(event.data);
        appendLog(data.message, data.level || 'INFO');
    });

    source.addEventListener('debug_log', function(event) {
        var data = JSON.parse(event.data);
        appendDebugLog(data.message, data.level || 'DEBUG');
    });

    source.addEventListener('status', function(event) {
        var data = JSON.parse(event.data);
        if (data.status === 'running') {
            setStatus('running', data.description || 'Running...');
        }
    });

    source.addEventListener('progress', function(event) {
        var data = JSON.parse(event.data);
        updateProgress(data.percent || 0, data.message || '');
    });

    source.addEventListener('complete', function(event) {
        var data = JSON.parse(event.data);
        setStatus('complete', data.message || 'Operation completed');
        updateProgress(100, 'Done');
        showOutputFiles(data.output_files || []);
        finishRun();
        source.close();
    });

    source.addEventListener('error_event', function(event) {
        var data = JSON.parse(event.data);
        setStatus('error', data.message || 'Operation failed');
        appendLog('ERROR: ' + (data.message || 'Unknown error'), 'ERROR');
        finishRun();
        source.close();
    });

    source.addEventListener('heartbeat', function() {
        // Keep-alive; nothing to display
    });

    source.onerror = function() {
        // Connection lost - check status via REST fallback
        if (currentRunId) {
            checkRunStatus(currentRunId);
        }
        source.close();
    };
}

function checkRunStatus(runId) {
    fetch('/api/operations/status/' + encodeURIComponent(runId))
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.status === 'completed') {
                setStatus('complete', 'Operation completed');
                updateProgress(100, 'Done');
                showOutputFiles(data.output_files || []);
                finishRun();
            } else if (data.status === 'failed') {
                setStatus('error', data.error_message || 'Operation failed');
                appendLog('ERROR: ' + (data.error_message || 'Unknown error'), 'ERROR');
                finishRun();
            }
            // If still running, SSE reconnect will handle it
        })
        .catch(function() {
            setStatus('error', 'Lost connection to server');
            finishRun();
        });
}

// ---------------------------------------------------------------------------
// UI Helpers
// ---------------------------------------------------------------------------

function resetExecutionPanel() {
    var panel = document.getElementById('executionPanel');
    panel.classList.remove('d-none');
    document.getElementById('logViewer').innerHTML = '';
    document.getElementById('debugLogViewer').innerHTML = '';
    document.getElementById('debugLogToggle').classList.add('d-none');
    document.getElementById('debugLogPanel').classList.add('d-none');
    document.getElementById('debugLogCount').textContent = '0';
    document.getElementById('outputFiles').classList.add('d-none');
    document.getElementById('outputFileList').innerHTML = '';
    updateProgress(0, '');
    setStatus('pending', 'Waiting...');
}

function appendLog(message, level) {
    var viewer = document.getElementById('logViewer');
    var line = document.createElement('div');
    line.className = 'log-line';
    if (level === 'ERROR' || level === 'CRITICAL') {
        line.classList.add('text-danger');
    } else if (level === 'WARNING') {
        line.classList.add('text-warning');
    }
    var ts = new Date().toLocaleTimeString();
    line.textContent = '[' + ts + '] ' + message;
    viewer.appendChild(line);
    viewer.scrollTop = viewer.scrollHeight;
}

function appendDebugLog(message, level) {
    var toggle = document.getElementById('debugLogToggle');
    var viewer = document.getElementById('debugLogViewer');
    var counter = document.getElementById('debugLogCount');
    toggle.classList.remove('d-none');
    var count = parseInt(counter.textContent || '0', 10) + 1;
    counter.textContent = count;
    var line = document.createElement('div');
    line.className = 'log-line text-muted';
    var ts = new Date().toLocaleTimeString();
    line.textContent = '[' + ts + '] ' + message;
    viewer.appendChild(line);
    if (!document.getElementById('debugLogPanel').classList.contains('d-none')) {
        viewer.scrollTop = viewer.scrollHeight;
    }
}

function toggleDebugLog() {
    var panel = document.getElementById('debugLogPanel');
    var btn = document.getElementById('debugLogToggle');
    var viewer = document.getElementById('debugLogViewer');
    if (panel.classList.contains('d-none')) {
        panel.classList.remove('d-none');
        btn.innerHTML = '&#9660; Debug Log <span class="badge bg-secondary ms-1" id="debugLogCount">' +
            document.getElementById('debugLogCount').textContent + '</span>';
        viewer.scrollTop = viewer.scrollHeight;
    } else {
        panel.classList.add('d-none');
        btn.innerHTML = '&#9654; Debug Log <span class="badge bg-secondary ms-1" id="debugLogCount">' +
            document.getElementById('debugLogCount').textContent + '</span>';
    }
}

function updateProgress(percent, message) {
    var bar = document.getElementById('progressBar');
    var pct = Math.min(100, Math.max(0, percent));
    bar.style.width = pct + '%';
    bar.setAttribute('aria-valuenow', pct);
    bar.textContent = pct + '%';

    if (message) {
        document.getElementById('statusMessage').textContent = message;
    }
}

function setStatus(state, message) {
    var badge = document.getElementById('statusBadge');
    badge.textContent = state.charAt(0).toUpperCase() + state.slice(1);

    badge.className = 'badge';
    if (state === 'running') {
        badge.classList.add('bg-primary');
    } else if (state === 'complete') {
        badge.classList.add('bg-success');
    } else if (state === 'error') {
        badge.classList.add('bg-danger');
    } else {
        badge.classList.add('bg-secondary');
    }

    if (message) {
        document.getElementById('statusMessage').textContent = message;
    }
}

function showError(msg) {
    resetExecutionPanel();
    setStatus('error', msg);
    appendLog(msg, 'ERROR');
}

function showOutputFiles(files) {
    if (!files || files.length === 0) return;

    var panel = document.getElementById('outputFiles');
    var list = document.getElementById('outputFileList');
    panel.classList.remove('d-none');

    files.forEach(function(file) {
        var li = document.createElement('li');
        li.className = 'd-flex gap-2 align-items-center mb-1';

        var link = document.createElement('a');
        link.href = '/api/data/download/' + encodeURIComponent(file);
        link.textContent = file;
        link.className = 'text-accent';
        li.appendChild(link);

        if (typeof DataPreviewModal !== 'undefined' && isPreviewable(file)) {
            li.appendChild(buildPreviewButton(file));
        }

        list.appendChild(li);
    });
}

function buildPreviewButton(filepath) {
    var btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-outline-primary';
    btn.textContent = 'Preview';
    btn.onclick = function() { DataPreviewModal.open(filepath); };
    return btn;
}

function isPreviewable(filename) {
    var ext = filename.split('.').pop().toLowerCase();
    return ['csv', 'json', 'log', 'db', 'sqlite'].indexOf(ext) >= 0;
}

function finishRun() {
    currentRunId = null;
    currentSSE = null;
    var btn = document.getElementById('runBtn');
    btn.disabled = false;
    btn.textContent = 'Run Operation';
    var stopBtn = document.getElementById('stopBtn');
    stopBtn.classList.add('d-none');
    stopBtn.disabled = false;
    stopBtn.textContent = 'Stop Operation';
    refreshActiveOps();
}

// ---------------------------------------------------------------------------
// Active Operations Panel
// ---------------------------------------------------------------------------

function refreshActiveOps() {
    fetch('/api/operations/active')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            var runs = data.active_runs || data.active || [];
            renderActiveOps(runs);
        })
        .catch(function() {
            // Silently fail - non-critical
        });
}

function renderActiveOps(runs) {
    var panel = document.getElementById('activeOpsPanel');
    var list = document.getElementById('activeOpsList');

    if (runs.length === 0) {
        panel.classList.add('d-none');
        return;
    }

    panel.classList.remove('d-none');
    list.innerHTML = '';
    runs.forEach(function(run) {
        var div = document.createElement('div');
        div.className = 'portal-card mb-2 p-2';
        div.style.cursor = 'pointer';
        div.title = 'Click to view logs and manage this operation';
        var isActive = (currentRunId === run.run_id);
        if (isActive) {
            div.style.borderLeft = '3px solid var(--accent-color, #0d6efd)';
        }
        div.innerHTML = '<div class="d-flex justify-content-between align-items-center">' +
            '<div><strong>Menu ' + escapeHtml(run.menu_number) + '</strong> ' +
            '<span class="badge bg-primary">Running</span>' +
            '<br><small class="text-muted">' + escapeHtml(run.description || '') + '</small>' +
            '<br><small class="text-muted text-xs">' +
            escapeHtml(run.run_id || '') + '</small></div>' +
            '<button class="btn btn-sm btn-outline-danger ms-2 stop-active-btn" ' +
            'title="Stop this operation" ' +
            'onclick="event.stopPropagation(); stopActiveOperation(\'' +
            escapeHtml(run.run_id) + '\')">' +
            'Stop</button></div>';
        div.addEventListener('click', function() {
            reconnectToOperation(run.run_id, run.menu_number, run.description);
        });
        list.appendChild(div);
    });
}

function reconnectToOperation(runId, menuNumber, description) {
    if (currentSSE) { currentSSE.close(); }
    currentRunId = runId;
    selectedMenuNumber = menuNumber;

    var titleEl = document.getElementById('selectedOpTitle');
    var descEl = document.getElementById('selectedOpDesc');
    var selectedPanel = document.getElementById('selectedOp');
    titleEl.textContent = 'Menu ' + menuNumber;
    descEl.textContent = description || '';
    selectedPanel.classList.remove('d-none');

    document.getElementById('parameterForm').classList.add('d-none');
    document.getElementById('cliOnlyPanel').classList.add('d-none');
    document.getElementById('runBtn').disabled = true;
    document.getElementById('runBtn').textContent = 'Running...';
    document.getElementById('stopBtn').classList.remove('d-none');

    resetExecutionPanel();
    setStatus('running', 'Reconnected to Menu ' + menuNumber);
    replayExistingLogs(runId);
    startSSEStream(runId);
}

function replayExistingLogs(runId) {
    fetch('/api/operations/status/' + encodeURIComponent(runId))
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.log_messages) {
                data.log_messages.forEach(function(entry) {
                    appendLog(entry.message, entry.level || 'INFO');
                });
            }
            if (data.debug_messages) {
                data.debug_messages.forEach(function(entry) {
                    appendDebugLog(entry.message, entry.level || 'DEBUG');
                });
            }
            if (data.output_files && data.output_files.length > 0) {
                showOutputFiles(data.output_files);
            }
            if (data.status === 'completed') {
                setStatus('complete', 'Operation completed');
                updateProgress(100, 'Done');
                finishRun();
            } else if (data.status === 'failed') {
                setStatus('error', data.error_message || 'Operation failed');
                finishRun();
            }
        })
        .catch(function(err) {
            appendLog('Could not load existing logs: ' + err.message, 'WARNING');
        });
}

function stopActiveOperation(runId) {
    fetch('/api/operations/stop/' + encodeURIComponent(runId), {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.error) {
            alert('Stop failed: ' + data.error);
        } else {
            refreshActiveOps();
        }
    })
    .catch(function(err) {
        alert('Stop request error: ' + err.message);
    });
}

// ---------------------------------------------------------------------------
// Search Filter
// ---------------------------------------------------------------------------

function setupSearch() {
    var input = document.getElementById('opSearch');
    if (!input) { return; }

    input.addEventListener('input', function() {
        var query = input.value.toLowerCase().trim();
        document.querySelectorAll('.op-item').forEach(function(item) {
            var text = item.textContent.toLowerCase();
            item.style.display = text.indexOf(query) >= 0 ? '' : 'none';
        });
    });
}

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

function escapeHtml(text) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', function() {
    loadOperations();
    setupSearch();
    refreshActiveOps();
    setInterval(refreshActiveOps, 5000);
});
