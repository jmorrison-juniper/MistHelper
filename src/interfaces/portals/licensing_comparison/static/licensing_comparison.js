/* Render the existing authorized comparison contract without inserting API markup. */
(() => {
  const root = document.querySelector(".licensing-dashboard");
  const find = (selector) => root.querySelector(selector);
  const stateKey = "misthelper.licensingComparison.v1";
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content ?? "";
  const descriptions = {
    "SUB-AI": "Mist AI bundle. Components use the current Mist catalog.",
    "SUB-MAN": "Wireless Assurance: access point management.",
    "SUB-VNA": "Marvis Virtual Network Assistant for wireless networks.",
    "SUB-AST": "Asset visibility and location services.",
    "SUB-ENG": "User engagement and location services.",
    "SUB-PMA": "Premium analytics.",
    "SUB-EX12": "Wired Assurance for 12-port EX switches.",
    "SUB-EX24": "Wired Assurance for 24-port EX switches.",
    "SUB-EX48": "Wired Assurance for 48-port EX switches.",
    "SUB-SVNA": "Marvis Virtual Network Assistant for switches.",
    "SUB-WAN": "WAN Assurance for gateways.",
    "SUB-WVNA": "Marvis Virtual Network Assistant for WAN networks.",
  };
  const inventoryNames = ["AP", "SWITCH", "GATEWAY"];
  const standardLicenses = Object.keys(descriptions);
  let storageError = "";
  let state = readState();
  let organizations = [];
  let comparison = null;
  let busy = false;
  let locked = false;

  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = String(text);
    if (className) element.className = className;
    return element;
  }

  function setStatus(message) {
    find("#page-status").textContent = `${message} ${storageError}`.trim();
  }

  function readState() {
    try {
      const value = JSON.parse(sessionStorage.getItem(stateKey) || "null");
      if (!value) return { selected: [], manual: [], purchased: {} };
      if (!validState(value)) {
        throw new Error("Invalid saved comparison data.");
      }
      return value;
    } catch (error) {
      storageError = `Browser session data is unavailable: ${error.message}`;
      setStatus("");
      return { selected: [], manual: [], purchased: {} };
    }
  }

  function validState(value) {
    const countsValid = (counts) => counts && typeof counts === "object" && !Array.isArray(counts) &&
      Object.entries(counts).every(([name, amount]) => /^[A-Za-z0-9_-]{1,32}$/.test(name) && count(amount) !== null);
    return Array.isArray(value.selected) && value.selected.every((id) => typeof id === "string") &&
      Array.isArray(value.manual) && value.manual.every((row) => row &&
        typeof row.name === "string" && /^manual-[A-Za-z0-9_-]{1,64}$/.test(row.row_id) &&
        countsValid(row.licenses) && countsValid(row.inventory)) &&
      value.purchased && typeof value.purchased === "object" && !Array.isArray(value.purchased) &&
      Object.values(value.purchased).every(countsValid);
  }

  function saveState() {
    try {
      sessionStorage.setItem(stateKey, JSON.stringify(state));
    } catch (error) {
      storageError = `Browser session data could not be saved: ${error.message}`;
      setStatus("");
    }
  }

  function updateButtons() {
    const count = state.selected.length;
    find("#selected-count").textContent = count;
    const unavailable = root.dataset.sessionAvailable !== "true";
    find("#compare-button").disabled = busy || unavailable || !(count + state.manual.length);
    find("#calculate-button").disabled = find("#compare-button").disabled;
    find("#select-all-button").disabled = busy || !organizations.length;
    find("#refresh-button").disabled = busy || unavailable;
    find("#export-button").disabled = busy || !comparison?.results?.length;
    ["#add-row-button", "#clear-purchases-button"].forEach((selector) => { find(selector).disabled = busy; });
    root.querySelectorAll("input, [data-testid='remove-manual-row']").forEach((input) => { input.disabled = locked; });
  }

  function invalidate() {
    comparison = null;
    find("#export-button").disabled = true;
    find("#balance-results").replaceChildren();
    find("#summary-cards").hidden = true;
    find("#comparison-results").replaceChildren(node("tr"));
    find("#comparison-results tr").append(node("td", "Values changed. Compare again to update results."));
    find("#comparison-totals").replaceChildren();
    updateButtons();
  }

  function normalize(name) {
    return String(name).toUpperCase().replaceAll("_", "-");
  }

  function count(value) {
    return Number.isSafeInteger(value) && value >= 0 ? value : null;
  }

  function countMap(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    return Object.fromEntries(Object.entries(value).map(([key, amount]) => [normalize(key), count(amount)]));
  }

  function outcomeData(outcome) {
    return outcome && outcome.status_code >= 200 && outcome.status_code < 300 && !outcome.error ? outcome.data : null;
  }

  function display(value) {
    return value === null || value === undefined ? "Unavailable" : value.toLocaleString();
  }

  function total(values) {
    const known = values.filter((value) => value !== null);
    const sum = known.reduce((value, amount) => value + amount, 0);
    if (known.length === values.length) return display(sum);
    return known.length ? `${display(sum)} (incomplete)` : "Unavailable (incomplete)";
  }

  function inventoryCounts(item) {
    const data = outcomeData(item.inventory);
    if (Array.isArray(data)) {
      return [...inventoryNames.map((kind) => data.filter((device) => normalize(device?.type) === kind).length), data.length];
    }
    if (data && typeof data === "object") {
      const counts = countMap(data);
      const values = inventoryNames.map((kind) => counts[kind] ?? null);
      return [...values, values.every((value) => value !== null) ? values.reduce((sum, value) => sum + value, 0) : null];
    }
    return [null, null, null, null];
  }

  function licenseTypes(rows) {
    const names = new Set();
    rows.forEach((item) => {
      const summary = outcomeData(item.license_summary);
      [summary?.summary, summary?.entitled].forEach((values) => Object.keys(countMap(values)).forEach((name) => names.add(name)));
      (Array.isArray(summary?.amendments) ? summary.amendments : []).forEach((record) => {
        if (typeof record.type === "string") names.add(normalize(record.type));
      });
      if (rows.some((item) => outcomeData(item.license_summary) === null)) standardLicenses.forEach((name) => names.add(name));
    });
    return Array.from(names).sort();
  }

  function renderHeader(types) {
    const row = node("tr");
    ["Organization", "Status", "APs", "Switches", "Gateways", "Total devices", ...types].forEach((text, index) => {
      const cell = node("th", text);
      cell.scope = "col";
      if (index >= 6) {
        cell.dataset.license = text;
        cell.title = descriptions[text] ?? `${text}: description unavailable.`;
        cell.tabIndex = 0;
        cell.setAttribute("aria-label", `${text}. ${cell.title} Values: used / entitled.`);
      }
      row.append(cell);
    });
    find("#comparison-head").replaceChildren(row);
  }

  function licensePair(item, type) {
    const data = outcomeData(item.license_summary);
    return [countMap(data?.summary)[type] ?? null, countMap(data?.entitled)[type] ?? null];
  }

  function renderResult(item, types) {
    const row = node("tr");
    const name = node("th", item.name);
    name.scope = "row";
    row.append(name, node("td", item.request_status));
    inventoryCounts(item).forEach((value) => row.append(node("td", display(value))));
    types.forEach((type) => row.append(node("td", licensePair(item, type).map(display).join(" / "))));
    const errors = ["license_summary", "license_use_by_site", "inventory"]
      .filter((key) => outcomeData(item[key]) === null)
      .map((key) => `${key.replaceAll("_", " ")}: ${item[key]?.error ?? "Unavailable"}`);
    if (errors.length) row.children[1].append(node("p", errors.join(". "), "licensing-errors"));
    return row;
  }

  function renderTotals(rows, types) {
    const row = node("tr");
    row.append(node("th", "TOTAL"), node("td", `${rows.length} organizations`));
    [0, 1, 2, 3].forEach((index) => row.append(node("td", total(rows.map((item) => inventoryCounts(item)[index])))));
    types.forEach((type) => row.append(node("td", [0, 1].map((index) => total(rows.map((item) => licensePair(item, type)[index]))).join(" / "))));
    find("#comparison-totals").replaceChildren(row);
    renderSummary(rows);
  }

  function renderSummary(rows) {
    const cards = find("#summary-cards");
    cards.replaceChildren();
    ["Total APs", "Total switches", "Total gateways", "Organizations"].forEach((label, index) => {
      const card = node("article");
      const value = node("strong", index === 3 ? rows.length : total(rows.map((item) => inventoryCounts(item)[index])));
      value.dataset.testid = ["summary-ap", "summary-switch", "summary-gateway", "summary-organizations"][index];
      card.append(value, node("span", label));
      cards.append(card);
    });
    cards.hidden = false;
  }

  function renderBalances(rows) {
    const container = find("#balance-results");
    container.replaceChildren();
    rows.forEach((item) => (item.balances ?? []).forEach((balance) => {
      const card = node("article", undefined, "licensing-balance-card");
      card.append(node("h3", `${item.name}: ${balance.license_type}`));
      [balance, ...(balance.bundle_components ?? [])].forEach((part) => {
        card.append(node("p", `${part.license_type}: purchased ${display(part.purchased_count)}, used ${display(part.used_count)}, remaining ${display(part.remaining_count)}`));
      });
      container.append(card);
    }));
  }

  function renderComparison() {
    const rows = comparison.results;
    const types = licenseTypes(rows);
    renderHeader(types);
    find("#comparison-results").replaceChildren(...rows.map((item) => renderResult(item, types)));
    renderTotals(rows, types);
    renderBalances(rows);
    if (!rows.length) {
      const row = node("tr");
      row.append(node("td", "No comparison results are available."));
      find("#comparison-results").append(row);
    }
    find("#export-button").disabled = !rows.length;
  }

  function selectedRows() {
    const selected = organizations.filter((item) => state.selected.includes(item.org_id));
    return [...selected, ...state.manual.map((item) => ({ org_id: item.row_id, name: item.name || "Manual organization" }))];
  }

  function numericField(name, value, kind) {
    const label = node("label", name);
    const input = node("input");
    Object.assign(input, { type: "number", min: "0", step: "1", max: String(Number.MAX_SAFE_INTEGER), value: value ?? "" });
    input.dataset[kind] = name;
    input.dataset.testid = kind === "inventory" ? "manual-inventory-count" : "license-count";
    input.setAttribute("aria-label", name);
    label.append(input);
    return label;
  }

  function fieldsGrid(values, names, kind) {
    const grid = node("div", undefined, "licensing-count-grid");
    Array.from(new Set([...names, ...Object.keys(values)])).forEach((name) => grid.append(numericField(name, values[name], kind)));
    return grid;
  }

  function readCounts(container, kind) {
    return Object.fromEntries(Array.from(container.querySelectorAll(`input[data-${kind}]`))
      .filter((input) => input.value !== "")
      .map((input) => {
        if (!input.checkValidity() || count(Number(input.value)) === null) throw new Error("Enter non-negative whole-number counts.");
        return [input.dataset[kind], Number(input.value)];
      }));
  }

  function captureInputs() {
    const manual = Array.from(find("#manual-rows").children, (fieldset) => ({
      row_id: fieldset.dataset.rowId,
      name: fieldset.querySelector(".manual-name").value.trim(),
      licenses: readCounts(fieldset, "license"),
      inventory: readCounts(fieldset, "inventory"),
    }));
    const purchased = Object.fromEntries(Array.from(find("#purchased-inputs").querySelectorAll("fieldset"), (fieldset) =>
      [fieldset.dataset.rowId, readCounts(fieldset, "license")]));
    state.manual = manual;
    state.purchased = { ...state.purchased, ...purchased };
    saveState();
  }

  function renderPurchasedInputs() {
    const container = find("#purchased-inputs");
    container.replaceChildren();
    selectedRows().forEach((item) => {
      const fieldset = node("fieldset", undefined, "purchase-input");
      fieldset.dataset.rowId = item.org_id;
      fieldset.append(node("legend", item.name));
      const values = state.purchased[item.org_id] ?? {};
      const types = comparison ? licenseTypes(comparison.results) : ["SUB-EX24", "SUB-MAN", "SUB-VNA", "SUB-WAN"];
      fieldset.append(fieldsGrid(values, ["SUB-AI", ...types], "license"));
      container.append(fieldset);
    });
    if (!container.children.length) container.append(node("p", "Select organizations or add a manual organization to enter purchased counts."));
  }

  function renderManualRows() {
    const container = find("#manual-rows");
    container.replaceChildren();
    state.manual.forEach((item) => {
      const fieldset = node("fieldset", undefined, "manual-row");
      fieldset.dataset.rowId = item.row_id;
      const label = node("label", "Organization name", "licensing-name-label");
      const input = node("input", undefined, "manual-name");
      Object.assign(input, { type: "text", maxLength: 120, required: true, value: item.name });
      input.dataset.testid = "manual-name";
      label.append(input);
      const remove = node("button", "Remove");
      remove.type = "button";
      remove.dataset.testid = "remove-manual-row";
      remove.addEventListener("click", () => removeManual(item.row_id));
      fieldset.append(node("legend", "Manual organization"), label,
        fieldsGrid(item.inventory, inventoryNames, "inventory"), fieldsGrid(item.licenses, standardLicenses, "license"), remove);
      container.append(fieldset);
    });
  }

  function removeManual(rowId) {
    captureInputs();
    state.manual = state.manual.filter((item) => item.row_id !== rowId);
    delete state.purchased[rowId];
    saveState();
    invalidate();
    renderManualRows();
    renderPurchasedInputs();
  }

  function renderOrganizations() {
    const container = find("#organization-select");
    container.replaceChildren();
    organizations.forEach((item) => {
      const label = node("label", undefined, "licensing-org-choice");
      const input = node("input");
      Object.assign(input, { type: "checkbox", value: item.org_id, checked: state.selected.includes(item.org_id) });
      input.dataset.testid = "organization-checkbox";
      input.addEventListener("change", () => run(changeSelection));
      label.append(input, node("span", item.name));
      container.append(label);
    });
    updateButtons();
  }

  function changeSelection() {
    captureInputs();
    state.selected = Array.from(find("#organization-select").querySelectorAll("input:checked"), (input) => input.value);
    saveState();
    invalidate();
    renderPurchasedInputs();
  }

  async function loadOrganizations() {
    setStatus("Reading authorized organizations from Mist.");
    const response = await fetch("/api/license-comparison/organizations");
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.errors?.[0]?.error ?? "The organization list could not be loaded.");
    organizations = payload.organizations;
    state.selected = state.selected.filter((id) => organizations.some((item) => item.org_id === id));
    saveState();
    invalidate();
    renderOrganizations();
    renderPurchasedInputs();
    setStatus(payload.errors?.length ? `Organization discovery is incomplete: ${payload.errors.map((item) => item.error).join(". ")}` :
      organizations.length ? `${organizations.length} authorized organizations available.` : "No authorized organizations are available.");
  }

  async function compare() {
    invalidate();
    captureInputs();
    const invalidName = Array.from(find("#manual-rows").querySelectorAll(".manual-name")).some((input) => !input.checkValidity() || !input.value.trim());
    if (invalidName) throw new Error("Enter a name for each manual organization.");
    const purchases = Object.fromEntries(selectedRows().map((item) => [item.org_id, state.purchased[item.org_id] ?? {}]));
    setStatus("Reading licenses and inventory from Mist.");
    const response = await fetch("/api/license-comparison", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ organization_ids: state.selected, manual_rows: state.manual, purchased_amounts: purchases }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error ?? "The comparison failed.");
    comparison = payload;
    renderComparison();
    renderPurchasedInputs();
    const errors = [...(payload.discovery_errors ?? []), ...(payload.catalog_error ? [payload.catalog_error] : [])];
    setStatus(`Compared ${payload.results.length} organization rows.${errors.length ? ` Some data is unavailable: ${errors.map((item) => item.error).join(". ")}` : ""}`);
  }

  async function exportCsv() {
    if (!comparison) throw new Error("Compare organizations before exporting.");
    const response = await fetch("/api/license-comparison/export", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify(comparison),
    });
    if (!response.ok) throw new Error((await response.json()).error ?? "The CSV export failed.");
    const address = URL.createObjectURL(await response.blob());
    const link = node("a");
    link.href = address;
    link.download = "mist_org_licensing_comparison.csv";
    link.click();
    URL.revokeObjectURL(address);
    setStatus("The comparison CSV is ready.");
  }

  async function run(action, lockInputs = false) {
    if (busy) return;
    busy = true;
    locked = lockInputs;
    updateButtons();
    try {
      await action();
    } catch (error) {
      setStatus(error.message);
    } finally {
      busy = false;
      locked = false;
      updateButtons();
    }
  }

  function bindControls() {
    find("#compare-button").addEventListener("click", () => run(compare, true));
    find("#calculate-button").addEventListener("click", () => run(compare, true));
    find("#refresh-button").addEventListener("click", () => run(loadOrganizations, true));
    find("#export-button").addEventListener("click", () => run(exportCsv));
    find("#select-all-button").addEventListener("click", () => run(() => {
      find("#organization-select").querySelectorAll("input").forEach((input) => { input.checked = true; });
      changeSelection();
    }));
  }

  function bindForms() {
    find("#add-row-button").addEventListener("click", () => run(() => {
      captureInputs();
      state.manual.push({ row_id: `manual-${crypto.randomUUID()}`, name: "", licenses: {}, inventory: {} });
      saveState();
      invalidate();
      renderManualRows();
      renderPurchasedInputs();
    }));
    find("#clear-purchases-button").addEventListener("click", () => {
      state.purchased = {};
      saveState();
      invalidate();
      renderPurchasedInputs();
    });
    [find("#manual-rows"), find("#purchased-inputs")].forEach((container) => container.addEventListener("change", () => run(() => {
      invalidate();
      captureInputs();
      setStatus("Values saved for this browser session. Compare again to update results.");
    })));
  }

  renderHeader([]);
  renderManualRows();
  renderPurchasedInputs();
  bindControls();
  bindForms();
  updateButtons();
  if (root.dataset.sessionAvailable === "true") run(loadOrganizations, true);
})();
