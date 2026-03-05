/**
 * operations.js - MistHelper Web Portal Operations Controller
 *
 * Handles operation listing, category accordion, execution via SSE,
 * progress bars, and log streaming.
 */

/* global getCsrfToken, connectSSE, formatTimestamp */

let selectedMenuNumber = null;
let currentRunId = null;
let currentSSE = null;

// ---------------------------------------------------------------------------
// Operation Listing
// ---------------------------------------------------------------------------

function loadOperations() {
    fetch('/api/operations/list')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            renderAccordion(data.categories || []);
            document.getElementById('opLoading').style.display = 'none';
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
        html += '<div class="accordion-item">';
        html += '<h2 class="accordion-header">';
        html += '<button class="accordion-button collapsed" type="button" ';
        html += 'data-bs-toggle="collapse" data-bs-target="#' + collapseId + '">';
        html += escapeHtml(cat.name) + ' (' + cat.operations.length + ')';
        html += '</button></h2>';
        html += '<div id="' + collapseId + '" class="accordion-collapse collapse">';
        html += '<div class="accordion-body p-0">';
        html += '<ul class="list-group list-group-flush">';
        cat.operations.forEach(function(op) {
            html += '<li class="list-group-item list-group-item-action op-item" ';
            html += 'data-menu="' + op.menu_number + '" ';
            html += 'onclick="selectOperation(' + op.menu_number + ', this)">';
            html += '<strong class="me-2">' + op.menu_number + '</strong> ';
            html += escapeHtml(op.description);
            html += '</li>';
        });
        html += '</ul></div></div></div>';
    });
    container.insertAdjacentHTML('beforeend', html);
}

// ---------------------------------------------------------------------------
// Operation Selection
// ---------------------------------------------------------------------------

function selectOperation(menuNumber, element) {
    selectedMenuNumber = String(menuNumber);

    // Highlight active item
    document.querySelectorAll('.op-item').forEach(function(el) {
        el.classList.remove('active');
    });
    if (element) {
        element.classList.add('active');
    }

    // Show selected panel
    var panel = document.getElementById('selectedOp');
    panel.style.display = '';
    document.getElementById('selectedOpTitle').textContent = 'Menu ' + menuNumber;
    document.getElementById('selectedOpDesc').textContent = element
        ? element.textContent.trim()
        : '';

    // Load parameters if any
    loadParameters(menuNumber);

    // Enable run button
    document.getElementById('runBtn').disabled = false;
}

function loadParameters(menuNumber) {
    var formDiv = document.getElementById('parameterForm');
    var fieldsDiv = document.getElementById('parameterFields');
    formDiv.style.display = 'none';
    fieldsDiv.innerHTML = '';

    fetch('/api/operations/parameters/' + menuNumber)
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.parameters && data.parameters.length > 0) {
                renderParameterFields(data.parameters, fieldsDiv);
                formDiv.style.display = '';
            }
        })
        .catch(function() {
            // No parameters needed; that is fine
        });
}

function renderParameterFields(params, container) {
    params.forEach(function(param) {
        var div = document.createElement('div');
        div.className = 'mb-2';

        var label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = param.label || param.name;
        div.appendChild(label);

        var input = document.createElement('input');
        input.className = 'form-control form-control-sm';
        input.name = param.name;
        input.placeholder = param.placeholder || '';
        if (param.required) {
            input.required = true;
        }
        div.appendChild(input);
        container.appendChild(div);
    });
}

// ---------------------------------------------------------------------------
// Run Operation
// ---------------------------------------------------------------------------

function runSelectedOperation() {
    if (selectedMenuNumber === null) { return; }

    // Collect parameters
    var params = {};
    var fields = document.querySelectorAll('#parameterFields input');
    fields.forEach(function(field) {
        if (field.value.trim()) {
            params[field.name] = field.value.trim();
        }
    });

    // Disable button
    var btn = document.getElementById('runBtn');
    btn.disabled = true;
    btn.textContent = 'Starting...';

    // Reset execution panel
    resetExecutionPanel();

    var body = { menu_number: selectedMenuNumber };
    if (Object.keys(params).length > 0) {
        body.parameters = params;
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
        startSSEStream(data.run_id);
    })
    .catch(function(err) {
        showError('Failed to start operation: ' + err.message);
        btn.disabled = false;
        btn.textContent = 'Run Operation';
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
    panel.style.display = '';
    document.getElementById('logViewer').innerHTML = '';
    document.getElementById('outputFiles').style.display = 'none';
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
    if (!files || files.length === 0) { return; }

    var panel = document.getElementById('outputFiles');
    var list = document.getElementById('outputFileList');
    panel.style.display = '';

    files.forEach(function(file) {
        var li = document.createElement('li');
        var link = document.createElement('a');
        link.href = '/api/data/download/' + encodeURIComponent(file);
        link.textContent = file;
        link.className = 'text-accent';
        li.appendChild(link);
        list.appendChild(li);
    });
}

function finishRun() {
    currentRunId = null;
    currentSSE = null;
    var btn = document.getElementById('runBtn');
    btn.disabled = false;
    btn.textContent = 'Run Operation';
    refreshActiveOps();
}

// ---------------------------------------------------------------------------
// Active Operations Panel
// ---------------------------------------------------------------------------

function refreshActiveOps() {
    fetch('/api/operations/active')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            var runs = data.active_runs || [];
            var panel = document.getElementById('activeOpsPanel');
            var list = document.getElementById('activeOpsList');

            if (runs.length === 0) {
                panel.style.display = 'none';
                return;
            }

            panel.style.display = '';
            list.innerHTML = '';
            runs.forEach(function(run) {
                var div = document.createElement('div');
                div.className = 'portal-card mb-2 p-2';
                div.innerHTML = '<strong>Menu ' + run.menu_number + '</strong> ' +
                    '<span class="badge bg-primary">Running</span>' +
                    '<br><small class="text-muted">' +
                    escapeHtml(run.run_id || '') + '</small>';
                list.appendChild(div);
            });
        })
        .catch(function() {
            // Silently fail - non-critical
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
});
