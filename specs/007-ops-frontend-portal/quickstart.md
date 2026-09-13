# Quickstart: Ops Frontend Portal

**Branch**: `007-ops-frontend-portal`

---

## Prerequisites

- Node.js 22+ (LTS)
- npm 10+ (included with Node.js)
- Mist Ops Platform backend running on `http://localhost:8000` (or configured via `.env`)

---

## Initial Setup

```bash
# Clone and switch to feature branch
cd MistHelper
git checkout 007-ops-frontend-portal

# Navigate to portal directory
cd ops-portal

# Install dependencies
npm install

# Copy environment template
cp .env.example .env
```

### Environment Variables

```bash
# .env
VITE_API_BASE_URL=http://localhost:8000/api/v1   # Backend API URL (dev only)
VITE_POLLING_ACTIVE_MS=5000                       # Active polling interval
VITE_POLLING_PASSIVE_MS=30000                     # Passive polling interval
```

---

## Development

```bash
# Start dev server with HMR
npm run dev
# Portal available at http://localhost:5173
# API requests proxied to backend via Vite dev server proxy

# Run type checking
npm run typecheck

# Run linter
npm run lint

# Run unit + component tests
npm run test

# Run E2E tests (requires portal + mock API running)
npm run test:e2e
```

---

## Build & Container

```bash
# Production build
npm run build
# Output: dist/ directory with static assets

# Build container image
podman build -t ops-portal .

# Run container (connects to backend API service)
podman run -d --name ops-portal -p 8080:80 ops-portal

# Or use compose (starts all services)
cd ..  # Back to MistHelper root
podman-compose up -d portal
```

---

## Project Structure

```
ops-portal/
├── src/
│   ├── api/             # API client + query factories (5 files)
│   ├── components/      # Shared UI components
│   ├── features/        # Feature modules
│   ├── hooks/           # Shared custom hooks
│   └── pages/           # Route-level pages
├── tests/
│   ├── e2e/             # Playwright tests
│   └── unit/            # Vitest + RTL tests
├── public/              # Static assets
├── nginx/               # Container Nginx config
├── Containerfile
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.ts
```

---

## Key Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server (port 5173) |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview production build locally |
| `npm run typecheck` | TypeScript type checking |
| `npm run lint` | ESLint + Prettier check |
| `npm run test` | Unit + component tests (Vitest) |
| `npm run test:e2e` | E2E tests (Playwright) |

---

## Connecting to Backend

**Development**: Vite's proxy routes `/api/` requests to the backend:

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

**Production**: Nginx reverse proxy handles `/api/` routing (see `nginx/default.conf`).

---

## Testing Against Mock Data

For frontend development without a running backend:

```bash
# Start mock API server (MSW-based)
npm run mock-api

# In another terminal, start dev server
npm run dev
```

The mock API serves realistic responses matching the backend API contracts.
