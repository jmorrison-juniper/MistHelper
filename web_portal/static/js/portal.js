/**
 * MistHelper Web Portal - Core JavaScript
 *
 * Theme switcher with localStorage persistence,
 * sortable table utilities, SSE EventSource helper,
 * CSRF token reader, and CSV export functionality.
 */

/* ========== CSRF ========== */

function getCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

/* ========== Safe JSON reading ========== */

// Issue #3087: every caller used to read an answer with `response.json()`.
// A stale CSRF token makes flask-wtf answer with an HTML error page, so the
// parser raised and the operator read:
//
//   Unexpected token '<', "<!doctype "... is not valid JSON
//
// That message names neither the cause nor an action. A proxy page and a
// server error page produce the same useless text. `readJsonAnswer` returns a
// usable object for any answer, so a caller always has a reason to show.

var SESSION_EXPIRED_MESSAGE =
    'Your session expired. Reload the page, then start the operation again.';

function statusReason(response) {
    // Turn one status code into a sentence that states a cause and an action.
    if (response.status === 400 || response.status === 403) return SESSION_EXPIRED_MESSAGE;
    if (response.status === 404) return 'The portal route is missing. Reload the page.';
    if (response.status === 502 || response.status === 503 || response.status === 504) {
        return 'The portal is restarting. Wait a moment, then try again.';
    }
    if (response.status >= 500) return 'The portal failed to answer. Read data/script.log for the cause.';
    return 'The portal answered with status ' + response.status + '.';
}

function readJsonAnswer(response) {
    // Always resolve with an object. A caller then reads `.error` for a reason.
    return response.text().then(function(body) {
        var parsed = null;
        try {
            parsed = body ? JSON.parse(body) : null;
        } catch (err) {
            parsed = null;  // The body was HTML or was empty, which is the reported case.
        }
        if (parsed && typeof parsed === 'object') {
            if (!response.ok && !parsed.error) parsed.error = statusReason(response);
            return parsed;
        }
        return { error: statusReason(response) };  // No JSON body, so name the status instead.
    });
}

/* ========== Theme Switcher ========== */

var THEME_STORAGE_KEY = 'misthelper-theme';

function getDefaultTheme() {
    // base.html carries the server value on the script tag. The literal below
    // answers only a page that omits the attribute, so it names the same
    // default that PortalConfigLoader.ENV_DEFAULTS holds (issue #3136).
    var script = document.querySelector('script[data-default-theme]');
    return script ? script.getAttribute('data-default-theme') : 'magenta';
}

function getSavedTheme() {
    return localStorage.getItem(THEME_STORAGE_KEY) || getDefaultTheme();
}

function applyTheme(themeName) {
    var link = document.getElementById('theme-css');
    if (link) {
        link.href = '/static/css/themes/' + themeName + '.css';
    }
    var html = document.documentElement;
    // Every shipped theme paints a dark page except `light`, so Bootstrap takes
    // its dark control set unless the operator chooses that one theme.
    if (themeName === 'light') {
        html.setAttribute('data-bs-theme', 'light');
    } else {
        html.setAttribute('data-bs-theme', 'dark');
    }
    localStorage.setItem(THEME_STORAGE_KEY, themeName);
}

function loadThemeMenu() {
    fetch('/api/themes')
        .then(readJsonAnswer)
        .then(function(data) {
            var menu = document.getElementById('themeMenu');
            if (!menu) return;
            menu.innerHTML = '';
            var saved = getSavedTheme();
            (data.themes || []).forEach(function(theme) {
                var li = document.createElement('li');
                var btn = document.createElement('button');
                btn.className = 'dropdown-item';
                btn.textContent = theme.display_label;
                if (theme.name === saved) {
                    btn.classList.add('active');
                }
                btn.addEventListener('click', function() {
                    applyTheme(theme.name);
                    menu.querySelectorAll('.dropdown-item')
                        .forEach(function(el) { el.classList.remove('active'); });
                    btn.classList.add('active');
                });
                li.appendChild(btn);
                menu.appendChild(li);
            });
        })
        .catch(function() { /* theme menu load failed silently */ });
}

