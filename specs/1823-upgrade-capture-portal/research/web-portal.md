# Web Portal Technical Reference (Feature 1823)

Research date: 2026-08-19.
Branch: `feat/1807-simple-endpoint-exporter`.
Scope: read-only study of the existing web portal. No source code changed.

## Purpose

Feature 1823 adds a second Gunicorn application on its own port. The new
application must serve many users at the same time. The existing portal runs
one Gunicorn worker because all of its state lives in process memory. This
document records what the existing portal does, why it needs one worker, and
which parts the new application must not copy.

## How to read this document

Every finding shows a source location as `file:line`. Statements that come from
inference, and not from a direct read, carry the label **Inference**. The
research did not open `.env`. No value from `.env` appears here.

---

## 1. Application factory and blueprints

### 1.1 The factory

`WebPortalApp.create_app` builds the Flask application. The signature is at
`web_portal/app.py:26-31` and takes three arguments: `apisession`,
`menu_actions`, and `org_id`.

The factory calls six helpers in a fixed order (`web_portal/app.py:38-45`):

1. `_load_portal_config` (`web_portal/app.py:38`)
2. `_inject_dependencies` (`web_portal/app.py:39`)
3. `_setup_theme_manager` (`web_portal/app.py:40`)
4. `_apply_security` (`web_portal/app.py:41`)
5. `_register_blueprints` (`web_portal/app.py:42`)
6. `_register_context_processor` (`web_portal/app.py:43`)

The factory then calls `InputInterceptor.install()` (`web_portal/app.py:45`).
That call patches a Python builtin for the whole process. Section 3 covers the
effect.

The factory sets `app.secret_key` from the configuration map
(`web_portal/app.py:65`). Section 3 explains why that line blocks several
workers.

The factory creates the event bus and starts its heartbeat thread
(`web_portal/app.py:84-86`). It stores the bus in `app.config["EVENT_BUS"]`.

The factory reads the data directory from the environment
(`web_portal/app.py:81-82`).

### 1.2 Registered blueprints

`_register_blueprints` registers five blueprints (`web_portal/app.py:113-117`):

| Blueprint | Module | URL prefix |
| --- | --- | --- |
| `dashboard` | `web_portal/routes/dashboard.py:11` | none (root) |
| `data` | `web_portal/routes/data.py:9` | none |
| `operations` | `web_portal/routes/operations.py` | none |
| `maps` | `web_portal/routes/maps.py` | none |
| `settings` | `web_portal/routes/settings.py:8` | none |

No blueprint uses a `url_prefix`. Each route declares its own full path. The
theme API lives at `/api/themes` (`web_portal/routes/settings.py:11`).

### 1.3 Orphan blueprint

`webhook_bp` exists at `web_portal/routes/webhooks.py:16`. It declares a route
at `/api/webhook` (`web_portal/routes/webhooks.py:32`). The factory never
imports it and never registers it (`web_portal/app.py:105-117`). The blueprint
is dead code today.

Two further problems sit inside that file. It verifies a signature with
HMAC-SHA256 (`web_portal/routes/webhooks.py:19-24`). It reads an application
config key named `DB_ROUTER` (`web_portal/routes/webhooks.py:29`). Nothing in
the factory sets `DB_ROUTER`. **Inference**: the blueprint would fail at
request time if someone registered it without more work.

### 1.4 What a new blueprint must do

A new blueprint must follow the same pattern. It must define full route paths
or set an explicit `url_prefix`. It must register inside a factory. Section 5
lists the security duties.

---

## 2. Launch paths and the Gunicorn command

The portal has two launch paths. Only one uses Gunicorn.

### 2.1 Container path (Gunicorn)

`container/scripts/start.sh` starts the portal in the container. The port
default is at `container/scripts/start.sh:52`:

```bash
WEB_PORT="${WEB_PORT:-8055}"
```

The exact command is at `container/scripts/start.sh:56-63`:

```bash
su - misthelper -c "cd /app && gunicorn wsgi:app \
    --bind 0.0.0.0:${WEB_PORT} \
    --workers 1 \
    --worker-class gthread \
    --threads 4 \
    --timeout 120 \
    --access-logfile /app/data/portal_access.log \
    --error-logfile /app/data/portal_error.log" &
```

