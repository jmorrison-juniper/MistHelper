# Research: Web Portal Interface

**Feature**: 005-web-portal | **Date**: 2026-03-04

## Research Questions

### R1: Real-Time Communication — WebSocket vs SSE vs Polling

**Context**: FR-023 specifies "WebSocket connections for real-time bidirectional communication." The clarification explicitly chose WebSocket over SSE/polling. However, technical constraints affect feasibility.

**Findings**:

| Transport | Server→Client | Client→Server | Gunicorn Compat | Python 3.13 |
|-----------|--------------|---------------|-----------------|-------------|
| WebSocket (Flask-SocketIO + eventlet) | Yes | Yes | Needs eventlet worker | **Deprecated** — eventlet maintainers say "new usages heavily discouraged" |
| WebSocket (Flask-SocketIO + gevent) | Yes | Yes | Needs gevent worker | Works (not free-threaded mode) |
| WebSocket (Flask-SocketIO threading mode) | Via long-poll | Via long-poll | gthread workers | **Works** — no eventlet/gevent needed |
| SSE (Server-Sent Events) | Yes (native) | N/A (use HTTP POST) | gthread workers | **Works** — zero extra deps |
| AJAX Polling | Yes (interval) | N/A (use HTTP POST) | Any worker | **Works** — simplest |

**Actual use cases analyzed**:
- Server→Client: operation progress (%), status changes (running→complete→failed), log streaming → **one-directional push**
- Client→Server: start operation (POST /api/operations/start), cancel operation (POST /api/operations/cancel) → **standard HTTP requests**

No actual bidirectional messaging is needed. The "full-duplex" WebSocket was chosen for future flexibility, not because current features require it.

**Decision**: **SSE (Server-Sent Events) for server→client push + standard HTTP POST for client→server actions**

**Rationale**:
1. SSE is natively supported by all target browsers (Chrome, Firefox, Edge) via `EventSource` API
2. Zero additional dependencies — Flask can stream responses natively
3. Works with standard Gunicorn gthread workers without eventlet/gevent
4. Avoids deprecated eventlet dependency and gevent free-threading concerns
5. Automatic reconnection built into EventSource specification
6. If true WebSocket is needed later, Flask-SocketIO threading mode can be added without architecture changes

**Alternatives considered**:
- Flask-SocketIO + gevent: Works on 3.13 today but gevent explicitly warns against free-threaded mode. Adding gevent as a dependency introduces build complexity (C extensions, greenlet). Overkill for 5 concurrent users.
- Flask-SocketIO threading mode (long-polling): Provides Socket.IO API but uses HTTP long-polling underneath — same as SSE but heavier. Adds `flask-socketio` and `python-socketio` dependencies for no functional benefit.
- AJAX polling: Simpler but adds 1-5 second latency between updates. Poor UX for progress monitoring.

**Spec Impact**: FR-023 wording changes from "WebSocket connections" to "Server-Sent Events (SSE) for real-time server-to-client communication." The external behavior (real-time progress updates in browser) is identical. Client→server communication uses standard HTTP requests.

---

### R2: Gunicorn Worker Configuration

**Context**: Gunicorn serves the Flask portal. Need to determine worker type, count, and threading model given the `apisession` sharing constraint.

**Findings**:

The `apisession` (mistapi.APISession) is a module-level global in MistHelper.py (line 2191). It holds authentication state (API token, session cookies). Key constraints:
- Each Gunicorn worker is a **separate process** (fork). Forked `apisession` objects diverge after fork — token refreshes in one worker don't propagate to others.
- `mistapi.APISession` uses `requests.Session` internally, which is thread-safe for concurrent requests but not process-safe.
- The portal is an internal NOC tool with 1-5 concurrent users — not a high-traffic web service.

**Decision**: **Single worker with 4 threads** — `gunicorn -w 1 -k gthread --threads 4`

**Rationale**:
1. Single process ensures one `apisession` instance — no token divergence
2. 4 threads handle concurrent browser requests (page loads, SSE streams, API calls)
3. gthread worker class is stable on Python 3.13 with no extra dependencies
4. Matches the workload profile (5 concurrent sessions, not 5000)
5. SSE streams require persistent connections — threads handle this naturally

**Alternatives considered**:
- Multiple sync workers (`-w 4`): Each worker forks `apisession`. Token refresh divergence causes auth failures. Would need per-worker session initialization from ENV.
- Async workers (eventlet/gevent): Discussed in R1 — compatibility concerns on 3.13.
- Uvicorn (ASGI): Unnecessary without WebSocket. Adds dependency for no benefit.

---

### R3: Dual-Process Container Startup

**Context**: Container must run both sshd (port 2200) and Gunicorn (port 8055). Current `start.sh` runs only `exec /usr/sbin/sshd -D`.

**Findings**:

| Approach | Deps | Complexity | Auto-restart | Signal handling |
|----------|------|-----------|--------------|-----------------|
| Shell script (bg + fg) | None | Low | Manual | trap needed |
| supervisord | ~10MB | Medium | Built-in | Built-in |
| s6-overlay | ~2MB | Medium | Built-in | Built-in |
| Two containers | Docker Compose | High | Per-container | Per-container |

