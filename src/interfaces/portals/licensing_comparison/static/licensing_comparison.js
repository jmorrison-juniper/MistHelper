(() => {
  const stateKey = "misthelper.licensingComparison.v1";
  const selection = document.querySelector("#organization-select");
  const results = document.querySelector("#comparison-results");
  const status = document.querySelector("#page-status");
  const manualRows = document.querySelector("#manual-rows");
  const purchasedInputs = document.querySelector("#purchased-inputs");
  const template = document.querySelector("#manual-row-template");
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content ?? "";
  let availableOrganizations = [];
  let comparison = null;
  let state = readState();

  function readState() {
    try {
      const saved = sessionStorage.getItem(stateKey);
      return saved ? JSON.parse(saved) : { selected: [], manual: [], purchased: {} };
    } catch (error) {
      setStatus(`Browser session data is unavailable: ${error.name}.`);
      return { selected: [], manual: [], purchased: {} };
    }
  }

  function saveState() {
    try {
      sessionStorage.setItem(stateKey, JSON.stringify(state));
    } catch (error) {
      setStatus(`Browser session data could not be saved: ${error.name}.`);
    }
  }

  function setStatus(message) {
    status.textContent = message;
  }

  function escapeJson(value) {
    try {
      const parsed = JSON.parse(value || "{}");
      if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
        throw new Error("Expected an object.");
      }
      return parsed;
    } catch {
      throw new Error("Enter a JSON object with non-negative whole-number values.");
    }
  }

  function renderManualRows() {
    manualRows.replaceChildren();
    state.manual.forEach((row) => {
      const fragment = template.content.cloneNode(true);
      const fieldset = fragment.querySelector(".manual-row");
      fieldset.dataset.rowId = row.row_id;
      fieldset.querySelector(".manual-name").value = row.name;
      fieldset.querySelector(".manual-licenses").value = JSON.stringify(row.licenses);
      fieldset.querySelector(".manual-inventory").value = JSON.stringify(row.inventory);
      fieldset.querySelector(".remove-row-button").addEventListener("click", () => {
        state.manual = state.manual.filter((item) => item.row_id !== row.row_id);
        delete state.purchased[row.row_id];
        saveState();
        renderManualRows();
        renderPurchasedInputs();
      });
      fieldset.addEventListener("change", () => updateManualRow(fieldset));
      manualRows.append(fragment);
    });
  }

  function updateManualRow(fieldset) {
    const row = state.manual.find((item) => item.row_id === fieldset.dataset.rowId);
    if (!row) {
      return;
    }
    try {
      row.name = fieldset.querySelector(".manual-name").value.trim();
      row.licenses = escapeJson(fieldset.querySelector(".manual-licenses").value);
      row.inventory = escapeJson(fieldset.querySelector(".manual-inventory").value);
      saveState();
      renderPurchasedInputs();
      setStatus("Manual organization values saved for this browser session.");
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function loadOrganizations() {
    const response = await fetch("/api/license-comparison/organizations");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.errors?.[0]?.error ?? "The organization list could not be loaded.");
    }
    availableOrganizations = payload.organizations;
    selection.replaceChildren();
    payload.organizations.forEach((organization) => {
      const option = document.createElement("option");
      option.value = organization.org_id;
      option.textContent = organization.name;
      option.selected = state.selected.includes(option.value);
      selection.append(option);
    });
    renderPurchasedInputs();
  }

  function renderPurchasedInputs() {
    purchasedInputs.replaceChildren();
    const selected = new Set(Array.from(selection.selectedOptions, (option) => option.value));
    const rows = availableOrganizations.filter((organization) => selected.has(organization.org_id));
    rows.push(...state.manual.map((row) => ({ org_id: row.row_id, name: row.name || "Manual organization" })));
    rows.forEach((organization) => {
      const label = document.createElement("label");
      label.className = "purchase-input";
      label.dataset.rowId = organization.org_id;
      label.append(`${organization.name} purchased license counts`);
      const input = document.createElement("textarea");
      input.value = JSON.stringify(state.purchased[organization.org_id] ?? {});
      input.setAttribute("aria-label", `${organization.name} purchased license counts`);
      input.dataset.testid = "purchased-license-input";
      input.addEventListener("change", () => {
        try {
          const values = escapeJson(input.value);
          if (Object.values(values).some((value) => !Number.isInteger(value) || value < 0)) {
            throw new Error("Use non-negative whole numbers for purchased license counts.");
          }
          state.purchased[organization.org_id] = values;
          saveState();
          setStatus("Purchased license counts saved for this browser session.");
        } catch (error) {
          setStatus(error.message);
        }
      });
      label.append(input);
      purchasedInputs.append(label);
    });
  }

  function renderValue(value) {
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(value ?? "Unavailable", null, 2);
    return pre;
  }

  function renderComparison() {
    results.replaceChildren();
    if (!comparison?.results?.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 6;
      cell.textContent = "No comparison results are available.";
      row.append(cell);
      results.append(row);
      return;
    }
    comparison.results.forEach((item) => {
      const row = document.createElement("tr");
      const fields = [
        item.name,
        item.request_status,
        item.license_summary,
        item.license_use_by_site,
        item.inventory,
        item.balances,
      ];
      fields.forEach((value, index) => {
        const cell = document.createElement("td");
        if (index < 2) {
          cell.textContent = String(value ?? "Unavailable");
        } else {
          cell.append(renderValue(value));
        }
        row.append(cell);
      });
      results.append(row);
    });
  }

  async function compare() {
    state.selected = Array.from(selection.selectedOptions, (option) => option.value);
    saveState();
    setStatus("Reading licenses and inventory from Mist.");
    const response = await fetch("/api/license-comparison", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({
        organization_ids: state.selected,
        manual_rows: state.manual,
        purchased_amounts: state.purchased,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error ?? "The comparison failed.");
    }
    comparison = payload;
    renderComparison();
    document.querySelector("#export-button").disabled = !payload.results?.length;
    setStatus(`Compared ${payload.results?.length ?? 0} organization rows.`);
  }

  async function exportCsv() {
    const response = await fetch("/api/license-comparison/export", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify(comparison),
    });
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.error ?? "The CSV export failed.");
    }
    const blob = await response.blob();
    const address = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = address;
    link.download = "mist_org_licensing_comparison.csv";
    link.click();
    URL.revokeObjectURL(address);
    setStatus("The comparison CSV is ready.");
  }

  document.querySelector("#add-row-button").addEventListener("click", () => {
    const rowId = `manual-${crypto.randomUUID()}`;
    state.manual.push({ row_id: rowId, name: "", licenses: {}, inventory: {} });
    saveState();
    renderManualRows();
  });

  document.querySelector("#compare-button").addEventListener("click", () => {
    compare().catch((error) => setStatus(error.message));
  });

  document.querySelector("#export-button").addEventListener("click", () => {
    exportCsv().catch((error) => setStatus(error.message));
  });

  selection.addEventListener("change", () => {
    state.selected = Array.from(selection.selectedOptions, (option) => option.value);
    saveState();
    renderPurchasedInputs();
  });

  renderManualRows();
  renderPurchasedInputs();
  loadOrganizations().catch((error) => setStatus(error.message));
})();