The script keeps the process identifier at `container/scripts/start.sh:64`. A
`cleanup` trap stops the process at `container/scripts/start.sh:67-75`. The
script also starts `sshd` (`container/scripts/start.sh:78-79`) and then waits
for the first child to exit (`container/scripts/start.sh:82`).

The container image sets the same port and exposes it. See `Containerfile:105`
(`ENV WEB_PORT=8055`) and `Containerfile:111` (`EXPOSE 2200 8055`). The image
entry point is `Containerfile:118` (`CMD ["/start.sh"]`).

The WSGI target is `wsgi:app`. `wsgi.py:3-4` records the same command in its
docstring.

### 2.2 Command-line path (Flask development server)

`MistHelper.py` accepts a `--web-portal` flag (`MistHelper.py:5039-5045`). The
dispatch entry is at `MistHelper.py:5704`. The mode function is at
`MistHelper.py:5691-5694`. The launcher is `_launch_web_portal`
(`MistHelper.py:4848-4870`). The host default is at `MistHelper.py:4862`.

`_run_web_portal_server` (`MistHelper.py:4834-4845`) calls the Flask
development server in both of its branches. It never calls Gunicorn. Inside a
container it forces `debug=False`.

**Result**: the command-line path never uses Gunicorn. Only the container
start script uses Gunicorn.

### 2.3 Why one worker is required today

`wsgi.py` builds process-wide state at import time
(`wsgi.py:98-105`):

- `apisession, org_id = _bootstrap_api_session()` (`wsgi.py:98`)
- `menu_actions = _load_menu_actions(apisession, org_id)` (`wsgi.py:99`)
- `app = WebPortalApp.create_app(...)` (`wsgi.py:101-105`)

`_bootstrap_api_session` creates and logs in one `mistapi.APISession`
(`wsgi.py:40-41` and `wsgi.py:44-45`). `_load_menu_actions` then writes to
MistHelper module globals (`wsgi.py:82-88`):

```python
MistHelper.apisession = wsgi_session
# Apply timeout adapter so API calls don't hang indefinitely
MistHelper._configure_session_timeout(wsgi_session)
if wsgi_org_id:
    MistHelper.org_id = wsgi_org_id
    os.environ["ORG_ID"] = wsgi_org_id
```

Several workers would each hold a separate authenticated session and a separate
copy of these globals. A token refresh in one worker would not reach the other
workers. The project already recorded this decision. See
`specs/005-web-portal/research.md:46-57`, decision R2.

Three further blockers exist. Each one alone forces a single worker:

1. The run map is per process (`web_portal/services/operation.py:313`).
2. The event bus subscriber map is per process
   (`web_portal/services/event_bus.py:29`).
3. The session secret key is random per process
   (`web_portal/services/config.py:56`).

### 2.4 What the new application must do

The new application must not import an authenticated API session at module
scope. It must create a session per worker, or per request, or it must read
data that another process already wrote. It must not write to MistHelper module
globals.

---

## 3. Process-level mutable state

The table lists every piece of state that lives in process memory. The last
column names the replacement that would let several workers run.

| State | Location | Survives several workers | Replacement |
| --- | --- | --- | --- |
| `apisession` global | `wsgi.py:98` | No. Each worker logs in on its own. | Per-worker session, or a shared token store |
| `menu_actions` global | `wsgi.py:99` | Partly. The map is read-only after build, but each worker rebuilds it. | Keep per worker. The map is not mutated. |
| `MistHelper.apisession` and `MistHelper.org_id` | `wsgi.py:83-88` | No. Cross-module globals diverge per worker. | Pass the session as an argument |
| `app.secret_key` from `uuid.uuid4()` | `web_portal/services/config.py:56` | **No. This breaks sessions and CSRF across workers.** | A fixed secret from the environment |
| `OperationExecutor._runs` | `web_portal/services/operation.py:313` | No. Worker A cannot see a run started in worker B. | Shared store (Redis or SQLite) |
| `OperationExecutor._lock` | `web_portal/services/operation.py:314` | No. A thread lock guards one process only. | Cross-process lock |
| `ThreadPoolExecutor` | `web_portal/services/operation.py:316-318` | No. Each worker gets its own pool. Total workers multiply. | Bounded shared queue, or per-worker cap |
| `PARAMETER_REGISTRY` | `web_portal/services/operation.py:291` | Yes. Built once at import and then read only. | No change needed |
| `PortalEventBus._subscribers` | `web_portal/services/event_bus.py:29` | No. A client subscribes in one worker only. | Shared broker, or short polling |
| `PortalEventBus._lock` | `web_portal/services/event_bus.py:30` | No. Same reason as the run lock. | Same as above |
| Heartbeat thread | `web_portal/services/event_bus.py:110-124` | No. Each worker starts its own thread. | Single scheduler, or drop the bus |
| `InputInterceptor._original_input`, `_local`, `_installed` | `web_portal/services/input_hook.py:23-25` | No. The patch applies per process. | Do not patch `input` in the new application |
| `builtins.input` patch | `web_portal/services/input_hook.py:33` | No. Process-global side effect. | Same as above |
| `_start_time` for uptime | `web_portal/routes/dashboard.py:14` | No. Each worker reports its own uptime. | Read the container start time |
| Executor singleton in app config | `web_portal/routes/operations.py:182-195` | No. `current_app.config` is per process. | Shared store |