**Decision**: **Shell script with background Gunicorn + foreground sshd**

**Rationale**:
1. No additional dependencies in the container image
2. sshd remains PID 1 via `exec` — proper signal handling on container stop
3. Gunicorn PID captured for explicit cleanup via `trap`
4. If Gunicorn crashes, sshd is preserved — SSH access maintained for debugging
5. Consistent with the existing container pattern (minimal, single-purpose images)

**Pattern**:
```bash
# 1. Start Gunicorn in background, save PID
gunicorn ... &
GUNICORN_PID=$!

# 2. Trap SIGTERM to kill both processes
trap "kill $GUNICORN_PID; exit 0" SIGTERM SIGINT

# 3. Start sshd as foreground (PID 1 via exec not possible with trap — use wait)
/usr/sbin/sshd -D &
SSHD_PID=$!
wait $SSHD_PID
```

Note: Cannot use `exec` for sshd when trap is needed. Instead, both run as background processes with `wait` to keep the script alive and responding to signals.

**Upgrade path**: If a third service is added (e.g., Celery worker), switch to supervisord.

---

### R4: Flask App Factory and Dependency Injection

**Context**: The Flask portal needs access to `apisession` and `menu_actions` from MistHelper.py. How should these be passed?

**Findings**:

The existing `maps_manager.py` pattern provides a proven template:
- `MapsManager.__init__(self, api_session, organization_id)` receives dependencies as constructor arguments (line 251)
- Never imports from MistHelper.py
- MistHelper.py's `MapsManagerLauncher` creates the MapsManager and passes `apisession` (line 50794)

The `menu_actions` dictionary is defined at line 50499 and contains ~120 entries mapping string keys to `(function, description)` tuples. Each function captures closure variables (like `apisession`) from the surrounding scope.

**Decision**: **Inject dependencies at app factory call time, stored on Flask app config**

**Pattern**:
```python
# web_portal/app.py
class WebPortalApp:
    @staticmethod
    def create_app(apisession, menu_actions, org_id):
        app = Flask(__name__)
        app.config['APISESSION'] = apisession
        app.config['MENU_ACTIONS'] = menu_actions
        app.config['ORG_ID'] = org_id
        # ... register blueprints, load ENV config
        return app
```

**Integration point in MistHelper.py**:
```python
# New menu option or startup hook
from web_portal.app import WebPortalApp
app = WebPortalApp.create_app(apisession, menu_actions, org_id)
```

**Rationale**:
1. Follows the proven `maps_manager.py` injection pattern
2. Avoids circular imports (web_portal never imports MistHelper)
3. `current_app.config['APISESSION']` available in all route handlers
4. Thread-safe: single `apisession` shared across gthread workers within one process

---

### R5: Bootstrap 5 — Bundled vs CDN

**Context**: The portal needs Bootstrap 5 for responsive, accessible UI. Container may operate in air-gapped environments.

**Findings**:

Known deployment constraints from copilot-instructions.md:
- Corporate Zscaler proxy intercepts SSL and blocks some HTTPS requests (documented 403 errors for ghcr.io)
- Air-gapped NOC environments have no internet access
- The existing `maps_manager.py` loads Plotly from CDN (line 7750) — this is a documented fragility

| Approach | Size (gzipped) | Offline | Maintenance |
|----------|---------------|---------|-------------|
| CDN | 0 bytes in image | Fails offline | Auto-updates (risk) |
| Bundled | ~50 KB | Works | Manual updates |
| CDN + local fallback | ~50 KB | Works + fast online | Complex |

**Decision**: **Bundle Bootstrap 5 as static files**

Files to bundle:
- `bootstrap.min.css` (~25 KB gzipped) — full CSS framework
- `bootstrap.bundle.min.js` (~25 KB gzipped) — JS + Popper.js for dropdowns/modals

**Rationale**:
1. Guarantees portal works in air-gapped and proxy-filtered environments
2. Eliminates external dependency for core functionality
3. 50 KB is negligible in a ~200 MB container image
4. Version pinned — no unexpected breaking changes from CDN updates
5. Placed in `static/vendor/` to separate from project code

---

### R6: Plotly.js Without Dash — Map Viewer Absorption

**Context**: The existing `maps_manager.py` is a 9,586-line Dash/Plotly application. The spec says to absorb it into the Flask portal and retire standalone Dash. Key question: can Plotly.js work without Dash?

**Findings**:

Yes — `maps_manager.py` already contains a **Flask-only viewer** (lines 7722-9189) that renders interactive maps without Dash:
- `_launch_flask_viewer()` (line 7722) creates a standalone Flask app
- Serves a Jinja2 template embedding Plotly.js directly
- Uses `fetch()` API to get map data from Flask endpoints
- Uses `Plotly.react()` for client-side rendering
- No Dash callbacks — all interaction handled in JavaScript

This Flask viewer is the **exact blueprint** for the portal's map page. The Dash layer is unnecessary.

