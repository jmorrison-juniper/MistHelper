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

/* ========== Theme Switcher ========== */

var THEME_STORAGE_KEY = 'misthelper-theme';

function getDefaultTheme() {
    var script = document.querySelector('script[data-default-theme]');
    return script ? script.getAttribute('data-default-theme') : 'dark';
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
    if (themeName === 'light') {
        html.setAttribute('data-bs-theme', 'light');
    } else {
        html.setAttribute('data-bs-theme', 'dark');
    }
    localStorage.setItem(THEME_STORAGE_KEY, themeName);
}

function loadThemeMenu() {
    fetch('/api/themes')
        .then(function(res) { return res.json(); })
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
            });
            th.classList.add(asc ? 'sort-asc' : 'sort-desc');
            rows.sort(function(a, b) {
                var aVal = a.cells[colIndex].textContent.trim();
                var bVal = b.cells[colIndex].textContent.trim();
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