Two notes on the table:

- `web_portal/routes/data.py` holds no module-level mutable state. The only
  module-level name is the blueprint (`web_portal/routes/data.py:9`).
- `web_portal/routes/maps.py` and `web_portal/routes/settings.py` read
  everything from `current_app.config`. They add no new state.

### 3.1 The secret key is the first blocker

`web_portal/services/config.py:56` reads:

```python
"secret_key": os.environ.get("PORTAL_SECRET_KEY") or str(uuid.uuid4()),
```

If `PORTAL_SECRET_KEY` is absent, each worker picks a different random key. A
cookie signed by worker A fails in worker B. CSRF tokens fail in the same way.
The new application must require a fixed secret from the environment. The
research did not read `.env`, so this document does not state whether
`PORTAL_SECRET_KEY` is set.

### 3.2 Log capture is not run-scoped

`_RunLogHandler` (`web_portal/services/operation.py:598`) attaches to the root
logger (`web_portal/services/operation.py:495-501`). Two runs in one process
capture each other's log lines. The new application must attach a handler with
a run filter, or it must write logs per run to separate files.

---

## 4. The stop mechanism

### 4.1 Where the file lives

The producer writes a sentinel file. See
`web_portal/services/operation.py:345-372`, and the key line at
`web_portal/services/operation.py:366`:

```python
stop_path = os.path.join(os.getcwd(), "stop_loop.txt")
```

The file name is `stop_loop.txt`. The directory is the process working
directory. In the container the working directory is `/app`
(`container/scripts/start.sh:56`).

### 4.2 Who consumes it

`src/config/config_utils.py:158-178` holds the consumer. The relevant lines are
`src/config/config_utils.py:169-176`:

```python
if os.path.exists("stop_loop.txt"):
    try:
        os.remove("stop_loop.txt")
    except OSError:
        pass
    logging.warning("Stop signal (stop_loop.txt) detected - operation stopped by user.")
    return True
```

The consumer tests a relative path. It deletes the file as soon as it sees it.

### 4.3 Is it safe for concurrent users

**No.** The mechanism fails for concurrent users in three ways:

1. The file carries no run identifier and no user identifier. Any loop that
   checks first consumes the signal.
2. One user's stop request cancels an unrelated user's operation.
3. SSH sessions in the same container share `/app` as a working directory
   (`container/scripts/start.sh:78-79`). A command-line loop can consume a
   stop signal that a portal user created.

The new application must use a per-run stop flag. A row in a shared store, or a
file named with the run identifier, would work. **Inference**: the second option
is the smaller change, because the loop code already tests a path.

---

## 5. Security middleware

`_apply_security` calls into `web_portal/services/config.py`. Four controls
exist.

### 5.1 Response headers

`web_portal/services/config.py:117-124` sets five headers on every response:

- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

The policy value is at `web_portal/services/config.py:100-106`:

```
default-src 'self'; script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline'; img-src 'self' data:;
connect-src 'self'
```

`X-Frame-Options: DENY` blocks every frame. `default-src 'self'` blocks every
external asset. A new page must not load a script, a stylesheet, a font, or an
image from another host.

### 5.2 CSRF protection

