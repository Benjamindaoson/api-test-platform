## ADDED Requirements

### Requirement: Reproducible UI image
The system SHALL provide `ui/Dockerfile` that installs the lockfile-defined dependencies with `pnpm install --frozen-lockfile`, builds the Next.js application with `pnpm build`, and starts the production server on port 3000.

#### Scenario: UI image is built from a clean Docker context
- **WHEN** Docker builds the UI image without a pre-existing `node_modules` directory
- **THEN** the locked pnpm installation and production Next.js build complete before the runtime image is created

### Requirement: Platform Compose profile
The system SHALL expose a `platform` Compose profile containing PostgreSQL, Redis, FastAPI, and UI, with FastAPI dependent on PostgreSQL health and UI dependent on FastAPI health.

The PostgreSQL service and FastAPI service SHALL consume the same configurable
`POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` values. Platform ports
SHALL bind to loopback by default so the local profile does not expose its
unauthenticated test executor on a LAN interface.

#### Scenario: Platform profile reaches healthy state
- **WHEN** `docker compose --profile platform up --build --wait` is run with no model credentials
- **THEN** PostgreSQL, Redis, FastAPI, and UI become available without starting the opt-in LangGraph service

#### Scenario: Non-default database credential is supplied
- **WHEN** a developer supplies `POSTGRES_PASSWORD` through the environment or `.env`
- **THEN** both PostgreSQL initialization and FastAPI connection use that same value and the API reports a healthy database connection

### Requirement: Python container/runtime alignment
The system SHALL use Python 3.13 container images and lockfile-resolved Python dependencies for management and LangGraph images.

#### Scenario: API image matches project Python floor
- **WHEN** the API container is built
- **THEN** its base image uses Python 3.13 and its dependencies are installed from the locked project dependency graph