/* ========== Sortable Tables ========== */

function makeSortable(table) {
    var headers = table.querySelectorAll('th[data-sort]');
    headers.forEach(function(th) {
        th.addEventListener('click', function() {
            var colIndex = th.cellIndex;
            var tbody = table.querySelector('tbody');
            if (!tbody) return;
            var rows = Array.from(tbody.rows);
            var asc = !th.classList.contains('sort-asc');
            headers.forEach(function(h) {
                h.classList.remove('sort-asc', 'sort-desc');
                h.setAttribute('aria-sort', 'none'); // Reset the state so assistive technology sees one active column.
            });
            th.classList.add(asc ? 'sort-asc' : 'sort-desc');
            th.setAttribute('aria-sort', asc ? 'ascending' : 'descending'); // Report the active direction to assistive technology.
            rows.sort(function(a, b) {
                var aCell = a.cells[colIndex]; // Read the cell so numeric sort metadata can override formatted text.
                var bCell = b.cells[colIndex]; // Read the cell so both rows use the same sort rule.
                var aVal = aCell.getAttribute('data-sort-value') || aCell.textContent.trim(); // Prefer stable raw values for formatted cells.
                var bVal = bCell.getAttribute('data-sort-value') || bCell.textContent.trim(); // Prefer stable raw values for formatted cells.
                var aNum = parseFloat(aVal);
                var bNum = parseFloat(bVal);
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return asc ? aNum - bNum : bNum - aNum;
                }
                return asc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            });
            rows.forEach(function(row) { tbody.appendChild(row); });
        });
    });
}

/* ========== SSE Helper ========== */

function connectSSE(runId, handlers) {
    var url = '/api/operations/stream';
    if (runId) url += '?run_id=' + encodeURIComponent(runId);
    var source = new EventSource(url);

    ['status', 'log', 'complete', 'error', 'heartbeat'].forEach(function(eventType) {
        source.addEventListener(eventType, function(event) {
            var data = JSON.parse(event.data);
            if (handlers[eventType]) {
                handlers[eventType](data);
            }
        });
    });

    source.onerror = function() {
        if (handlers.connectionError) {
            handlers.connectionError();
        }
    };

    return source;
}

/* ========== CSV Export ========== */

function exportTableToCSV(tableElement, filename) {
    var rows = [];
    var headerRow = tableElement.querySelector('thead tr');
    if (headerRow) {
        var headers = [];
        headerRow.querySelectorAll('th').forEach(function(th) {
            headers.push(csvEscapeCell(th.textContent.trim()));
        });
        rows.push(headers.join(','));
    }
    tableElement.querySelectorAll('tbody tr').forEach(function(tr) {
        var cells = [];
        tr.querySelectorAll('td').forEach(function(td) {
            cells.push(csvEscapeCell(td.textContent.trim()));
        });
        rows.push(cells.join(','));
    });
    downloadBlob(rows.join('\n'), filename || 'export.csv', 'text/csv');
}

function csvEscapeCell(value) {
    if (value.indexOf(',') >= 0 || value.indexOf('"') >= 0 || value.indexOf('\n') >= 0) {
        return '"' + value.replace(/"/g, '""') + '"';
    }
    return value;
}

function downloadBlob(content, filename, mimeType) {
    var blob = new Blob([content], { type: mimeType });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

/* ========== Utility ========== */

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    var units = ['B', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(1024));
    if (i >= units.length) i = units.length - 1;
    return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i];
}

function formatTimestamp(epoch) {
    if (!epoch) return '';
    var d = new Date(epoch * 1000);
    return d.toLocaleString();
}

/* ========== Initialization ========== */

document.addEventListener('DOMContentLoaded', function() {
    applyTheme(getSavedTheme());
    loadThemeMenu();
    document.querySelectorAll('.portal-table').forEach(makeSortable);
});