`web_portal/services/config.py:138-144` installs `CSRFProtect` from
`flask-wtf`. Every POST, PUT, PATCH, and DELETE needs a token. The base
template exposes the token in a meta tag (`web_portal/templates/base.html:6`).
The client reads it with `getCsrfToken()`
(`web_portal/static/js/portal.js:11-14`).

### 5.3 IP allow list

`web_portal/services/config.py:126-136` blocks a client that is outside the
allowed CIDR list. It calls `abort(403)`. The list comes from
`PORTAL_ALLOWED_IPS`. An empty value disables the check
(`web_portal/services/config.py:30`). The code trusts `X-Forwarded-For`
(`web_portal/services/config.py:146-151`).

### 5.4 Duties for a new blueprint

A new blueprint must:

1. Send the CSRF token with every state-changing request. Use the meta tag.
2. Serve every asset from the same origin. Vendor any new library.
3. Avoid an inline `<script src>` that points at a content delivery network.
4. Accept that inline `<script>` and inline `<style>` still work, because the
   policy allows `'unsafe-inline'` for both.
5. Never rely on an iframe.

**Inference**: the new application will need its own copy of these controls,
because they attach to a Flask application object and not to a blueprint.

---

## 6. The event bus and server-sent events

### 6.1 Numbers

`web_portal/services/event_bus.py` sets the limits:

- Maximum subscribers: `10` (`web_portal/services/event_bus.py:24`)
- Queue size per subscriber: `100` (`web_portal/services/event_bus.py:25`)
- Heartbeat interval: `30` seconds (`web_portal/services/event_bus.py:113`)
- Poll timeout inside `poll`: `35` seconds
  (`web_portal/services/event_bus.py:78`)
- Stale subscriber cutoff: `3600` seconds
  (`web_portal/services/event_bus.py:133`)

`subscribe` raises an error when the eleventh client arrives
(`web_portal/services/event_bus.py:53-54`). The message is
`Maximum SSE connections reached`.

### 6.2 The stream route

The stream endpoint is at `web_portal/routes/operations.py:85-131`. It polls
the bus with a 5-second timeout (`web_portal/routes/operations.py:109`). It
sets `Cache-Control: no-cache` and `X-Accel-Buffering: no`
(`web_portal/routes/operations.py:127-130`). The frame format helper is at
`web_portal/routes/operations.py:273-276`.

The browser helper opens an `EventSource`
(`web_portal/static/js/portal.js:104-125`). It listens for five event names:
`status`, `log`, `complete`, `error`, and `heartbeat`
(`web_portal/static/js/portal.js:109`).

### 6.3 Can the bus serve a 30-second status display for many users

**No.** Three limits block it:

1. The subscriber cap is 10 (`web_portal/services/event_bus.py:24`). The
   eleventh user gets an error.
2. Gunicorn runs 4 threads (`container/scripts/start.sh:60`). Each open stream
   holds a thread for its whole life. Five streams would starve the portal of
   request threads.
3. The subscriber map is per process
   (`web_portal/services/event_bus.py:29`). With several workers a client
   subscribes in one worker and misses events published in another worker.

### 6.4 Recommendation

For a 30-second status display, do not use this bus. Use a plain JSON endpoint
and let the browser poll it every 30 seconds. A poll costs one short request per
user per 30 seconds. It works with any number of workers. It needs no shared
broker.

If push is a hard requirement later, move the bus to Redis. The compose file
already runs Redis (`compose.yml:95`).

---

## 7. Theming and the ignore-file question

### 7.1 How a theme loads

The base template links a theme stylesheet by name
(`web_portal/templates/base.html:13-14`). The name comes from
`config.PORTAL.theme`. The template also injects the accent color into a CSS
custom property (`web_portal/templates/base.html:20-24`):

```html
<style>
    :root {
        --portal-accent: {{ config.PORTAL.accent_color }};
    }
</style>
```

The browser can swap the stylesheet at run time. `applyTheme` rewrites the
`href` of the `theme-css` element (`web_portal/static/js/portal.js:29-41`). It
saves the choice in `localStorage` under the key `misthelper-theme`
(`web_portal/static/js/portal.js:18` and `web_portal/static/js/portal.js:40`).
It also flips the Bootstrap attribute `data-bs-theme`
(`web_portal/static/js/portal.js:34-39`). The template hard-codes `dark` in the
`html` element (`web_portal/templates/base.html:2`), and the script corrects it
after load (`web_portal/static/js/portal.js:187`).

