# Production Readiness: Containerized Deployment, Resilience & Observability, CI Pipeline

## What was built

This PR makes SupportLens production-ready with three capabilities:

### 1. Containerized Deployment
- **Backend Dockerfile** (`python:3.13-slim`) — installs deps with layer caching, runs uvicorn
- **Frontend Dockerfile** (multi-stage) — builds with `node:20-alpine`, serves production build via `nginx:stable-alpine`
- **`docker-compose.yml`** — orchestrates `db`, `backend`, `frontend`, and a one-shot `seed` service
- **Seed idempotency** — checks if traces exist before inserting; safe to run `docker compose up` repeatedly
- **Data persistence** — named `pgdata` volume survives `docker compose down` / `up` cycles
- **Configuration via `.env`** — API key can be changed without rebuilding images
- **Image sizes** — backend ~173MB, frontend ~62MB (no `node_modules`, `.git`, or `__pycache__` in images)

### 2. Resilience & Health Endpoint
- **`GET /health`** probes real dependencies:
  - Database: `SELECT 1` against PostgreSQL
  - LLM: checks if `GROQ_API_KEY` is configured
  - Uptime: seconds since process start
- **Graceful degradation** when LLM is unavailable — chat returns a fallback response, traces are stored with `category = "LLM_UNAVAILABLE"`, and the app continues serving traffic

### 3. Structured JSON Logging
- Every HTTP request (except `/health`) is logged as a JSON line to stdout
- Fields: `timestamp`, `level`, `method`, `path`, `status_code`, `duration_ms`, `request_id`
- LLM errors logged with structured context: `event`, `error_type`, `error_message`, `user_message`
- `/health` is excluded to prevent log flooding from orchestrator polls

### 4. CI Pipeline (GitHub Actions)
- **Layer 1: Code Quality** — `black --check` + `flake8` (fast fail gate)
- **Layer 2: Docker Build** — builds both images (proves they compile)
- **Layer 3: End-to-End Test** — `docker compose up` + `scripts/e2e_test.sh`
  - Verifies data flow: POST /chat, check analytics total incremented, verify trace exists, test category filter
  - Not just status code checks — asserts actual data correctness

---

## What does "healthy" mean for this application?

The health endpoint returns three possible statuses:

| Status | Condition | Operator action |
|---|---|---|
| `healthy` | DB reachable, LLM key configured | No action needed |
| `degraded` | DB reachable, LLM key **not** configured | Inform — the app still works (fallback responses, `LLM_UNAVAILABLE` category). Users get a polite "assistant unavailable" message. No data loss. |
| `unhealthy` | DB **not** reachable | Page — the app cannot store traces or serve analytics. Core functionality is broken. |

The key design decision: a missing LLM API key is **degraded, not unhealthy**. The app deliberately handles this case — it returns deterministic fallback responses and marks traces as `LLM_UNAVAILABLE` so the degradation is visible in analytics. An operator should be informed but not paged at 3am for this.

---

## How does the CI pipeline handle the missing LLM API key?

The CI pipeline copies `.env.example` as `.env` — the `GROQ_API_KEY` stays empty. This means:

1. **No real API credits are burned** on every push
2. **No secrets are committed** to the repository
3. The app starts in **degraded mode** — fallback responses, `LLM_UNAVAILABLE` category
4. The e2e test **verifies this fallback behavior** — it checks that the category is `LLM_UNAVAILABLE` and that it appears correctly in analytics
5. If a real API key were available (e.g., via GitHub Secrets), the same test would pass with real LLM responses — the assertions are designed to work in both modes

---

## What would you change about the Docker setup before a real deployment?

1. **Non-root user in backend container** — currently runs as root; should add `USER appuser` for security
2. **Health check on the backend service** in compose — currently only the DB has a healthcheck; the backend should too so orchestrators know when it's ready
3. **Production-grade CORS** — currently `allow_origins=["*"]`; should be locked down to the frontend domain
4. **Secrets management** — `.env` files are fine for local dev, but production should use Docker secrets, Vault, or cloud-native secret stores
5. **Gunicorn with multiple workers** — uvicorn single-worker is fine for dev but production needs multiple workers behind gunicorn for concurrency
6. **Image pinning** — `postgres:16-alpine` should be pinned to a specific patch version (e.g., `16.2-alpine`) to avoid surprise upgrades
7. **Log rotation / aggregation** — stdout logging is correct for containers, but a real deployment needs a log collector (Fluentd, CloudWatch, etc.)
8. **Resource limits** — `mem_limit` and `cpus` in compose or orchestrator-level limits to prevent runaway containers
9. **TLS termination** — a reverse proxy (Traefik, Caddy) in front for HTTPS
10. **Database backups** — the `pgdata` volume has no backup strategy; production needs automated snapshots

---

## Commit history

| Commit | Description |
|---|---|
| `4aaf1b0` | refactor: production-ready backend code (context manager, LLM fallback, seed idempotency) |
| `6be984d` | feat: add production /health endpoint |
| `2adbae4` | feat: add structured JSON request logging |
| `b809172` | feat: add Dockerfiles and nginx config |
| `316c3c4` | feat: add docker-compose.yml |
| `9f5f34b` | feat: add unified .env.example at project root |
| `91f9ab0` | feat: add CI pipeline and end-to-end test script |
