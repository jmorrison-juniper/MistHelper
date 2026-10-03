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
        sortTruncated: false,  // Keep the server's sort warning while the current page is visible.
        sortLimit: 0,  // Keep the limit that explains a partial server sort.
        clippedRows: [],  // Hold only rows whose visible cells overflow on the current page.
        renderVersion: 0,  // Reject a scheduled geometry check after data changes.
        clippingFrame: null,  // Allow one pending animation-frame measurement at a time.
        loadVersion: 0,  // Reject preview responses that belong to an older file or page.
        layoutObserver: null,  // Observe the table wrapper without adding repeated listeners.
        resizeHandlerInstalled: false,  // Install the window fallback only once.
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
        if (state.searchTimer) clearTimeout(state.searchTimer);  // Stop a filter timer from changing the new file.
        state.searchTimer = null;  // Keep later filter input independent of an old timer.
        state.path = path;
        state.page = 1;
        state.search = '';
        state.sortColumn = -1;
        state.sortDir = 'asc';
        state.sortTruncated = false;  // A new file must not inherit the old file's sort warning.
        state.sortLimit = 0;  // Reset the old file's sort boundary with its warning.
        state.clippedRows = [];  // A new file starts without the prior file's clipping rows.
        state.openRow = -1;
        invalidateClippingCheck();  // Cancel geometry work that belongs to the previous file.
        renderTruncationNoticeContent();  // Hide any notice that belongs to the previous file.
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
        var loadVersion = state.loadVersion + 1;
        state.loadVersion = loadVersion;  // Give this request ownership of the next rendered result.
        state.sortTruncated = false;  // Do not show a warning from the page being replaced.
        state.sortLimit = 0;  // Clear the old sort limit while the new page loads.
        state.clippedRows = [];  // Do not describe rows from the page being replaced.
        invalidateClippingCheck();  // Cancel any scheduled measurement for the old page.
        renderTruncationNoticeContent();  // Keep the notice tied to the visible result state.
        setSummary('Loading the results...');
        fetch(buildUrl())
            .then(readJsonAnswer)
            .then(function(data) {
                if (loadVersion !== state.loadVersion) return;  // Ignore a response that belongs to an older request.
                if (data.error) { renderError(data.error); return; }
                render(data);
            })
            .catch(function(err) {
                if (loadVersion !== state.loadVersion) return;  // Keep an older failure from replacing current results.
                renderError(err.message);
            });
    }

    function renderError(message) {
        state.sortTruncated = false;  // An error result has no active sort warning.
        state.sortLimit = 0;  // Clear a sort limit that belongs to the failed request.
        state.clippedRows = [];  // An error result has no measurable data rows.
        invalidateClippingCheck();  // Reject geometry callbacks for the failed request.
        renderTruncationNoticeContent();  // Hide notices that no longer describe the result.
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
        state.renderVersion += 1;  // Mark this data render so older frame callbacks cannot publish.
        cancelClippingFrame();  // Stop a queued check before the new rows replace the old rows.
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
        state.sortTruncated = Boolean(data.sort_truncated);  // Preserve the existing server sort warning.
        state.sortLimit = data.sort_limit || 0;  // Retain the exact limit for the existing warning.
        state.clippedRows = [];  // Measure only the rows produced by this render.
        renderTruncationNoticeContent();  // Publish the sort warning before the geometry check runs.
        scheduleClippingCheck();  // Measure rendered cells after the browser completes layout.
    }

    function renderTruncationNoticeContent() {  // Rebuild notices from the current result state.
        var notice = document.getElementById('resultsTruncated');  // Reuse the existing accessible notice region.
        if (!notice) return;  // Keep pages without the results panel safe.
        while (notice.firstChild) notice.removeChild(notice.firstChild);  // Drop old controls to prevent stale handlers.
        var visible = state.sortTruncated || state.clippedRows.length > 0;  // Show either current warning condition.
        show('resultsTruncated', visible);  // Keep Bootstrap visibility as the single display control.
        if (!visible) return;  // Do not leave empty alert text visible.
        notice.setAttribute('role', 'status');  // Announce changes without moving keyboard focus.
        notice.setAttribute('aria-live', 'polite');  // Read the warning when the rendered result changes.
        if (state.sortTruncated) appendSortTruncationWarning(notice);  // Preserve the existing sort message.
        if (state.clippedRows.length === 0) return;  // A sort-only warning keeps its current content.
        appendClippedValueNotice(notice);  // Add row controls only when rendered cells overflow.
    }

    function appendSortTruncationWarning(notice) {  // Keep the existing sort warning in its own text node.
        notice.appendChild(document.createTextNode(
            'This file holds more rows than one sort can cover, so the order reads the first ' +
            state.sortLimit + ' rows only. Filter the rows to narrow the result.'
        ));  // Keep the existing sort warning text unchanged and safe.
    }

    function appendClippedValueNotice(notice) {  // Add full-value paths for the rows that currently clip.
        if (state.sortTruncated) notice.appendChild(document.createElement('br'));  // Separate both warning messages.
        notice.appendChild(document.createTextNode(
            'The table shortens values that do not fit. Open row details to read full values. '
        ));  // Explain the clipping and its existing full-value path.
        state.clippedRows.forEach(function(rowIndex) {  // Build controls only for rows with measured overflow.
            notice.appendChild(createClippedRowControl(rowIndex));  // Add one control for each affected visible row.
        });
        notice.appendChild(document.createTextNode('See '));  // Introduce the complete file location.
        var outputLink = document.createElement('a');  // Use a safe DOM element instead of HTML text.
        outputLink.href = '#outputFiles';  // Point to the existing Output Files panel.
        outputLink.textContent = 'Output Files';  // Keep the link name clear to assistive technology.
        notice.appendChild(outputLink);  // Keep the complete CSV available through the existing file list.
        notice.appendChild(document.createTextNode(' for the complete file.'));  // Finish the notice as readable text.
    }

    function createClippedRowControl(rowIndex) {  // Link one affected row to its existing detail behavior.
        var button = document.createElement('button');  // Use a keyboard-accessible native control.
        var rowNumber = rowIndex + 1;  // Show a one-based row number to match the visible table.
        button.type = 'button';  // Keep the control from submitting any surrounding form.
        button.className = 'btn btn-link btn-sm p-0 me-2';  // Match the existing compact portal controls.
        button.textContent = 'Open details for row ' + rowNumber;  // Set safe, visible control text.
        button.setAttribute('aria-label', 'Open details for row ' + rowNumber);  // Name the action for assistive tools.
        button.setAttribute('aria-controls', 'result-detail-' + rowIndex);  // Link the control to the real detail row.
        button.setAttribute('aria-expanded', String(state.openRow === rowIndex));  // Report the current detail state.
        button.addEventListener('click', function() {  // Bind one action to the current affected row.
            toggleRow(rowIndex);  // Use the existing row-detail transition.
        });
        return button;  // Return one control for the current affected row.
    }

    function ensureLayoutObserver() {  // Install one observer for the result table's visible width.
        var wrap = document.getElementById('resultsTableWrap');  // Observe the box that sets the cell widths.
        if (!wrap) return;  // Avoid setup when the results table is absent.
        if (typeof ResizeObserver !== 'undefined' && !state.layoutObserver) {  // Prefer element-sized layout changes.
            state.layoutObserver = new ResizeObserver(scheduleClippingCheck);  // Track table layout changes once.
            state.layoutObserver.observe(wrap);  // Recheck when the visible table width changes.
        }
        if (!state.resizeHandlerInstalled) {  // Keep a single fallback for browsers without ResizeObserver.
            window.addEventListener('resize', scheduleClippingCheck);  // Cover browsers without ResizeObserver.
            state.resizeHandlerInstalled = true;  // Prevent duplicate global resize handlers.
        }
    }

    function cancelClippingFrame() {  // Release any scheduled measurement before the result changes.
        if (state.clippingFrame === null) return;  // No queued measurement needs cancellation.
        cancelAnimationFrame(state.clippingFrame);  // Stop geometry work for an older result.
        state.clippingFrame = null;  // Allow the current render to schedule one check.
    }

    function invalidateClippingCheck() {  // Invalidate callbacks that belong to another result state.
        state.renderVersion += 1;  // Invalidate callbacks before clearing their pending frame.
        cancelClippingFrame();  // Release the one scheduled geometry measurement.
    }

    function isCurrentRender(renderVersion, path, page) {  // Compare every identity that owns the current rows.
        return renderVersion === state.renderVersion && path === state.path && page === state.page;  // Keep checks bound to one page.
    }

    function measureVisibleClippedRows() {  // Find current visible rows with real cell overflow.
        var clippedRows = [];  // Keep only visible row indexes with actual cell overflow.
        document.querySelectorAll('#resultsBody tr[data-row]').forEach(function(row) {  // Inspect only rendered data rows.
            if (row.getClientRects().length === 0) return;  // Ignore hidden or detached rows.
            var rowIndex = Number(row.getAttribute('data-row'));  // Use the renderer's stable row index.
            if (rowHasClippedCell(row)) clippedRows.push(rowIndex);  // Report a row once even if several cells clip.
        });
        return clippedRows;  // Return measurements from the active page only.
    }

    function rowHasClippedCell(row) {  // Check rendered cell geometry instead of value length.
        return Array.from(row.querySelectorAll('td')).some(function(cell) {  // Test each visible data cell.
            return cell.getClientRects().length > 0 &&
                   cell.clientWidth > 0 &&
                   cell.scrollWidth > cell.clientWidth;  // Detect layout overflow, not string length.
        });
    }

    function scheduleClippingCheck() {  // Coalesce layout updates into one current-page measurement.
        ensureLayoutObserver();  // Watch future layout changes without creating repeated observers.
        cancelClippingFrame();  // Coalesce repeated resize events into the latest measurement.
        var renderVersion = state.renderVersion;  // Bind this callback to the current rendered rows.
        var path = state.path;  // Prevent a file change from publishing old measurements.
        var page = state.page;  // Prevent a page change from publishing old measurements.
        state.clippingFrame = requestAnimationFrame(function() {  // Measure after layout settles.
            state.clippingFrame = null;  // Release the frame slot before measuring.
            if (!isCurrentRender(renderVersion, path, page)) return;  // Ignore a stale callback before DOM reads.
            var clippedRows = measureVisibleClippedRows();  // Measure actual cell geometry after layout.
            if (!isCurrentRender(renderVersion, path, page)) return;  // Do not publish data after a state change.
            state.clippedRows = clippedRows;  // Keep the notice limited to the current visible page.
            renderTruncationNoticeContent();  // Update accessible controls from the completed measurement.
        });
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
            if (state.openRow === idx) html += detailRow(row, idx);  // Give notice controls a stable detail target.
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
    function detailRow(row, rowIndex) {  // Give notice controls the same stable row target.
        // The table can be far wider than the panel, and it scrolls sideways.
        // The detail block is pinned to the left edge, so it must also be no
        // wider than the visible area, or the reader has to scroll to read it.
        var wrap = document.getElementById('resultsTableWrap');
        var visibleWidth = wrap ? wrap.clientWidth : 0;
        var widthStyle = visibleWidth ? ' style="width:' + visibleWidth + 'px"' : '';
        var html = '<tr id="result-detail-' + rowIndex +  // Match the accessible control to this real detail row.
                   '" class="result-detail" data-testid="results-row-detail"><td colspan="' +
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
        scheduleClippingCheck();  // Recheck cells after the detail changes the table layout.
    }

    function onSearchInput(value) {
        if (state.searchTimer) clearTimeout(state.searchTimer);  // One request for each pause, not for each key.
        state.searchTimer = setTimeout(function() {
            state.searchTimer = null;  // Release the timer slot before starting the new filter request.
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
        if (state.searchTimer) clearTimeout(state.searchTimer);  // Stop filtering after the result panel resets.
        state.searchTimer = null;  // Keep later runs independent of this timer.
        state.loadVersion += 1;  // Invalidate a preview response that belongs to the cleared result.
        state.files = [];
        state.path = null;
        state.rows = [];
        state.openRow = -1;
        state.sortTruncated = false;  // A cleared result has no active sort warning.
        state.sortLimit = 0;  // Remove the limit from the cleared result.
        state.clippedRows = [];  // Remove affected rows from the cleared result.
        invalidateClippingCheck();  // Prevent an old result callback from restoring its notice.
        renderTruncationNoticeContent();  // Hide and clear the notice for the cleared result.
        show('resultsPanel', false);
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
