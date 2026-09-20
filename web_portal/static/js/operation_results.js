/**
 * operation_results.js - the results table of one finished operation.
 *
 * Why:
 *     An operation used to report its result as a log. A log cannot be sorted,
 *     it cannot be filtered, and a row cannot be opened. The rogue DHCP scan of
 *     menu 269 writes 20 columns for each finding, and a log line cannot carry
 *     that. Issue #3048 records the gap.
 *
 *     This module renders the rows of the file that a run produced, directly on
 *     the operations page, with no extra click.
 *
 * Server work:
 *     The paging, the filter, and the order all run on the server through
 *     `/api/data/preview`. The browser therefore holds one page at a time, and
 *     a file with 10,000 rows cannot freeze the tab.
 */

/* global escapeHtml */

var OperationResults = (function() {
    'use strict';

    var PER_PAGE = 25;  // One screen of rows. The server caps the page size as well.
    var SEARCH_DELAY_MS = 300;  // Wait for a pause in typing before asking the server.

    var state = {
        files: [],        // Every file that the run produced.
        path: null,       // The file the table shows now.
        columns: [],
        page: 1,
        totalPages: 1,
        totalRows: 0,
        search: '',
        sortColumn: -1,   // -1 keeps the file order, which is the order the scan produced.
        sortDir: 'asc',
        openRow: -1,      // The row index that shows its detail, or -1 for none.
        rows: [],
        searchTimer: null
    };

    // -----------------------------------------------------------------------
    // Visibility
    // -----------------------------------------------------------------------

    function show(id, visible) {
        var el = document.getElementById(id);
        if (!el) return;
        // The panels carry the Bootstrap class `d-none`, which holds
        // `display: none !important`. Only the class can hide or reveal them.
        // Issue #3030 records the defect that an inline style caused.
        if (visible) { el.classList.remove('d-none'); } else { el.classList.add('d-none'); }
    }

    function isPreviewable(name) {
        return /\.(csv|json)$/i.test(name || '');  // The preview endpoint reads these two as a table.
    }

    // -----------------------------------------------------------------------
    // Entry point
    // -----------------------------------------------------------------------

    /**
     * Show the results of one finished run.
     *
     * @param {string[]} files The output files that the run reported.
     */
    function showForRun(files) {
        var tabular = (files || []).filter(isPreviewable);  // A log file belongs in the log panel.
        state.files = tabular;
        if (tabular.length === 0) {  // A run with no table has no result to show here.
            show('resultsPanel', false);
            return;
        }
        buildFileSelect(tabular);
        selectFile(tabular[0]);  // Open the first table at once, so no extra click is needed.
    }

    function buildFileSelect(files) {
        var select = document.getElementById('resultsFileSelect');
        select.innerHTML = files.map(function(name) {
            return '<option value="' + escapeHtml(name) + '">' + escapeHtml(name) + '</option>';
        }).join('');
        show('resultsFileSelect', files.length > 1);  // One file needs no chooser.
    }

    /**
     * Load one result file into the table.
     *
     * @param {string} path The file to show.
     */
    function selectFile(path) {
        state.path = path;
        state.page = 1;
        state.search = '';
        state.sortColumn = -1;
        state.sortDir = 'asc';
        state.openRow = -1;
        var search = document.getElementById('resultsSearch');
        if (search) search.value = '';
        show('resultsPanel', true);
        load();
    }

    // -----------------------------------------------------------------------
    // Loading
    // -----------------------------------------------------------------------

    function buildUrl() {
        var url = '/api/data/preview/' + encodeURIComponent(state.path) +
                  '?page=' + state.page + '&per_page=' + PER_PAGE;
        if (state.search) url += '&search=' + encodeURIComponent(state.search);
        if (state.sortColumn >= 0) {  // The server orders every row, not only this page.
            url += '&sort_column=' + state.sortColumn + '&sort_dir=' + state.sortDir;
        }
        return url;
    }

    function load() {
        setSummary('Loading the results...');
        fetch(buildUrl())
            .then(readJsonAnswer)
            .then(function(data) {
                if (data.error) { renderError(data.error); return; }
                render(data);
            })
            .catch(function(err) { renderError(err.message); });
    }

    function renderError(message) {
        document.getElementById('resultsHead').innerHTML = '';
        document.getElementById('resultsBody').innerHTML = '';
        setSummary('');
        show('resultsPagination', false);
        document.getElementById('resultsBody').innerHTML =
            '<tr><td class="text-danger">Could not read the results: ' + escapeHtml(message) + '</td></tr>';
    }

    function setSummary(text) {
        document.getElementById('resultsSummary').textContent = text;
    }

    // -----------------------------------------------------------------------
    // Rendering
    // -----------------------------------------------------------------------

    function render(data) {
        state.columns = data.columns || [];
        state.rows = data.rows || [];
        state.totalRows = data.total_rows || 0;
        state.totalPages = data.total_pages || 1;
        state.page = data.page || 1;
        state.openRow = -1;  // A new page closes any open detail, so no stale row stays open.

        if (state.totalRows === 0) {  // An empty result must read as an answer, not as a fault.
            document.getElementById('resultsHead').innerHTML = '';
            document.getElementById('resultsBody').innerHTML =
                '<tr><td class="text-muted">No row matches this filter.</td></tr>';
            setSummary('The result holds no row.');
            show('resultsPagination', false);
            renderTruncationNotice(data);
            return;
        }

        renderHead();
        renderBody();
        setSummary(summaryText());
        renderTruncationNotice(data);
        renderPagination();
    }

    function summaryText() {
        var first = (state.page - 1) * PER_PAGE + 1;
        var last = Math.min(first + state.rows.length - 1, state.totalRows);
        var text = 'Showing ' + first + ' to ' + last + ' of ' + state.totalRows + ' rows.';
        if (state.search) text += ' The filter "' + state.search + '" selected them.';
        return text + ' Select a column heading to sort. Select a row to open it.';
    }

    function renderTruncationNotice(data) {
        var visible = Boolean(data.sort_truncated);
        show('resultsTruncated', visible);
        if (!visible) return;
        // Never let a partial order look complete. That silence is the defect
        // that issue #3047 repaired, and it must not return in another form.
        document.getElementById('resultsTruncated').textContent =
            'This file holds more rows than one sort can cover, so the order reads the first ' +
            (data.sort_limit || 0) + ' rows only. Filter the rows to narrow the result.';
    }

    function renderHead() {
        var html = '<tr>';
        state.columns.forEach(function(col, idx) {
            // The arrow comes from the `sort-asc` and `sort-desc` rules in
            // portal.css, which add it with an `::after` rule. A second arrow
            // in this text would render twice, as "country down down".
            var cls = 'sortable';
            if (state.sortColumn === idx) cls += state.sortDir === 'asc' ? ' sort-asc' : ' sort-desc';
            html += '<th class="' + cls + '" style="cursor:pointer" data-col="' + idx + '"' +
                    ' onclick="OperationResults.sortBy(' + idx + ')">' +
                    escapeHtml(col) + '</th>';
        });
        document.getElementById('resultsHead').innerHTML = html + '</tr>';
    }

    function renderBody() {
        var html = '';
        state.rows.forEach(function(row, idx) {
            html += '<tr style="cursor:pointer" data-row="' + idx + '"' +
                    ' onclick="OperationResults.toggleRow(' + idx + ')">';
            row.forEach(function(cell) {
                var text = cellText(cell);
                // The cell truncates with an ellipsis, so the title carries the
                // whole value for a hover. The row detail holds it as well.
                html += '<td title="' + escapeHtml(text) + '">' + escapeHtml(text) + '</td>';
            });
            html += '</tr>';
            if (state.openRow === idx) html += detailRow(row);
        });
        document.getElementById('resultsBody').innerHTML = html;
    }

    function cellText(cell) {
        return String(cell === null || cell === undefined ? '' : cell);
    }

    /**
     * Build the detail row that opens under one result row.
     *
     * A record of 20 columns does not fit across a screen, and a long detail
     * text wraps into an unreadable block. This view names every column and its
     * value, one pair to a line.
     */
    function detailRow(row) {
        // The table can be far wider than the panel, and it scrolls sideways.
        // The detail block is pinned to the left edge, so it must also be no
        // wider than the visible area, or the reader has to scroll to read it.
        var wrap = document.getElementById('resultsTableWrap');
        var visibleWidth = wrap ? wrap.clientWidth : 0;
        var widthStyle = visibleWidth ? ' style="width:' + visibleWidth + 'px"' : '';
        var html = '<tr class="result-detail" data-testid="results-row-detail"><td colspan="' +
                   state.columns.length + '"><div class="result-detail-inner"' + widthStyle +
                   '><dl class="row mb-0 small">';
        state.columns.forEach(function(col, idx) {
            var value = cellText(row[idx]);
            html += '<dt class="col-sm-3 text-muted">' + escapeHtml(col) + '</dt>';
            html += '<dd class="col-sm-9">' + (value ? escapeHtml(value) : '<span class="text-muted">empty</span>') +
                    '</dd>';
        });
        return html + '</dl></div></td></tr>';
    }

    function renderPagination() {
        var many = state.totalPages > 1;
        show('resultsPagination', many);
        if (!many) return;
        document.getElementById('resultsPageInfo').textContent =
            'Page ' + state.page + ' of ' + state.totalPages;
    }

    // -----------------------------------------------------------------------
    // Interaction
    // -----------------------------------------------------------------------

    function sortBy(idx) {
        if (state.sortColumn === idx) {
            state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';  // A second click reverses the order.
        } else {
            state.sortColumn = idx;
            state.sortDir = 'asc';
        }
        state.page = 1;  // A new order starts at the first page, or the view would jump.
        load();
    }

    function toggleRow(idx) {
        state.openRow = state.openRow === idx ? -1 : idx;  // A second click closes the detail.
        renderBody();
    }

    function onSearchInput(value) {
        if (state.searchTimer) clearTimeout(state.searchTimer);  // One request for each pause, not for each key.
        state.searchTimer = setTimeout(function() {
            state.search = value.trim();
            state.page = 1;  // A new filter starts at the first page.
            load();
        }, SEARCH_DELAY_MS);
    }

    function previousPage() {
        if (state.page <= 1) return;
        state.page -= 1;
        load();
    }

    function nextPage() {
        if (state.page >= state.totalPages) return;
        state.page += 1;
        load();
    }

    /** Download the rows that the active filter and order selected. */
    function exportCsv() {
        var url = '/api/data/download/' + encodeURIComponent(state.path);
        window.open(url, '_blank');  // The download route streams the whole file.
    }

    function reset() {
        state.files = [];
        state.path = null;
        state.rows = [];
        state.openRow = -1;
        show('resultsPanel', false);
        show('resultsTruncated', false);
    }

    return {
        showForRun: showForRun,
        selectFile: selectFile,
        sortBy: sortBy,
        toggleRow: toggleRow,
        onSearchInput: onSearchInput,
        previousPage: previousPage,
        nextPage: nextPage,
        exportCsv: exportCsv,
        reset: reset
    };
})();
