# AgentTutor

AgentTutor is an agentic AI academic tutoring platform that combines
Socratic teaching with the TreeInstruct hierarchical debugging methodology.
It provides course-aware tutoring, debugging assistance, knowledge-base
retrieval, adaptive difficulty, and persistent student progress.

The project contains:

- **Backend:** Flask, SQLAlchemy, Alembic, PostgreSQL/pgvector
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Evaluation tools:** reproducible utilities under `evaluation/`

## Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer and npm
- PostgreSQL 15 or newer with the `vector` extension
  - Docker Desktop is the simplest way to run PostgreSQL locally.
- Git

Docker is optional if PostgreSQL is already installed locally. An LLM API key
is not required for local development because the default provider is `mock`.

## Quick start on Windows

Run the following commands from the repository root in PowerShell.

### 1. Configure environment variables

```powershell
Copy-Item .env.example .env
```

The defaults use the deterministic mock LLM and embedding providers. For a
real provider, edit `.env` and set the matching `LLM_PROVIDER` and
`LLM_API_KEY`. Keep `.env` private; it is intended for local configuration and
must not be committed.

### 2. Start PostgreSQL

If PostgreSQL is installed locally, make sure it is running and create the
`agenttutor_dev` and `agenttutor_test` databases.

Alternatively, start the PostgreSQL service supplied by this repository:

```powershell
docker compose up -d postgres
```

The Compose service uses:

| Setting | Value |
|---|---|
| Host | `localhost` |
| Port | `5432` |
| User | `agenttutor` |
| Password | `password` |
| Development database | `agenttutor_dev` |
| Test database | `agenttutor_test` |

The initialization script also enables `vector` and `uuid-ossp`.

### 3. Install backend dependencies and initialize the database

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\seed.py
Set-Location ..
```

If the virtual environment already exists, skip the `python -m venv .venv`
command.

### 4. Install frontend dependencies

```powershell
Set-Location frontend
npm install
Set-Location ..
```

### 5. Start the application

Use two PowerShell windows.

**Backend:**

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m flask --app wsgi:app run --debug --host=0.0.0.0 --port=5000
```

**Frontend:**

```powershell
Set-Location frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in a browser. The backend
API is available at `http://localhost:5000/api/v1`; the health endpoint is
`http://localhost:5000/api/v1/health`.

## Makefile shortcuts

The repository includes Windows-oriented Makefile targets for setup, database
migrations, seeding, tests, and linting. From the repository root:

```powershell
make setup
make db-migrate
make db-seed
make test
make lint
```

The backend and frontend development servers must be started in separate
terminals with `make dev-backend` and `make dev-frontend`. Do not use
`make dev`: it is listed for reference but is not currently implemented as a
combined process runner.

## Docker notes

The current `docker-compose.yml` reliably defines the PostgreSQL development
service:

```powershell
docker compose up -d postgres
docker compose logs -f postgres
docker compose down
```

The `backend` and `frontend` Compose services reference Dockerfiles that are
not currently included in this repository. Therefore, use the local backend
and frontend commands above unless those Dockerfiles are added.

## Testing and linting

Backend tests and checks:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest tests -v --tb=short
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m mypy app --ignore-missing-imports
```

Frontend tests and checks:

```powershell
Set-Location frontend
npm run lint
npm run test
npm run build
```

End-to-end tests are available with `npm run test:e2e`; they require the
frontend, backend, and database to be running.

See [docs/TESTING.md](docs/TESTING.md) for the testing policy and guidance on
interpreting mock-provider results.

## Configuration

All application settings are environment-driven. See [.env.example](.env.example)
for the complete list, including:

- `DATABASE_URL` and `TEST_DATABASE_URL`
- `LLM_PROVIDER`, `LLM_API_KEY`, and `LLM_MODEL`
- `EMBEDDING_PROVIDER` and `ENABLE_VECTOR_SEARCH`
- upload, authentication, rate-limit, CORS, and code-execution settings

Use `LLM_PROVIDER=mock` and `EMBEDDING_PROVIDER=mock` for deterministic local
development without external API credentials. Set `ENABLE_VECTOR_SEARCH=true`
only when the PostgreSQL `vector` extension and a compatible embedding
configuration are available.

## Project structure

```text
frontend/       React + TypeScript + Vite application
backend/        Flask API, agents, tutoring, retrieval, migrations, tests
evaluation/     Research evaluation utilities and benchmark inputs
docs/           API, architecture, database, and testing documentation
scripts/        Database initialization scripts
uploads/        Local uploaded-document storage
```

For more detail, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[docs/API.md](docs/API.md), and [docs/DATABASE.md](docs/DATABASE.md).

## Research evaluation

The evaluation framework does not contain pre-populated results. Run it only
with recorded observations and document the model, prompt, dataset,
configuration, and sample size. See [evaluation/README.md](evaluation/README.md).

## License

MIT