| Component | Size | Needed for portal? |
|-----------|------|--------------------|
| `plotly.min.js` (full) | 3.5 MB | Yes — map rendering |
| `dash` Python package | ~15 MB installed | **No** — Flask viewer exists |
| `plotly` Python package | ~25 MB installed | Partial — only for server-side figure generation |

**Decision**: **Bundle `plotly.min.js` as a static vendor file. Keep `plotly` Python package for server-side map data generation. Remove `dash` dependency.**

**Rationale**:
1. The Flask viewer pattern in maps_manager.py proves Dash is not needed for interactive maps
2. Removing `dash` from requirements.txt reduces container image by ~15 MB and eliminates a transitive dependency tree
3. `plotly` Python package is still needed for server-side figure generation (creating map layouts, computing trace data)
4. Client-side rendering via `Plotly.react()` is more responsive than Dash's callback-based approach
5. 3.5 MB for plotly.min.js is loaded once and cached by the browser

**Map viewer absorption strategy**:
1. Extract the Flask viewer HTML template from maps_manager.py (lines 7750-8706)
2. Extract Flask API endpoints for map data retrieval
3. Create `web_portal/routes/maps.py` with these endpoints
4. Create `web_portal/templates/map_viewer.html` with the Plotly.js template
5. `maps_manager.py` continues to provide the `MapsManager` class (API interactions, map data processing) — it becomes a pure library class, no longer a standalone app
6. Remove `if __name__ == "__main__"` block and Dash-specific code from maps_manager.py

---

### R7: Dependency Changes

**Context**: What packages need to be added/removed/modified in requirements.txt?

**Decision**:

| Action | Package | Reason |
|--------|---------|--------|
| **Add** | `gunicorn>=22.0.0` | WSGI server for Flask portal |
| **Keep** | `plotly>=5.14.0` | Server-side map figure generation |
| **Keep** | `matplotlib>=3.5.0` | Used elsewhere in MistHelper |
| **Keep** | `pillow>=9.0.0` | Image processing for maps |
| **Keep** | `kaleido>=0.2.1` | Static image export for Plotly figures |
| **Remove** | `dash>=2.9.0` | Replaced by Flask portal + Plotly.js client-side |
| **No change** | All other packages | Not affected by web portal |

Note: `Flask` is already a transitive dependency via Dash. After Dash removal, Flask becomes a direct dependency and must be explicitly listed:

| **Add** | `Flask>=3.0.0` | Web framework (was transitive via Dash) |

---

### R8: Security Implementation

**Context**: FR-018 through FR-021 require CSRF, XSS prevention, CSP headers, and IP allowlisting.

**Findings**:

| Requirement | Implementation | Dependencies |
|-------------|---------------|--------------|
| CSRF tokens (FR-018) | Flask-WTF provides CSRF protection via `CSRFProtect(app)` | `flask-wtf` (new dep) |
| XSS prevention (FR-019) | Jinja2 auto-escaping (enabled by default in Flask) | None (built-in) |
| CSP headers (FR-020) | Flask `@app.after_request` decorator | None (built-in) |
| IP allowlisting (FR-021) | Flask `@app.before_request` with CIDR matching | `ipaddress` (stdlib) |

**Decision**: **Add `flask-wtf` for CSRF. Implement CSP and IP allowlisting as custom middleware classes.**

**Rationale**:
1. Flask-WTF is the standard CSRF solution for Flask — well-maintained, minimal footprint
2. Jinja2 auto-escaping is already enabled by default — just verify no `|safe` filters are used without validation
3. CSP headers are a simple `after_request` hook — no external dependency needed
4. IP allowlisting uses Python's stdlib `ipaddress.ip_network()` for CIDR parsing — no external dependency

**Updated dependency additions**:
| **Add** | `flask-wtf>=1.2.0` | CSRF protection |

---

## Summary of All Decisions

| # | Question | Decision | Key Rationale |
|---|----------|----------|---------------|
| R1 | Real-time communication | SSE + HTTP POST | No actual bidirectional need; avoids eventlet/gevent 3.13 issues |
| R2 | Gunicorn workers | 1 worker, 4 threads (gthread) | Single apisession, low traffic, thread-safe |
| R3 | Dual-process container | Shell script (bg + fg) | No extra deps, matches existing pattern |
| R4 | Dependency injection | App factory with injected refs | Follows maps_manager.py pattern, avoids circular imports |
| R5 | Bootstrap 5 | Bundled static files | Air-gap/proxy compatibility |
| R6 | Map viewer | Plotly.js client-side + remove Dash | Flask viewer already exists in maps_manager.py |
| R7 | Dependencies | +gunicorn, +Flask, +flask-wtf, -dash | Minimal additions, one removal |
| R8 | Security | flask-wtf CSRF + built-in CSP/XSS/IP | Standard Flask security patterns |

## Spec Amendments Required

1. **FR-023**: Change "WebSocket connections" to "Server-Sent Events (SSE)" — behavior unchanged for user, implementation simplified
2. **Dependencies**: Remove Flask-SocketIO, add flask-wtf
3. **Architecture**: Single Gunicorn worker (not multiple) — document in deployment notes