The theme menu loads from `/api/themes`
(`web_portal/static/js/portal.js:43-70`). That endpoint is in the settings
blueprint (`web_portal/routes/settings.py:11-24`).

### 7.2 Stylesheet discovery

`ThemeManager` (`web_portal/services/config.py:162`) scans a directory. The
scan is at `web_portal/services/config.py:197-215`. It globs `*.css`, removes
the suffix, and builds a display label. A name that is not in `DISPLAY_LABELS`
(`web_portal/services/config.py:169-173`) gets a title-cased label.

**Result**: a new theme needs no code change. Drop a `.css` file into the theme
directory and the menu shows it.

### 7.3 Every theme file

Four stylesheets exist under `web_portal/static/css`:

| File | Role |
| --- | --- |
| `web_portal/static/css/portal.css` | Shared layout and component rules |
| `web_portal/static/css/themes/dark.css` | Dark theme, the default |
| `web_portal/static/css/themes/light.css` | Light theme |
| `web_portal/static/css/themes/high-contrast.css` | High contrast theme |

`dark.css` defines about 17 custom properties at
`web_portal/static/css/themes/dark.css:8-27`. A new theme should define the
same property names.

### 7.4 The accent color

The default accent is `#0077B6` (`web_portal/services/config.py:27`). The
context processor uses a different fallback, `#0d6efd`
(`web_portal/app.py:119-133`). The two defaults do not match. **Inference**:
the second value is a copy of the Bootstrap primary color and is unreachable
whenever `_load_portal_config` runs first, which it always does
(`web_portal/app.py:38`).

### 7.5 Every occurrence of `#E20074`

The search found `#E20074` only in Markdown documentation. Every hit sits
inside a Mermaid diagram theme block. The canonical definition is at
`specs/016-mermaid-documentation-suite/contracts/theme-contract.md`.

**No portal stylesheet references `#E20074`.** No Python file sets it. No
template sets it. The color is a diagram color today, not a portal color.

### 7.6 Would an ignore file exclude a file whose name contains `t-mobile`

The answer is **not for every letter case**. Git ignore patterns are
case-sensitive by default. The same rule applies to `.dockerignore`.

`.gitignore:31-35` reads exactly:

```
*tmo*
*TMO*
*t-mobile*
*T-Mobile*
*T-MOBILE*
```

`.dockerignore:93-96` reads exactly:

```
*tmo*
*TMO*
*t-mobile*
*T-Mobile*
```

Findings:

1. A file named `t-mobile.css` matches `*t-mobile*`. Git excludes it. The build
   context excludes it. The file would never reach the container.
2. A file named `tmobile.css` matches `*tmo*`. Both files exclude it.
3. A file named `T-mobile.css` matches no pattern in either file. It would
   survive today. It is still a trap, because a later case-insensitive
   configuration would hide it.
4. `.gitignore` lists `*T-MOBILE*`. `.dockerignore` does not. The two lists
   differ.

**Recommendation**: do not put the string `tmo`, `TMO`, or `t-mobile` in any
new file name. Name a branded theme after its color or its purpose, for example
`magenta.css`. Set the brand name only inside the file content and inside
environment variables.

---

## 8. Configuration and the new port

### 8.1 The default settings map

`web_portal/services/config.py:24-31` holds `ENV_DEFAULTS`:

| Environment variable | Default value |
| --- | --- |
| `PORTAL_TITLE` | `MistHelper` |
| `PORTAL_LOGO_URL` | `/static/img/logo-default.svg` |
| `PORTAL_ACCENT_COLOR` | `#0077B6` |
| `PORTAL_THEME` | `dark` |
| `WEB_PORT` | `8055` |
| `PORTAL_ALLOWED_IPS` | empty string |

Two more variables act outside that map:

- `PORTAL_SECRET_KEY` (`web_portal/services/config.py:56`)
- `DATA_DIR` (`web_portal/app.py:81-82`)

### 8.2 Port selection

`_validate_port` (`web_portal/services/config.py:66-75`) accepts an integer from
1024 to 65535. Any other value falls back to `8055`.

