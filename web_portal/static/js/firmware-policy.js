/* Menu 305 uses a dedicated settings workflow, never the generic safe-operation runner. */
(function () {
    'use strict';
    const element = id => document.getElementById(id);
    let generation = 0;
    let token = null;
    let catalogs = null;
    let busy = false;

    function message(text, failed = false) {
        element('policyMessage').textContent = text;
        element('policyMessage').className = 'alert ' + (failed ? 'alert-danger' : 'alert-info');
    }

    async function request(url, body) {
        const options = body === undefined ? {} : {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
            body: JSON.stringify(body)
        };
        const response = await fetch(url, options);
        const data = await readJsonAnswer(response);
        if (data.error) throw new Error(data.error);
        return data;
    }

    function scope() {
        return {
            organizations: Array.from(element('policyOrganizations').selectedOptions).map(option => option.value),
            kinds: Array.from(document.querySelectorAll('[data-policy-kind]:checked')).map(input => input.value)
        };
    }

    function invalidate() {
        generation += 1;
        token = null;
        element('policyPlan').textContent = '';
        element('policyApply').disabled = true;
        element('policyConfirmation').value = '';
    }

    function resetCatalog() {
        invalidate();
        catalogs = null;
        element('policyModels').textContent = 'Load available model versions for the selected scope.';
        element('policyPreview').disabled = true;
    }

    function option(select, value, text) {
        const item = document.createElement('option');
        item.value = value;
        item.textContent = text;
        select.appendChild(item);
        return item;
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
                const item = option(element('policyOrganizations'), org.id, org.name + ' (' + org.id + ')');
                item.selected = data.organizations.length === 1;
            });
            message(data.count + ' organization choices loaded. Select the target organizations and device types.');
        } catch (error) {
            if (current === generation) message(error.message, true);
        }
    }

    function selectControl(parent, id, labelText, values) {
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

    function drawModels() {
        element('policyModels').replaceChildren();
        Object.entries(catalogs).forEach(([kind, models]) => {
            const group = document.createElement('fieldset');
            group.className = 'mb-4';
            group.dataset.kind = kind;
            const legend = document.createElement('legend');
            legend.className = 'fs-6';
            legend.textContent = kind;
            group.appendChild(legend);
            selectControl(group, 'policy-enabled-' + kind, 'Automatic policy enabled state', ['ENABLE', 'DISABLE']);
            Object.entries(models).forEach(([model, versions], index) => {
                const row = document.createElement('div');
                row.className = 'mb-3';
                row.dataset.model = model;
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'form-check-input me-2';
                checkbox.id = 'policy-model-' + kind + '-' + index;
                checkbox.dataset.testid = checkbox.id;
                const label = document.createElement('label');
                label.htmlFor = checkbox.id;
                label.textContent = 'Configure ' + model;
                row.append(checkbox, label);
                const versionsSelect = selectControl(row, 'policy-version-' + kind + '-' + index, 'Version for ' + model, versions);
                versionsSelect.disabled = true;
                checkbox.addEventListener('change', () => { versionsSelect.disabled = !checkbox.checked; });
                group.appendChild(row);
            });
            if (kind === 'ap') {
                selectControl(group, 'policy-day', 'AP upgrade day', ['any', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']);
                const label = document.createElement('label');
                label.htmlFor = 'policy-time';
                label.className = 'form-label';
                label.textContent = "AP upgrade time: HH:MM or any, in each site's time zone";
                const time = document.createElement('input');
                time.id = 'policy-time';
                time.className = 'form-control';
                time.dataset.testid = 'policy-time';
                time.placeholder = '02:00 or any';
                group.append(label, time);
            }
            element('policyModels').appendChild(group);
        });
        element('policyPreview').disabled = false;
    }

    async function loadCatalog() {
        if (busy) return;
        resetCatalog();
        const current = generation;
        const chosen = scope();
        if (!chosen.organizations.length || !chosen.kinds.length) {
            message('Select at least one organization and one device type.', true);
            return;
        }
        message('Reading shared model versions...');
        try {
            const data = await request('/api/firmware-policy/catalog', chosen);
            if (current !== generation) return;
            catalogs = data.catalogs;
            drawModels();
            message('Select model versions and an explicit enabled state. Then preview the complete change.');
        } catch (error) {
            if (current === generation) message(error.message, true);
        }
    }

    function selectedPolicies() {
        return Array.from(element('policyModels').querySelectorAll('fieldset')).map(group => {
            const kind = group.dataset.kind;
            const state = element('policy-enabled-' + kind).value;
            if (!state) throw new Error('Select ENABLE or DISABLE for ' + kind + '.');
            const models = {};
            group.querySelectorAll('[data-model]').forEach(row => {
                if (!row.querySelector('input').checked) return;
                const version = row.querySelector('select').value;
                if (!version) throw new Error('Select a version for ' + row.dataset.model + '.');
                models[row.dataset.model] = version;
            });
            if (!Object.keys(models).length) throw new Error('Select at least one model for ' + kind + '.');
            const policy = {kind, enabled: state === 'ENABLE', models};
            if (kind === 'ap') {
                policy.day = element('policy-day').value;
                policy.time = element('policy-time').value.trim();
                if (!policy.day || !policy.time) throw new Error('Select an AP day and time, or explicitly enter any.');
            }
            return policy;
        });
    }

    async function preview() {
        if (busy || !catalogs) return;
        invalidate();
        const current = generation;
        try {
            const chosen = scope();
            chosen.policies = selectedPolicies();
            message('Reading complete organization and site settings. No settings are changing.');
            const data = await request('/api/firmware-policy/preview', chosen);
            if (current !== generation) return;
            token = data.token;
            element('policyPlan').textContent = JSON.stringify(data.organizations, null, 2);
            message('Dry run complete. ' + data.settings_count + ' full settings backups must verify before the first change.');
        } catch (error) {
            if (current === generation) message(error.message, true);
        }
    }

    async function apply() {
        if (busy || !token || element('policyConfirmation').value !== 'CONFIGURE') return;
        busy = true;
        const selectedToken = token;
        token = null;
        element('policyApply').disabled = true;
        element('policyPreview').disabled = true;
        element('policyLoad').disabled = true;
        element('policyResult').textContent = '';
        message('Verifying all complete settings backups before saving organization policies and removing site overrides...');
        try {
            const data = await request('/api/firmware-policy/apply', {token: selectedToken, confirmation: 'CONFIGURE'});
            element('policyResult').textContent = JSON.stringify(data, null, 2);
            message(data.status === 'complete' ? 'Settings change complete. All backups and changed settings verified.' :
                'Partial completion. Review the failed and remaining targets below.', data.status !== 'complete');
        } catch (error) {
            element('policyResult').textContent = error.message;
            message(error.message + ' Create a new preview before another attempt.', true);
        } finally {
            busy = false;
            element('policyLoad').disabled = false;
            element('policyPreview').disabled = !catalogs;
        }
    }

    element('policyMsp').addEventListener('change', organizations);
    element('policyOrganizations').addEventListener('change', resetCatalog);
    document.querySelectorAll('[data-policy-kind]').forEach(input => input.addEventListener('change', resetCatalog));
    element('policyModels').addEventListener('change', invalidate);
    element('policyModels').addEventListener('input', invalidate);
    element('policyLoad').addEventListener('click', loadCatalog);
    element('policyPreview').addEventListener('click', preview);
    element('policyApply').addEventListener('click', apply);
    element('policyConfirmation').addEventListener('input', () => {
        element('policyApply').disabled = busy || !token || element('policyConfirmation').value !== 'CONFIGURE';
    });
    organizations();
    request('/api/operations/msps').then(data => {
        (data.msps || []).forEach(msp => option(element('policyMsp'), msp.id || msp.msp_id, msp.name || msp.msp_name));
    }).catch(error => message('MSP choices could not be read: ' + error.message, true));
}());
