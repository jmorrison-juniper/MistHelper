/* Settings workflows share the operation workspace, never the generic operation runner. */
(function () {
    'use strict';
    const element = id => document.getElementById(id);
    const visible = (id, shown) => element(id).classList.toggle('d-none', !shown);
    const labels = {ap: 'Access points', switch: 'Switches', ssr: 'SSR routers and gateways', juniper_srx: 'SRX gateways and firewalls'};
    const human = value => String(value).replaceAll('_', ' ').replace(/^\w/, letter => letter.toUpperCase());

    async function request(url, body, jobStatus = false) {
        const response = await fetch(url, body === undefined ? {} : {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
            body: JSON.stringify(body)
        });
        const data = await readJsonAnswer(response);
        if (!response.ok || (data.error && !jobStatus)) {
            const error = new Error(data.error || 'The settings request failed.');
            error.status = response.status;
            throw error;
        }
        return data;
    }

    function option(select, value, text) {
        const item = document.createElement('option');
        item.value = value;
        item.textContent = text;
        select.appendChild(item);
        return item;
    }

    function control(parent, id, labelText, values) {
        const label = document.createElement('label');
        label.htmlFor = id;
        label.className = 'form-label mt-2';
        label.textContent = labelText;
        const select = document.createElement('select');
        select.id = id;
        select.className = 'form-select mb-2';
        select.dataset.testid = id;
        option(select, '', 'Select a value');
        values.forEach(value => option(select, value, value));
        parent.append(label, select);
        return select;
    }

    class ScopeTable {
        constructor(prefix) {
            this.root = element(prefix + 'Rows');
            this.page = 0;
            this.rows = [];
        }

        update(rows) {
            this.rows = [...rows].sort((left, right) =>
                (left.name || left.id).localeCompare(right.name || right.id, undefined, {numeric: true, sensitivity: 'base'}));
            this.render();
        }

        render() {
            this.root.replaceChildren();
            if (!this.rows.length) return;
            const wrap = document.createElement('div');
            wrap.className = 'table-responsive';
            const table = document.createElement('table');
            table.className = 'table table-sm portal-table';
            table.dataset.testid = this.root.id + '-table';
            const head = table.createTHead().insertRow();
            ['Organization / site', 'Scope', 'Backup', 'Settings'].forEach(text => {
                const cell = document.createElement('th');
                cell.scope = 'col';
                cell.textContent = text;
                head.appendChild(cell);
            });
            const body = table.createTBody();
            this.page = Math.min(this.page, Math.floor((this.rows.length - 1) / 50));
            this.rows.slice(this.page * 50, (this.page + 1) * 50).forEach(row => {
                const line = body.insertRow();
                [row.name || row.id, row.scope === 'org' ? 'Organization' : 'Site',
                    human(row.backup || row.backup_status || 'Pending'), human(row.status || 'Not changed')].forEach(text => {
                    line.insertCell().textContent = String(text);
                });
                line.cells[0].title = row.id;
            });
            wrap.appendChild(table);
            this.root.appendChild(wrap);
            const navigation = document.createElement('div');
            navigation.className = 'd-flex justify-content-between align-items-center gap-2';
            const previous = this.button('Previous', -1);
            previous.disabled = this.page === 0;
            const summary = document.createElement('span');
            summary.className = 'small text-muted';
            summary.textContent = `${this.rows.length} scopes. Page ${this.page + 1} of ${Math.ceil(this.rows.length / 50)}.`;
            const next = this.button('Next', 1);
            next.disabled = (this.page + 1) * 50 >= this.rows.length;
            navigation.append(previous, summary, next);
            this.root.appendChild(navigation);
        }

        button(label, change) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-sm btn-outline-secondary';
            button.textContent = label;
            button.dataset.testid = this.root.id + '-' + label.toLowerCase();
            button.addEventListener('click', () => { this.page += change; this.render(); });
            return button;
        }
    }

    class SettingsJob {
        constructor(prefix, endpoint, confirmation) {
            this.prefix = prefix;
            this.endpoint = endpoint;
            this.confirmation = confirmation;
            this.token = null;
            this.busy = false;
            this.table = new ScopeTable(prefix);
            element(prefix + 'Confirmation').addEventListener('input', () => this.controls());
            element(prefix + 'Apply').addEventListener('click', () => this.apply());
        }

        message(text, failed = false) {
            element(this.prefix + 'Message').textContent = text;
            element(this.prefix + 'Message').className = 'alert ' + (failed ? 'alert-danger' : 'alert-info');
        }

        controls() {
            element(this.prefix + 'Controls').disabled = this.busy;
            element(this.prefix + 'Confirmation').disabled = this.busy || !this.token;
            element(this.prefix + 'Apply').disabled = this.busy || !this.token ||
                element(this.prefix + 'Confirmation').value !== this.confirmation;
            visible(this.prefix + 'ConfirmPanel', !this.busy && !!this.token);
            if (this.prefix === 'restore') element('restoreCancel').disabled = this.busy || !this.token;
        }

        invalidate() {
            this.token = null;
            sessionStorage.removeItem(this.prefix + '-settings-job');
            element(this.prefix + 'Confirmation').value = '';
            element(this.prefix === 'policy' ? 'policyPlan' : 'restorePreviewText').replaceChildren();
            this.table.update([]);
            const progress = element(this.prefix + 'Progress');
            progress.style.width = '0%';
            progress.setAttribute('aria-valuenow', '0');
            progress.removeAttribute('aria-valuetext');
            progress.classList.remove('progress-bar-striped', 'progress-bar-animated');
            progress.textContent = '0%';
            this.message('Selection changed. Prepare backups again.');
            this.controls();
        }

        async prepare(body) {
            if (this.busy) return;
            this.invalidate();
            element(this.prefix + 'Result').textContent = '';
            this.table.update([]);
            await this.start(this.endpoint + '/preview', body);
        }

        async apply() {
            if (this.busy || !this.token || element(this.prefix + 'Confirmation').value !== this.confirmation) return;
            const token = this.token;
            const identifier = sessionStorage.getItem(this.prefix + '-settings-job');
            this.invalidate();
            if (identifier) sessionStorage.setItem(this.prefix + '-settings-job', identifier);
            await this.start(this.endpoint + '/apply', {token, confirmation: this.confirmation});
        }

        async start(url, body) {
            this.busy = true;
            this.controls();
            this.message('The server is preparing this operation. No automatic settings retry is permitted.');
            try {
                const data = await request(url, body);
                if (!data.job_id) throw new Error('The server did not return an operation reference.');
                sessionStorage.setItem(this.prefix + '-settings-job', data.job_id);
                await this.poll(data.job_id);
            } catch (error) {
                this.busy = false;
                this.message(error.message + ' Check the operation status before another attempt.', true);
                this.controls();
            }
        }

        async resume() {
            const identifier = sessionStorage.getItem(this.prefix + '-settings-job');
            if (!identifier) return;
            this.busy = true;
            this.controls();
            await this.poll(identifier);
        }

        async poll(identifier) {
            try {
                const data = await request('/api/firmware-policy/jobs/' + encodeURIComponent(identifier), undefined, true);
                const state = data.state || data.status;
                const progress = data.progress || {};
                const completed = Number(progress.completed || 0);
                const total = Number(progress.total || 0);
                const percentage = total ? Math.min(100, Math.round(100 * completed / total)) : 0;
                const active = ['queued', 'preparing', 'applying', 'running'].includes(state);
                const indeterminate = active && !total;
                const bar = element(this.prefix + 'Progress');
                bar.style.width = indeterminate ? '100%' : percentage + '%';
                bar.textContent = indeterminate ? 'Working' : percentage + '%';
                bar.classList.toggle('progress-bar-striped', indeterminate);
                bar.classList.toggle('progress-bar-animated', indeterminate);
                bar.setAttribute('aria-valuetext', indeterminate ?
                    'Working. The target count is not available yet.' : `${completed} of ${total}.`);
                if (indeterminate) bar.removeAttribute('aria-valuenow');
                else bar.setAttribute('aria-valuenow', String(percentage));
                const wait = Number(progress.wait_seconds || 0);
                this.message((progress.message || human(progress.phase || state)) +
                    (total ? `: ${completed} of ${total}.` : '') +
                    (wait ? ` Request allowance wait: about ${Math.ceil(wait)} seconds.` : ''));
                if (data.rows) this.table.update(data.rows);
                if (active) {
                    window.setTimeout(() => this.poll(identifier), 1500);
                    return;
                }
                this.busy = false;
                if (state === 'ready') {
                    this.token = data.token;
                    this.message('All backups verified. Examine the sorted scope table, then type ' + this.confirmation + '.');
                    const summary = element(this.prefix === 'policy' ? 'policyPlan' : 'restorePreviewText');
                    summary.textContent = `${data.rows ? data.rows.length : total} complete target backups verified. No settings changed.`;
                    if (this.prefix === 'policy') this.policySummary(summary, data.organizations || []);
                    else this.restoreSummary(summary, data);
                } else {
                    sessionStorage.removeItem(this.prefix + '-settings-job');
                    const failed = state !== 'complete';
                    const preparationFailed = state === 'failed' && data.failure_stage === 'preparation';
                    const result = data.result || {};
                    const failures = result.failures || result.failed || [];
                    const remaining = result.remaining || [];
                    element(this.prefix + 'Result').textContent = failed ?
                        `${failures.length} failed targets. ${remaining.length} remaining targets. ${data.error || result.error || 'Examine the scope table. Saved changes can remain.'}` :
                        'Settings change complete. All changed settings passed readback verification.';
                    if (preparationFailed) {
                        element(this.prefix + 'Result').textContent = '';
                        this.message('Preparation failed: ' + data.error + ' No settings changed.', true);
                    } else {
                        this.message(failed ? ((data.error || 'The operation stopped with ' + state + ' status.') +
                            ' Saved changes can remain. No settings request will be repeated.') :
                            'Settings change complete. All backups and changed settings verified.', failed);
                    }
                }

                this.controls();
            } catch (error) {
                this.message('Status could not be read: ' + error.message + ' No settings request will be repeated.', true);
                if (error.status && error.status < 500) {
                    this.busy = false;
                    sessionStorage.removeItem(this.prefix + '-settings-job');
                    this.controls();
                } else {
                    window.setTimeout(() => this.poll(identifier), 5000);
                }
            }

        }

        restoreSummary(parent, data) {
            const scope = document.createElement('p');
            scope.className = 'small mt-2';
            scope.dataset.testid = 'restore-policy-scope';
            scope.textContent = data.warning || 'Only AP, switch, SSR, and SRX firmware policies restore. Unrelated current settings remain unchanged.';
            parent.appendChild(scope);
        }

        policySummary(parent, organizations) {
            organizations.forEach(organization => {
                const heading = document.createElement('p');
                heading.className = 'fw-semibold mt-2 mb-1';
                heading.textContent = organization.name + ' (' + organization.id + ')';
                parent.appendChild(heading);
                Object.entries(organization.policies || {}).forEach(([kind, policy]) => {
                    const line = document.createElement('p');
                    line.className = 'small mb-1';
                    const name = kind === 'auto_upgrade' ? 'Access points' : labels[kind];
                    const versions = Object.entries(policy.custom_versions || {}).map(([model, version]) => model + ': ' + version).join(', ');
                    const schedule = kind === 'auto_upgrade' ? `. Day: ${policy.day_of_week}. Time: ${policy.time_of_day}` : '';
                    line.textContent = `${name}: ${policy.enabled ? 'Enabled' : 'Disabled'}. ${versions}${schedule}`;
                    parent.appendChild(line);
                });
            });
        }
    }

    const policy = new SettingsJob('policy', '/api/firmware-policy', 'CONFIGURE');
    const restore = new SettingsJob('restore', '/api/settings-restore', 'RESTORE');
    let catalogs = null;
    let generation = 0;
    let policyInitialized = false;
    let restoreInitialized = false;
    let bundles = [];

    function resetCatalog() {
        generation += 1;
        catalogs = null;
        policy.invalidate();
        element('policyModels').textContent = 'Load available model versions for the selected scope.';
        element('policyPlan').textContent = '';
        element('policyPreview').disabled = true;
    }

    async function organizations() {
        resetCatalog();
        const current = generation;
        element('policyOrganizations').replaceChildren();
        try {
            const msp = element('policyMsp').value;
            const data = await request('/api/firmware-policy/organizations' + (msp ? '?msp_id=' + encodeURIComponent(msp) : ''));
            if (current !== generation) return;
            data.organizations.forEach(org => {
                option(element('policyOrganizations'), org.id, org.name + ' (' + org.id + ')').selected = data.organizations.length === 1;
            });
            policy.message(data.count + ' organization choices loaded.');
        } catch (error) {
            policy.message(error.message, true);
        }
    }

    function scope() {
        return {
            organizations: Array.from(element('policyOrganizations').selectedOptions, item => item.value),
            kinds: Array.from(document.querySelectorAll('[data-policy-kind]:checked'), item => item.value)
        };
    }

    function drawModels() {
        element('policyModels').replaceChildren();
        Object.entries(catalogs).forEach(([kind, models]) => {
            const group = document.createElement('fieldset');
            group.className = 'mb-4';
            group.dataset.kind = kind;
            const legend = document.createElement('legend');
            legend.className = 'fs-6';
            legend.textContent = labels[kind];
            group.appendChild(legend);
            control(group, 'policy-enabled-' + kind, 'Automatic policy state', ['ENABLE', 'DISABLE']);
            const modelList = document.createElement('div');
            modelList.className = 'overflow-auto pe-2';
            modelList.style.maxHeight = '18rem';
            modelList.dataset.testid = 'policy-model-list-' + kind;
            modelList.setAttribute('aria-label', labels[kind] + ' models');
            modelList.tabIndex = 0;
            Object.entries(models).forEach(([model, versions], index) => {
                const row = document.createElement('div');
                row.className = 'mb-2';
                row.dataset.model = model;
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'form-check-input me-2';
                checkbox.id = 'policy-model-' + kind + '-' + index;
                checkbox.dataset.testid = checkbox.id;
                const label = document.createElement('label');
                label.htmlFor = checkbox.id;
                label.textContent = model;
                const versionBox = document.createElement('div');
                versionBox.hidden = true;
                const sorted = [...versions].sort((left, right) => right.localeCompare(left, undefined, {numeric: true}));
                const select = control(versionBox, 'policy-version-' + kind + '-' + index, 'Version for ' + model, sorted);
                select.disabled = true;
                checkbox.addEventListener('change', () => {
                    versionBox.hidden = !checkbox.checked;
                    select.disabled = !checkbox.checked;
                });
                row.append(checkbox, label, versionBox);
                modelList.appendChild(row);
            });
            group.appendChild(modelList);
            if (kind === 'ap') {
                control(group, 'policy-day', 'AP upgrade day (any means every day)', ['any', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']).value = 'any';
                const label = document.createElement('label');
                label.htmlFor = 'policy-time';
                label.className = 'form-label';
                label.textContent = "AP time: HH:MM or any, in each site's time zone";
                const time = document.createElement('input');
                time.id = 'policy-time';
                time.className = 'form-control';
                time.dataset.testid = 'policy-time';
                time.value = '02:00';
                group.append(label, time);
            }
            element('policyModels').appendChild(group);
        });
        element('policyPreview').disabled = false;
    }

    function selectedPolicies() {
        return Array.from(element('policyModels').querySelectorAll('fieldset'), group => {
            const kind = group.dataset.kind;
            const state = element('policy-enabled-' + kind).value;
            if (!state) throw new Error('Select ENABLE or DISABLE for ' + labels[kind] + '.');
            const models = {};
            group.querySelectorAll('[data-model]').forEach(row => {
                if (!row.querySelector('input').checked) return;
                const version = row.querySelector('select').value;
                if (!version) throw new Error('Select a version for ' + row.dataset.model + '.');
                models[row.dataset.model] = version;
            });
            if (!Object.keys(models).length) throw new Error('Select at least one model for ' + labels[kind] + '.');
            const chosen = {kind, enabled: state === 'ENABLE', models};
            if (kind === 'ap') {
                chosen.day = element('policy-day').value;
                chosen.time = element('policy-time').value.trim();
            }
            return chosen;
        });
    }

    element('policyLoad').addEventListener('click', async () => {
        if (policy.busy) return;
        resetCatalog();
        const current = generation;
        const chosen = scope();
        if (!chosen.organizations.length || !chosen.kinds.length) {
            policy.message('Select at least one organization and one device type.', true);
            return;
        }
        element('policyLoad').disabled = true;
        policy.message('Reading shared model versions...');
        try {
            const data = await request('/api/firmware-policy/catalog', chosen);
            if (current !== generation) return;
            catalogs = data.catalogs;
            drawModels();
            policy.message('Select model versions and an explicit policy state, then prepare verified backups.');
        } catch (error) {
            policy.message(error.message, true);
        } finally {
            element('policyLoad').disabled = false;
        }
    });
    element('policyPreview').addEventListener('click', async () => {
        try {
            await policy.prepare({organizations: scope().organizations, policies: selectedPolicies()});
        } catch (error) {
            policy.message(error.message, true);
        }
    });
    element('policyMsp').addEventListener('change', organizations);
    element('policyOrganizations').addEventListener('change', resetCatalog);
    document.querySelectorAll('[data-policy-kind]').forEach(input => input.addEventListener('change', resetCatalog));
    ['change', 'input'].forEach(event => element('policyModels').addEventListener(event, () => policy.invalidate()));

    async function loadBundles() {
        try {
            const data = await request('/api/settings-restore/bundles');
            bundles = data.bundles;
            element('activeCloud').textContent = data.cloud;
            element('restoreBundle').replaceChildren();
            option(element('restoreBundle'), '', 'Select a backup');
            bundles.forEach(bundle => option(element('restoreBundle'), bundle.token,
                `${bundle.created_at} | ${bundle.record_count} complete records`));
            restore.message(bundles.length ? 'Select the backup and saved records.' : 'No verified private backup is available.');
        } catch (error) {
            restore.message(error.message, true);
        }
    }

    element('restoreBundle').addEventListener('change', () => {
        restore.invalidate();
        element('restoreAll').checked = false;
        const records = element('restoreRecords');
        records.replaceChildren();
        const bundle = bundles.find(item => item.token === element('restoreBundle').value);
        (bundle ? bundle.records : []).forEach(record => {
            const label = document.createElement('label');
            label.className = 'd-block mb-1';
            const input = document.createElement('input');
            input.type = 'checkbox';
            input.className = 'form-check-input me-2';
            input.value = record.scope + ':' + record.id;
            input.dataset.testid = 'restore-record-' + record.scope + '-' + record.id;
            input.addEventListener('change', () => restore.invalidate());
            label.append(input, document.createTextNode((record.name || (record.scope === 'org' ? 'Organization' : 'Site')) + ' (' + record.id + ')'));
            records.appendChild(label);
        });
    });
    element('restoreAll').addEventListener('change', () => {
        element('restoreRecords').querySelectorAll('input').forEach(input => { input.checked = element('restoreAll').checked; });
        restore.invalidate();
    });
    element('restoreCloud').addEventListener('input', () => restore.invalidate());
    element('restoreRefresh').addEventListener('click', async () => { restore.invalidate(); await loadBundles(); });
    element('restorePreview').addEventListener('click', () => restore.prepare({
        bundle: element('restoreBundle').value,
        records: Array.from(element('restoreRecords').querySelectorAll('input:checked'), input => input.value),
        cloud: element('restoreCloud').value
    }));
    element('restoreCancel').addEventListener('click', async () => {
        try {
            await request('/api/settings-restore/cancel', {token: restore.token});
            restore.invalidate();
            sessionStorage.removeItem('restore-settings-job');
            restore.message('Restoration cancelled. No settings writes.');
        } catch (error) {
            restore.message(error.message, true);
        }
    });

    window.FirmwareWorkspace = {
        select: async menu => {
            if (menu === '305' && !policyInitialized) {
                policyInitialized = true;
                const pending = sessionStorage.getItem('policy-settings-job');
                await organizations();
                try {
                    const data = await request('/api/operations/msps');
                    (data.msps || []).forEach(msp => option(element('policyMsp'), msp.id || msp.msp_id, msp.name || msp.msp_name));
                } catch (error) {
                    policy.message('MSP choices could not be read: ' + error.message, true);
                }
                if (pending) {
                    sessionStorage.setItem('policy-settings-job', pending);
                    await policy.resume();
                }
            }
            if (menu === '306' && !restoreInitialized) {
                restoreInitialized = true;
                await loadBundles();
                await restore.resume();
            }
        }
    };
}());