The container sets `WEB_PORT=8055` in three places: `Containerfile:105`,
`compose.yml:26`, and the shell default at `container/scripts/start.sh:52`.

### 8.3 Ports already in use

`compose.yml` publishes these ports:

| Port | Service | Location |
| --- | --- | --- |
| 2200 | SSH | `compose.yml:11` |
| 8055 | Web portal | `compose.yml:13` |
| 8529 | ArangoDB | `compose.yml:70` |
| 6379 | Redis | `compose.yml:95` |
| 8001 | RedisInsight | `compose.yml:97` |
| 11434 | Ollama | `compose.yml:116` |

### 8.4 Recommended new port

Use the variable name `CAPTURE_PORT` with the default value `8056`.

Reasons:

1. `8056` collides with no port in `compose.yml`.
2. `8056` sits inside the range that `_validate_port` accepts
   (`web_portal/services/config.py:66-75`).
3. `8056` sits next to `8055`, so the pair is easy to remember.
4. The name `CAPTURE_PORT` does not collide with `WEB_PORT`, so the two
   applications can start together.

The new port needs three edits when implementation starts: an `ENV` line and an
`EXPOSE` line near `Containerfile:105` and `Containerfile:111`, a published
port near `compose.yml:13`, and a second Gunicorn command in
`container/scripts/start.sh`.

---

## 9. Templates and assets

### 9.1 The base template

`web_portal/templates/base.html` is the only base template. It defines four
blocks:

| Block | Line |
| --- | --- |
| `title` | `web_portal/templates/base.html:7` |
| `extra_head` | `web_portal/templates/base.html:26` |
| `content` | `web_portal/templates/base.html:80` |
| `extra_scripts` | `web_portal/templates/base.html:98` |

The page holds a sticky navigation bar
(`web_portal/templates/base.html:30-76`), a main container
(`web_portal/templates/base.html:79-81`), and a footer
(`web_portal/templates/base.html:84-86`). The navigation list is hard-coded
with four links (`web_portal/templates/base.html:45-61`). A new page needs a
manual edit there, or a new base template.

Elements carry `data-testid` attributes, for example
`web_portal/templates/base.html:30` and `web_portal/templates/base.html:47`.
**Inference**: those attributes exist for browser automation that no test uses
yet. Section 10 covers that gap.

### 9.2 Vendored assets

Bootstrap is vendored, not loaded from a content delivery network:

- CSS at `web_portal/templates/base.html:10`, path
  `static/vendor/bootstrap/bootstrap.min.css`
- JavaScript at `web_portal/templates/base.html:89`, path
  `static/vendor/bootstrap/bootstrap.bundle.min.js`

Vendoring is required, because the content security policy allows `'self'`
only (`web_portal/services/config.py:100-106`).

Two portal scripts load on every page:

- `web_portal/static/js/portal.js` (`web_portal/templates/base.html:92-93`)
- `web_portal/static/js/data_preview.js`
  (`web_portal/templates/base.html:96`)

The `portal.js` tag carries a `data-default-theme` attribute
(`web_portal/templates/base.html:93`). The script reads it
(`web_portal/static/js/portal.js:20-23`).

### 9.3 Is there a JavaScript build step

**No.** `portal.js` is plain ES5-style JavaScript with `var` and function
declarations (`web_portal/static/js/portal.js:11-190`). No bundler
configuration exists for `web_portal`. The template links source files
directly.

**Inference**: a separate application named `ops-portal` exists in this
repository and may carry its own front-end tooling. That tooling does not apply
to `web_portal`.

### 9.4 Client helpers already available

`portal.js` provides five reusable helpers. A new page can call them:

| Helper | Line |
| --- | --- |
| `getCsrfToken` | `web_portal/static/js/portal.js:11` |
| `applyTheme` | `web_portal/static/js/portal.js:29` |
| `makeSortable` | `web_portal/static/js/portal.js:74` |
| `connectSSE` | `web_portal/static/js/portal.js:104` |
| `exportTableToCSV` | `web_portal/static/js/portal.js:129` |

The startup hook runs on `DOMContentLoaded`
(`web_portal/static/js/portal.js:186-190`). It applies the saved theme, loads
the theme menu, and makes every element with class `portal-table` sortable.

---

## 10. Test setup

### 10.1 Fixtures

