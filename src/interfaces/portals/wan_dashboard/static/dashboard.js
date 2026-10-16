/* Build the WAN dashboard with text nodes so Mist data cannot become markup. */
(() => {
    "use strict";

    const root = document.getElementById("wan-dashboard");
    if (!root) return;

    const state = {
        gateways: [],
        activeGateway: null,
        activePort: null,
        activeTrafficRange: "7d",
        activeInsightRange: "24h",
        peersByPort: {},
    };

    const elements = {
        status: document.getElementById("wan-status"),
        rows: document.getElementById("wan-gateway-rows"),
        siteFilter: document.getElementById("wan-site-filter"),
        search: document.getElementById("wan-gateway-search"),
        empty: document.getElementById("wan-empty-state"),
        gatewayCount: document.getElementById("wan-gateway-count"),
        portCount: document.getElementById("wan-port-count"),
        connectedCount: document.getElementById("wan-connected-count"),
        activePortCount: document.getElementById("wan-active-port-count"),
        chartModal: document.getElementById("wan-chart-modal"),
        chartRate: document.getElementById("wan-chart-rate"),
        chartData: document.getElementById("wan-chart-data"),
        chartStatus: document.getElementById("wan-chart-status"),
        trafficRange: document.getElementById("wan-traffic-range"),
        insightModal: document.getElementById("wan-insights-modal"),
        insightRange: document.getElementById("wan-insights-range"),
        insightContent: document.getElementById("wan-insights-content"),
        portExport: document.getElementById("wan-port-export"),
        peerModal: document.getElementById("wan-peer-modal"),
        peerSummary: document.getElementById("wan-peer-summary"),
        peerContent: document.getElementById("wan-peer-content"),
    };

    function node(tag, text, className) {
        const element = document.createElement(tag);
        if (text !== undefined && text !== null) element.textContent = String(text);
        if (className) element.className = className;
        return element;
    }

    async function requestJson(url) {
        const response = await fetch(url, { headers: { Accept: "application/json" } });
        let payload;
        try {
            payload = await response.json();
        } catch {
            throw new Error("The portal returned an invalid response.");
        }
        if (!response.ok) {
            const error = new Error(payload.notice || `Request failed with status ${response.status}.`);
            error.status = response.status;
            throw error;
        }
        return payload;
    }

    function setStatus(message, status = "ok") {
        elements.status.textContent = message;
        elements.status.dataset.state = status;
    }

    function filteredGateways() {
        const selectedSite = elements.siteFilter.value;
        const query = elements.search.value.trim().toLocaleLowerCase();
        return state.gateways.filter((gateway) => {
            const matchesSite = !selectedSite || gateway.site_id === selectedSite;
            const searchable = `${gateway.name} ${gateway.model} ${gateway.site_name}`.toLocaleLowerCase();
            return matchesSite && (!query || searchable.includes(query));
        });
    }

    function populateSites() {
        const selected = elements.siteFilter.value;
        const siteNames = new Map(state.gateways.map((gateway) => [gateway.site_id, gateway.site_name]));
        elements.siteFilter.replaceChildren(node("option", "All sites"));
        elements.siteFilter.options[0].value = "";
        for (const [siteId, siteName] of [...siteNames.entries()].sort((left, right) => left[1].localeCompare(right[1]))) {
            const option = node("option", siteName);
            option.value = siteId;
            elements.siteFilter.append(option);
        }
        elements.siteFilter.value = selected;
    }

    function gatewayCell(row, value) {
        const cell = node("td", value || "Unavailable");
        row.append(cell);
        return cell;
    }

    function formatUptime(seconds) {
        const value = Number(seconds);
        if (!Number.isFinite(value) || value < 0) return "Unavailable";
        const hours = Math.floor(value / 3600);
        const days = Math.floor(hours / 24);
        return days ? `${days}d ${hours % 24}h` : `${hours}h`;
    }

    function formatBytes(value) {
        const bytes = Number(value);
        if (!Number.isFinite(bytes) || bytes < 0) return "Unavailable";
        if (bytes === 0) return "0 B";
        const units = ["B", "KB", "MB", "GB", "TB"];
        const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
        return `${(bytes / 1024 ** index).toFixed(2)} ${units[index]}`;
    }

    function gatewayRow(gateway) {
        const row = document.createElement("tr");
        row.dataset.testid = "wan-gateway-row";
        row.dataset.gatewayId = gateway.device_id;
        row.append(
            node("td", gateway.site_name || "Unavailable"),
            node("td", gateway.name || "Unknown gateway"),
            node("td", gateway.model || "Unavailable"),
        );
        const status = gatewayCell(row, gateway.status || "unknown");
        status.dataset.status = String(gateway.status || "unknown").toLocaleLowerCase();
        gatewayCell(row, gateway.ip);
        gatewayCell(row, formatUptime(gateway.uptime));
        gatewayCell(row, gateway.wan_port_count);
        const actionCell = document.createElement("td");
        const button = node("button", "Details", "btn btn-sm btn-outline-primary");
        button.type = "button";
        button.dataset.action = "details";
        button.setAttribute("aria-label", `Show details for ${gateway.name || "gateway"}`);
        actionCell.append(button);
        row.append(actionCell);
        return row;
    }

    function renderGateways() {
        const gateways = filteredGateways();
        elements.rows.replaceChildren();
        elements.empty.hidden = gateways.length > 0;
        for (const gateway of gateways) elements.rows.append(gatewayRow(gateway));
        elements.gatewayCount.textContent = String(state.gateways.length);
        elements.portCount.textContent = String(
            state.gateways.reduce((total, gateway) => total + Number(gateway.wan_port_count || 0), 0),
        );
        elements.connectedCount.textContent = String(
            state.gateways.filter((gateway) => String(gateway.status).toLowerCase() === "connected").length,
        );
        elements.activePortCount.textContent = String(
            state.gateways.reduce(
                (total, gateway) =>
                    total + (gateway.ports || []).filter((port) => port.up === true && port.enabled !== false).length,
                0,
            ),
        );
        if (gateways.length === 0) {
            const row = node("tr");
            row.append(node("td", "No gateways match these filters.", "wan-empty"));
            row.firstChild.colSpan = 8;
            elements.rows.append(row);
        }
    }

    async function loadOverview() {
        setStatus("Loading gateway data.");
        try {
            const result = await requestJson("/wan-dashboard/api/overview");
            state.gateways = Array.isArray(result.data) ? result.data : [];
            populateSites();
            renderGateways();
            if (result.notice) setStatus(result.notice, result.status);
            else if (result.status === "empty") setStatus("No gateways are available.", "empty");
            else setStatus(`${state.gateways.length} gateways loaded.`);
        } catch (error) {
            setStatus(error.message, error.status === 429 ? "rate_limited" : "error");
        }
    }

    function detailCell(row, value) {
        const cell = node("td", value === null || value === undefined || value === "" ? "Unavailable" : value);
        row.append(cell);
        return cell;
    }

    function portAction(action, label, gateway, port) {
        const button = node("button", label, "btn btn-sm btn-outline-primary");
        button.type = "button";
        button.dataset.action = action;
        button.dataset.gatewayId = gateway.device_id;
        button.dataset.portId = port.port_id;
        button.dataset.gatewayName = gateway.name;
        button.dataset.portName = port.name || port.port_id;
        return button;
    }

    function trafficCell(gateway, port, field, direction) {
        const cell = document.createElement("td");
        const value = formatBytes(port[field]);
        const button = portAction("traffic", value, gateway, port);
        button.className = "btn btn-link p-0 wan-traffic-value";
        button.setAttribute("aria-label", `Show traffic chart for ${gateway.name} ${port.name} ${direction} total ${value}`);
        cell.append(button);
        return cell;
    }

    function portTable(gateway, ports) {
        const table = node("table", undefined, "table table-sm wan-port-table");
        const headings = [
            "Port", "WAN", "Description", "Enabled", "Status", "Gateway IP", "WAN IP", "VLAN",
            "Netmask", "Type", "Override", "MAC", "Speed", "RX data", "TX data", "Peer paths",
        ];
        const header = document.createElement("thead");
        const headingRow = document.createElement("tr");
        for (const heading of headings) {
            const cell = node("th", heading, "text-nowrap");
            cell.scope = "col";
            headingRow.append(cell);
        }
        header.append(headingRow);
        const body = document.createElement("tbody");
        for (const port of ports) body.append(portRow(gateway, port));
        table.append(header, body);
        return table;
    }

    function portRow(gateway, port) {
        const row = document.createElement("tr");
        const values = [
            port.name || port.port_id, port.wan_name, port.description,
            port.enabled === true ? "Yes" : port.enabled === false ? "No" : "Unavailable",
            port.up === true ? "Up" : port.up === false ? "Down" : "Unavailable",
            port.gateway, port.ip, port.vlan_id, port.netmask, port.configuration_type,
            port.override, port.mac, port.speed,
        ];
        for (const value of values) detailCell(row, value);
        row.append(trafficCell(gateway, port, "rx_bytes", "receive"));
        row.append(trafficCell(gateway, port, "tx_bytes", "transmit"));
        const actions = node("td", undefined, "wan-actions-cell");
        const peerCount = (state.peersByPort[port.port_id] || []).length;
        const peersButton = portAction("peers", `Peer paths (${peerCount})`, gateway, port);
        peersButton.disabled = peerCount === 0;
        actions.append(
            portAction("traffic", "Traffic", gateway, port),
            portAction("insights", "Insights", gateway, port),
            peersButton,
        );
        row.append(actions);
        return row;
    }

    async function expandGateway(row) {
        const previous = row.nextElementSibling;
        if (previous?.classList.contains("wan-details-row")) {
            previous.remove();
            row.classList.remove("is-expanded");
            return;
        }
        const gateway = state.gateways.find((item) => item.device_id === row.dataset.gatewayId);
        if (!gateway) return;
        const detailsRow = node("tr", undefined, "wan-details-row");
        detailsRow.dataset.testid = "wan-port-details-row";
        const detailCellElement = document.createElement("td");
        detailCellElement.colSpan = 8;
        detailCellElement.append(node("p", "Loading port details.", "wan-muted"));
        detailsRow.append(detailCellElement);
        row.after(detailsRow);
        row.classList.add("is-expanded");
        try {
            const result = await requestJson(`/wan-dashboard/api/gateways/${encodeURIComponent(gateway.device_id)}/ports`);
            detailCellElement.replaceChildren();
            if (result.notice) setStatus(result.notice, result.status);
            const data = result.data || {};
            const ports = Array.isArray(data.ports) ? data.ports : [];
            state.peersByPort = data.peers_by_port || {};
            detailCellElement.append(node("h3", "WAN port details"));
            if (ports.length) detailCellElement.append(portTable(gateway, ports));
            else detailCellElement.append(node("p", "No WAN port data is available.", "wan-muted"));
        } catch (error) {
            detailCellElement.replaceChildren(node("p", error.message, "wan-status"));
        }
    }

    function sampleValue(sample, field) {
        if (sample[field] === null || sample[field] === undefined || sample[field] === "") return null;
        const value = Number(sample[field]);
        return Number.isFinite(value) ? value : null;
    }

    function chartPath(samples, field, width, height, maximum) {
        return samples
            .map((sample, index) => {
                const value = sampleValue(sample, field);
                if (value === null) return null;
                const x = samples.length < 2 ? width / 2 : (index / (samples.length - 1)) * width;
                return `${x},${height - (value / maximum) * height}`;
            })
            .filter(Boolean)
            .join(" ");
    }

    function appendChartGrid(svg, width, height) {
        for (let line = 1; line <= 4; line += 1) {
            const grid = document.createElementNS(svg.namespaceURI, "line");
            grid.setAttribute("x1", "0");
            grid.setAttribute("x2", String(width));
            grid.setAttribute("y1", String((height / 4) * line));
            grid.setAttribute("y2", String((height / 4) * line));
            grid.setAttribute("class", "chart-grid");
            svg.append(grid);
        }
    }

    function appendChartLegend(container, series) {
        const legend = node("div", undefined, "wan-chart-legend");
        for (const item of series) legend.append(node("span", item.label, item.className));
        container.append(legend);
    }

    function renderChart(container, samples, series) {
        container.replaceChildren();
        const values = samples.flatMap((sample) =>
            series.map((item) => sampleValue(sample, item.field)).filter((value) => value !== null),
        );
        if (!values.length) {
            container.append(node("p", "No samples are available for this chart.", "wan-empty"));
            return;
        }
        const width = 900;
        const height = 260;
        const maximum = Math.max(1, ...values);
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        svg.setAttribute("role", "img");
        svg.setAttribute("aria-label", series.map((item) => item.label).join(", "));
        appendChartGrid(svg, width, height);
        for (const item of series) {
            const line = document.createElementNS(svg.namespaceURI, "polyline");
            line.setAttribute("points", chartPath(samples, item.field, width, height, maximum));
            line.setAttribute("class", item.className);
            svg.append(line);
        }
        container.append(svg);
        appendChartLegend(container, series);
    }

    function transferredSamples(samples, range) {
        const first = Number(samples[0]?.timestamp);
        const last = Number(samples.at(-1)?.timestamp);
        const duration = samples.length > 1 && Number.isFinite(first) && Number.isFinite(last)
            ? (last - first) / (samples.length - 1)
            : 0;
        const seconds = duration > 0 ? duration : range === "1h" ? 600 : 3600;
        return samples.map((sample) => ({
            ...sample,
            rx_mb: sampleValue(sample, "rx_bps") === null ? null : (sample.rx_bps * seconds) / 8 / 1048576,
            tx_mb: sampleValue(sample, "tx_bps") === null ? null : (sample.tx_bps * seconds) / 8 / 1048576,
        }));
    }

    async function loadTraffic() {
        const { gatewayId, portId } = state.activePort;
        const range = elements.trafficRange.value;
        state.activeTrafficRange = range;
        elements.chartStatus.textContent = "Loading traffic data.";
        try {
            const result = await requestJson(
                `/wan-dashboard/api/gateways/${encodeURIComponent(gatewayId)}/ports/${encodeURIComponent(portId)}/traffic?range=${range}`,
            );
            const samples = Array.isArray(result.data) ? result.data : [];
            const rateSamples = samples.map((sample) => ({
                ...sample,
                rx_mbps: sampleValue(sample, "rx_bps") === null ? null : sample.rx_bps / 1000000,
                tx_mbps: sampleValue(sample, "tx_bps") === null ? null : sample.tx_bps / 1000000,
            }));
            renderChart(elements.chartRate, rateSamples, [
                { field: "rx_mbps", label: "RX (Download)", className: "rx-line" },
                { field: "tx_mbps", label: "TX (Upload)", className: "tx-line" },
            ]);
            renderChart(elements.chartData, transferredSamples(samples, range), [
                { field: "rx_mb", label: "Receive MB", className: "rx-line" },
                { field: "tx_mb", label: "Transmit MB", className: "tx-line" },
            ]);
            elements.chartStatus.textContent = result.notice || `${samples.length} samples loaded.`;
        } catch (error) {
            elements.chartRate.replaceChildren(node("p", error.message, "wan-status"));
            elements.chartData.replaceChildren();
            elements.chartStatus.textContent = error.message;
        }
    }

    function showTraffic(button) {
        state.activePort = {
            gatewayId: button.dataset.gatewayId,
            portId: button.dataset.portId,
            gatewayName: button.dataset.gatewayName,
            portName: button.dataset.portName,
        };
        document.getElementById("wan-chart-title").textContent =
            `${state.activePort.gatewayName} - ${state.activePort.portName}`;
        elements.trafficRange.value = state.activeTrafficRange;
        elements.chartModal.hidden = false;
        loadTraffic();
    }

    function addMetric(container, label, value, unit = "") {
        const card = node("div", undefined, "wan-insight-metric");
        card.append(node("span", label));
        card.append(node("strong", value === null || value === undefined ? "Unavailable" : `${value}${unit}`));
        container.append(card);
    }

    function insightChart(title, rows, series) {
        const section = node("section");
        section.append(node("h3", title));
        const chart = node("div", undefined, "wan-chart");
        renderChart(chart, rows, series);
        section.append(chart);
        return section;
    }

    function impactedNames(interfaces) {
        return interfaces
            .map((item) =>
                typeof item === "string"
                    ? item
                    : item.interface_name || item.port_name || item.port_id || item.name || item.interface,
            )
            .filter(Boolean);
    }

    function appendInsightCharts(container, rows, health) {
        const charts = node("div", undefined, "wan-insights-charts");
        charts.append(
            insightChart("Hourly receive and transmit", rows, [
                { field: "rx_bps", label: "Average RX", className: "rx-line" },
                { field: "max_rx_bps", label: "Peak RX", className: "peak-rx-line" },
                { field: "tx_bps", label: "Average TX", className: "tx-line" },
                { field: "max_tx_bps", label: "Peak TX", className: "peak-tx-line" },
            ]),
            insightChart("Link health", rows, [
                { field: "avg_jitter_ms", label: "Jitter", className: "jitter-line" },
                { field: "avg_latency_ms", label: "Latency", className: "latency-line" },
            ]),
            insightChart("Packet loss", rows, [
                { field: "avg_loss_pct", label: "Loss", className: "loss-line" },
            ]),
        );
        const trendRows = health.trend.map((sample) => ({
            timestamp: sample.timestamp,
            sle_pct: sample.pct,
        }));
        charts.append(
            insightChart("Application health trend", trendRows, [
                { field: "sle_pct", label: "Application health", className: "rx-line" },
            ]),
        );
        container.append(charts);
    }

    async function loadInsights() {
        const { gatewayId, portId } = state.activePort;
        const range = elements.insightRange.value;
        state.activeInsightRange = range;
        elements.insightContent.replaceChildren(node("p", "Loading WAN Insights.", "wan-muted"));
        try {
            const result = await requestJson(
                `/wan-dashboard/api/gateways/${encodeURIComponent(gatewayId)}/ports/${encodeURIComponent(portId)}/insights?range=${range}`,
            );
            const data = result.data || {};
            const rows = Array.isArray(data.hourly) ? data.hourly : [];
            const latest = rows.at(-1) || {};
            const health = data.application_health || {};
            const impacts = Array.isArray(health.impacted_interfaces) ? health.impacted_interfaces : [];
            elements.insightContent.replaceChildren();
            addMetric(elements.insightContent, "Average receive", latest.rx_bps, " bps");
            addMetric(elements.insightContent, "Peak receive", latest.max_rx_bps, " bps");
            addMetric(elements.insightContent, "Average transmit", latest.tx_bps, " bps");
            addMetric(elements.insightContent, "Peak transmit", latest.max_tx_bps, " bps");
            addMetric(elements.insightContent, "Jitter", latest.avg_jitter_ms, " ms");
            addMetric(elements.insightContent, "Latency", latest.avg_latency_ms, " ms");
            addMetric(elements.insightContent, "Loss", latest.avg_loss_pct, "%");
            addMetric(
                elements.insightContent,
                "Application Health",
                health.summary_pct,
                "%",
            );
            addMetric(elements.insightContent, "SLE threshold", health.threshold_pct, "%");
            addMetric(elements.insightContent, "Impacted interfaces", impacts.length);
            appendInsightCharts(elements.insightContent, rows, {
                ...health,
                trend: Array.isArray(health.trend) ? health.trend : [],
            });
            const names = impactedNames(impacts);
            if (names.length) elements.insightContent.append(node("p", `Impacted: ${names.join(", ")}`, "wan-muted"));
            elements.insightContent.append(
                node("p", result.notice || `${rows.length} hourly samples loaded.`, "wan-muted"),
            );
            elements.portExport.href =
                `/wan-dashboard/api/gateways/${encodeURIComponent(gatewayId)}/ports/${encodeURIComponent(portId)}/hourly/export?range=${range}`;
        } catch (error) {
            elements.insightContent.replaceChildren(node("p", error.message, "wan-status"));
        }
    }

    function showInsights(button) {
        state.activePort = {
            gatewayId: button.dataset.gatewayId,
            portId: button.dataset.portId,
        };
        elements.insightRange.value = state.activeInsightRange;
        elements.insightModal.hidden = false;
        loadInsights();
    }

    function peerRow(peer) {
        const row = document.createElement("tr");
        const status = peer.up === true ? "Up" : peer.up === false ? "Down" : "Unavailable";
        const values = [
            status, peer.is_active === true ? "Active" : "Standby",
            peer.vpn_name, peer.peer_router_name, peer.peer_port_id, peer.type,
            peer.latency === null || peer.latency === undefined ? null : `${peer.latency} ms`,
            peer.loss === null || peer.loss === undefined ? null : `${peer.loss}%`,
            peer.jitter === null || peer.jitter === undefined ? null : `${peer.jitter} ms`,
            peer.mos, peer.uptime, peer.mtu, peer.hop_count,
        ];
        for (const value of values) detailCell(row, value);
        return row;
    }

    function averagePeerMetric(peers, field, suffix, digits = 1) {
        const values = peers.map((peer) => sampleValue(peer, field)).filter((value) => value !== null);
        if (!values.length) return "Unavailable";
        const average = values.reduce((total, value) => total + value, 0) / values.length;
        return `${average.toFixed(digits)}${suffix}`;
    }

    function showPeerPaths(button) {
        const peers = state.peersByPort[button.dataset.portId] || [];
        const upCount = peers.filter((peer) => peer.up === true).length;
        const activeCount = peers.filter((peer) => peer.is_active === true).length;
        document.getElementById("wan-peer-title").textContent =
            `${button.dataset.gatewayName} - ${button.dataset.portName}`;
        elements.peerSummary.replaceChildren(
            node("span", `${peers.length} paths`),
            node("span", `${upCount} up`),
            node("span", `${activeCount} active`),
            node("span", `Avg latency ${averagePeerMetric(peers, "latency", " ms")}`),
            node("span", `Avg loss ${averagePeerMetric(peers, "loss", "%", 2)}`),
            node("span", `Avg MOS ${averagePeerMetric(peers, "mos", "", 1)}`),
        );
        elements.peerContent.replaceChildren();
        if (!peers.length) {
            elements.peerContent.append(node("p", "No VPN peer paths are available.", "wan-muted"));
        } else {
            elements.peerContent.append(peerTable(peers));
        }
        elements.peerModal.hidden = false;
    }

    function peerTable(peers) {
        const table = node("table", undefined, "table table-sm wan-peer-table");
        const headings = [
            "Status", "Activity", "VPN", "Peer router", "Peer port", "Type", "Latency",
            "Loss", "Jitter", "MOS", "Uptime", "MTU", "Hops",
        ];
        const header = document.createElement("thead");
        const headingRow = document.createElement("tr");
        for (const heading of headings) {
            const cell = node("th", heading, "text-nowrap");
            cell.scope = "col";
            headingRow.append(cell);
        }
        header.append(headingRow);
        const body = document.createElement("tbody");
        for (const peer of peers) body.append(peerRow(peer));
        table.append(header, body);
        return table;
    }

    function updateExportLink() {
        const query = new URLSearchParams();
        if (elements.siteFilter.value) query.set("site_id", elements.siteFilter.value);
        if (elements.search.value.trim()) query.set("search", elements.search.value.trim());
        document.getElementById("wan-gateway-export").href =
            `/wan-dashboard/api/gateways/export${query.size ? `?${query}` : ""}`;
    }

    elements.rows.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-action]");
        const row = event.target.closest('tr[data-testid="wan-gateway-row"]');
        if (button?.dataset.action === "details" && row) expandGateway(row);
        if (button?.dataset.action === "traffic") showTraffic(button);
        if (button?.dataset.action === "insights") showInsights(button);
        if (button?.dataset.action === "peers") showPeerPaths(button);
    });
    elements.siteFilter.addEventListener("change", () => {
        renderGateways();
        updateExportLink();
    });
    elements.search.addEventListener("input", () => {
        renderGateways();
        updateExportLink();
    });
    elements.trafficRange.addEventListener("change", loadTraffic);
    elements.insightRange.addEventListener("change", loadInsights);
    document.getElementById("wan-refresh").addEventListener("click", loadOverview);
    document.getElementById("wan-modal-close").addEventListener("click", () => {
        elements.chartModal.hidden = true;
    });
    document.getElementById("wan-insights-close").addEventListener("click", () => {
        elements.insightModal.hidden = true;
    });
    document.getElementById("wan-peer-close").addEventListener("click", () => {
        elements.peerModal.hidden = true;
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            elements.chartModal.hidden = true;
            elements.insightModal.hidden = true;
            elements.peerModal.hidden = true;
        }
    });

    loadOverview();
})();
