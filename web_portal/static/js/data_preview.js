/**
 * data_preview.js - MistHelper Web Portal Data Preview Modal
 *
 * Provides a Bootstrap 5 full-viewport modal overlay for previewing
 * CSV, SQLite, JSON, and LOG files from the Data Browser and
 * Operations results pages.
 */

/* exported DataPreviewModal */

var DataPreviewModal = (function() {
    'use strict';

    var state = {
        currentPath: '',
        currentPage: 1,
        perPage: 50,
        searchQuery: '',
        sortColumn: -1,
        sortDir: 'asc',
        totalPages: 1,
        totalRows: 0,
        columns: [],
        modalInstance: null
    };

    // -----------------------------------------------------------------------
    // Public API
    // -----------------------------------------------------------------------

    function openPreview(filepath) {
        state.currentPath = filepath;
        state.currentPage = 1;
        state.searchQuery = '';
        state.sortColumn = -1;
        state.sortDir = 'asc';

        showModal();
        setModalTitle(filepath);
        clearModalBody();
        showLoading(true);
        detectAndLoad(filepath);
    }

    // -----------------------------------------------------------------------
    // Modal Management
    // -----------------------------------------------------------------------

    function showModal() {
        var el = document.getElementById('dataPreviewModal');
        if (!el) return;
        if (!state.modalInstance) {
            state.modalInstance = new bootstrap.Modal(el, { keyboard: true });
        }
        state.modalInstance.show();
    }

    function hideModal() {
        if (state.modalInstance) state.modalInstance.hide();
    }

    function setModalTitle(title) {
        var el = document.getElementById('dataPreviewModalLabel');
        if (el) el.textContent = 'Preview: ' + title;
    }

    function clearModalBody() {
        setContent('');
        setSearchVisible(false);
        setPaginationVisible(false);
    }

    function setContent(html) {
        var el = document.getElementById('dataPreviewBody');
        if (el) el.innerHTML = html;
    }

    function showLoading(show) {
        var el = document.getElementById('dataPreviewLoading');
        if (el) { if (show) { el.classList.remove('d-none'); } else { el.classList.add('d-none'); } }
    }

    // -----------------------------------------------------------------------
    // File Type Detection
    // -----------------------------------------------------------------------

    function detectAndLoad(filepath) {
        var ext = filepath.split('.').pop().toLowerCase();
        if (ext === 'csv') {
            loadCsvPreview();
        } else if (ext === 'db' || ext === 'sqlite') {
            loadSqliteTableList(filepath);
        } else if (ext === 'json') {
            loadJsonPreview(filepath);
        } else if (ext === 'log') {
            loadLogPreview(filepath);
        } else {
            showLoading(false);
            setContent('<p class="text-muted">Unsupported file type: ' + escapeHtml(ext) + '</p>');
        }
    }

    // -----------------------------------------------------------------------
    // CSV Rendering
    // -----------------------------------------------------------------------

    function loadCsvPreview() {
        setSearchVisible(true);
        var url = buildPreviewUrl(state.currentPath);

        fetch(url)
            .then(function(res) { return res.json(); })
            .then(function(data) {
                showLoading(false);
                if (data.error) { setContent('<p class="text-danger">' + escapeHtml(data.error) + '</p>'); return; }
                renderCsvTable(data);
            })
            .catch(function(err) {
                showLoading(false);
                setContent('<p class="text-danger">Failed to load preview: ' + escapeHtml(err.message) + '</p>');
            });
    }

    function renderCsvTable(data) {
        state.columns = data.columns || [];
        state.totalPages = data.total_pages || 1;
        state.totalRows = data.total_rows || 0;
        state.currentPage = data.page || 1;

        var html = '<table class="table table-sm portal-table" id="modalPreviewTable"><thead><tr>';
        state.columns.forEach(function(col, idx) {
            var sortCls = getSortClass(idx);
            html += '<th class="' + sortCls + '" data-col="' + idx + '" onclick="DataPreviewModal.sortBy(' + idx + ')">';
            html += escapeHtml(col) + '</th>';
        });
        html += '</tr></thead><tbody>';
        (data.rows || []).forEach(function(row) {
            html += '<tr>';
            row.forEach(function(cell) {
                html += '<td>' + escapeHtml(String(cell !== null ? cell : '')) + '</td>';
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        setContent(html);
        updatePagination();
    }

    function getSortClass(colIdx) {
        if (state.sortColumn !== colIdx) return '';
        return state.sortDir === 'asc' ? 'sort-asc' : 'sort-desc';
    }

    function sortBy(colIdx) {
        if (state.sortColumn === colIdx) {
            state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
            state.sortColumn = colIdx;
            state.sortDir = 'asc';
        }
        state.currentPage = 1;
        showLoading(true);
        loadCsvPreview();
    }

    // -----------------------------------------------------------------------
    // SQLite Rendering
    // -----------------------------------------------------------------------

    function loadSqliteTableList(dbPath) {
        fetch('/api/data/preview/' + encodeURIComponent(dbPath))
            .then(function(res) { return res.json(); })
            .then(function(data) {
                showLoading(false);
                if (data.error) { setContent('<p class="text-danger">' + escapeHtml(data.error) + '</p>'); return; }
                renderSqliteList(data.tables || [], dbPath);
            })
            .catch(function(err) {
                showLoading(false);
                setContent('<p class="text-danger">Failed: ' + escapeHtml(err.message) + '</p>');
            });
    }

    function renderSqliteList(tables, dbPath) {
        var html = '<table class="table table-sm portal-table"><thead><tr>';
        html += '<th>Table</th><th>Rows</th><th>Columns</th><th>Actions</th>';
        html += '</tr></thead><tbody>';
        tables.forEach(function(t) {
            html += '<tr><td>' + escapeHtml(t.table_name) + '</td>';
            html += '<td>' + t.row_count + '</td>';
            html += '<td>' + t.column_names.length + '</td>';
            html += '<td><button class="btn btn-sm btn-outline-primary" ';
            html += 'onclick="DataPreviewModal.openSqliteTable(\'' + escapeJs(dbPath) + "','";
            html += escapeJs(t.table_name) + '\')">View</button></td></tr>';
        });
        html += '</tbody></table>';
        setContent(html);
    }

    function openSqliteTable(dbPath, tableName) {
        state.currentPath = dbPath + '/' + tableName;
        state.currentPage = 1;
        state.searchQuery = '';
        state.sortColumn = -1;
        state.sortDir = 'asc';

        setModalTitle(dbPath + ' > ' + tableName);
        setContent('');
        showLoading(true);
        setSearchVisible(true);

        var url = '/api/data/preview/' + encodeURIComponent(dbPath) + '/' +
                  encodeURIComponent(tableName) + '?page=1&per_page=' + state.perPage;
        fetch(url)
            .then(function(res) { return res.json(); })
            .then(function(data) {
                showLoading(false);
                if (data.error) { setContent('<p class="text-danger">' + escapeHtml(data.error) + '</p>'); return; }
                renderCsvTable(data);
            })
            .catch(function(err) {
                showLoading(false);
                setContent('<p class="text-danger">Failed: ' + escapeHtml(err.message) + '</p>');
            });
    }

    // -----------------------------------------------------------------------
    // JSON Rendering
    // -----------------------------------------------------------------------

    function loadJsonPreview(filepath) {
        fetch('/api/data/preview/' + encodeURIComponent(filepath))
            .then(function(res) { return res.json(); })
            .then(function(data) {
                showLoading(false);
                if (data.error) { setContent('<p class="text-danger">' + escapeHtml(data.error) + '</p>'); return; }
                renderJsonContent(data);
            })
            .catch(function(err) {
                showLoading(false);
                setContent('<p class="text-danger">Failed: ' + escapeHtml(err.message) + '</p>');
            });
    }

    function renderJsonContent(data) {
        var raw = data.raw || data.content || JSON.stringify(data, null, 2);
        var html = '<pre class="json-preview">';
        html += escapeHtml(typeof raw === 'string' ? raw : JSON.stringify(raw, null, 2));
        html += '</pre>';
        setContent(html);
    }

    // -----------------------------------------------------------------------
    // LOG Rendering
    // -----------------------------------------------------------------------

    function loadLogPreview(filepath) {
        fetch('/api/data/preview/' + encodeURIComponent(filepath))
            .then(function(res) { return res.json(); })
            .then(function(data) {
                showLoading(false);
                if (data.error) { setContent('<p class="text-danger">' + escapeHtml(data.error) + '</p>'); return; }
                renderLogContent(data);
            })
            .catch(function(err) {
                showLoading(false);
                setContent('<p class="text-danger">Failed: ' + escapeHtml(err.message) + '</p>');
            });
    }

    function renderLogContent(data) {
        var content = '';
        if (data.rows) {
            data.rows.forEach(function(row) { content += row.join(' ') + '\n'; });
        } else if (data.raw || data.content) {
            content = data.raw || data.content;
        }
        var html = '<pre class="log-preview">';
        html += escapeHtml(content);
        html += '</pre>';
        setContent(html);
    }

    // -----------------------------------------------------------------------
    // Search
    // -----------------------------------------------------------------------

    function onSearch() {
        var input = document.getElementById('dataPreviewSearch');
        state.searchQuery = input ? input.value : '';
        state.currentPage = 1;
        showLoading(true);
        loadCsvPreview();
    }

    function setSearchVisible(visible) {
        var el = document.getElementById('dataPreviewSearchRow');
        if (el) { if (visible) { el.classList.remove('d-none'); } else { el.classList.add('d-none'); } }
    }

    // -----------------------------------------------------------------------
    // Pagination
    // -----------------------------------------------------------------------

    function buildPreviewUrl(path) {
        var url = '/api/data/preview/' + encodeURIComponent(path) +
                  '?page=' + state.currentPage + '&per_page=' + state.perPage;
        if (state.searchQuery) url += '&search=' + encodeURIComponent(state.searchQuery);
        return url;
    }

    function updatePagination() {
        var show = state.totalPages > 1;
        setPaginationVisible(show);
        if (!show) return;

        var info = document.getElementById('dataPreviewPageInfo');
        var prev = document.getElementById('dataPreviewPrev');
        var next = document.getElementById('dataPreviewNext');

        if (info) info.textContent = 'Page ' + state.currentPage + ' of ' + state.totalPages + ' (' + state.totalRows + ' rows)';
        if (prev) prev.disabled = (state.currentPage <= 1);
        if (next) next.disabled = (state.currentPage >= state.totalPages);
    }

    function setPaginationVisible(visible) {
        var el = document.getElementById('dataPreviewPagination');
        if (el) { if (visible) { el.classList.remove('d-none'); } else { el.classList.add('d-none'); } }
    }

    function changePage(delta) {
        state.currentPage += delta;
        showLoading(true);
        loadCsvPreview();
    }

    // -----------------------------------------------------------------------
    // Export
    // -----------------------------------------------------------------------

    function exportCsv() {
        var table = document.getElementById('modalPreviewTable');
        if (!table) return;
        exportTableToBlob(table, 'preview_export.csv');
    }

    function exportTableToBlob(table, filename) {
        var csv = [];
        var rows = table.querySelectorAll('tr');
        rows.forEach(function(row) {
            var cols = row.querySelectorAll('th, td');
            var line = [];
            cols.forEach(function(col) {
                var text = col.textContent.replace(/"/g, '""');
                line.push('"' + text + '"');
            });
            csv.push(line.join(','));
        });

        var blob = new Blob([csv.join('\n')], { type: 'text/csv' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    // -----------------------------------------------------------------------
    // Keyboard & Cleanup
    // -----------------------------------------------------------------------

    function initKeyboard() {
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                hideModal();
            }
        });
    }

    // -----------------------------------------------------------------------
    // Utility
    // -----------------------------------------------------------------------

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function escapeJs(str) {
        return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    }

    // -----------------------------------------------------------------------
    // Init
    // -----------------------------------------------------------------------

    document.addEventListener('DOMContentLoaded', function() {
        initKeyboard();

        var searchInput = document.getElementById('dataPreviewSearch');
        if (searchInput) {
            var timer;
            searchInput.addEventListener('input', function() {
                clearTimeout(timer);
                timer = setTimeout(onSearch, 400);
            });
        }
    });

    // -----------------------------------------------------------------------
    // Public Interface
    // -----------------------------------------------------------------------

    return {
        open: openPreview,
        openPreview: openPreview,
        openSqliteTable: openSqliteTable,
        sortBy: sortBy,
        changePage: changePage,
        exportCsv: exportCsv,
        hide: hideModal
    };

})();