`tests/e2e/conftest.py` defines four fixtures:

| Fixture | Line | Purpose |
| --- | --- | --- |
| `flask_app` | `tests/e2e/conftest.py:20-40` | Builds the application through the factory |
| `client` | `tests/e2e/conftest.py:43-46` | Flask test client |
| `_find_free_port` | `tests/e2e/conftest.py:49-53` | Picks a free port |
| `gunicorn_server` | `tests/e2e/conftest.py:56-99` | Starts a real Gunicorn process |

The `gunicorn_server` fixture runs this command
(`tests/e2e/conftest.py:56-99`):

```
python -m gunicorn --bind 127.0.0.1:{port} --timeout 30 --workers 1 wsgi:app
```

### 10.2 Does any test use the Gunicorn fixture

**No test uses it.** Stated plainly: the `gunicorn_server` fixture has zero
consumers. Every test in `tests/e2e/test_portal_smoke.py` takes the `client`
fixture only. The file holds no reference to `gunicorn_server`
(`tests/e2e/test_portal_smoke.py:1-165`).

The previous review was correct. The end-to-end setup is declared but unused.

### 10.3 Is a browser automation library installed and wired

Two separate answers:

- **Installed: yes.** `playwright>=1.40.0` is a declared dependency
  (`pyproject.toml:78`). An import check in this environment confirmed that
  `playwright`, `gunicorn`, `flask_wtf`, and `flask` all import.
- **Wired: no.** No portal test imports Playwright. No test opens a browser
  page. The only Playwright reference in the test tree sits in an unrelated
  geocoder test, where it is mocked.

**Result**: the portal has no real browser test. The `data-testid` attributes in
the templates have no consumer today.

### 10.4 What the new application should do

The new application can reuse the `client` fixture pattern for route tests. If
the feature needs proof that several workers work, a test must start Gunicorn
with more than one worker. The current fixture hard-codes `--workers 1`
(`tests/e2e/conftest.py:56-99`), so it needs a parameter.

---

## 11. Linter and type checker exclusions

### 11.1 ruff excludes the portal

`pyproject.toml:161`:

```toml
extend-exclude = ["mist-ops-platform", "web_portal", "scripts", "src/maps"]
```

ruff never checks `web_portal`.

### 11.2 mypy excludes the portal

`pyproject.toml:273-281`:

```toml
exclude = [
    "mist-ops-platform",
    "web_portal",
    "src/maps",
    "tests",
    "scripts",
    "tools",
    "starlink_dashboard.py",
]
```

A second mypy block softens imports for the same package
(`pyproject.toml:311-312`):

```toml
module = ["MistHelper", "src.maps.*", "web_portal.*"]
follow_imports = "silent"
```

mypy never checks `web_portal`.

### 11.3 Which gates still cover the portal

Three gates still apply:

- **bandit includes it** (`pyproject.toml:391`):

  ```toml
  targets = ["MistHelper.py", "maps_manager.py", "wsgi.py", "web_portal", "mist-ops-platform", "ops-portal", "src"]
  ```

- **interrogate includes it** (`pyproject.toml:492-494`): `fail-under = 90` and
  `exclude = ["tests", ".venv", "setup.py"]`. Portal docstrings are gated.
- **black includes it** (`pyproject.toml:435-437`): no exclusion for
  `web_portal`.

### 11.4 Decision for the new application

Do not place new code inside `web_portal`. Code placed there escapes ruff and
mypy. Place the new application in a new top-level package that the exclusion
lists do not name. Then ruff, mypy, bandit, black, and interrogate all cover it.

---

## Summary of constraints for feature 1823

1. Do not create an authenticated API session at module scope.
2. Require a fixed `SECRET_KEY` from the environment. Never generate one.
3. Keep run state in a shared store, not in a dictionary.
4. Use a per-run stop flag. Do not reuse `stop_loop.txt`.
5. Do not use the event bus. Poll a JSON endpoint every 30 seconds.
6. Do not patch `builtins.input`.
7. Serve every asset from the same origin. Vendor any new library.
8. Send the CSRF token with every state-changing request.
9. Use `CAPTURE_PORT` with the default `8056`.
10. Avoid `tmo`, `TMO`, and `t-mobile` in any file name.
11. Place the code outside `web_portal`, so ruff and mypy check it.
