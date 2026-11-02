# Testing

## Backend

Run from the repository root:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m pytest tests -q
```

The backend tests use deterministic mock LLM and embedding providers where
possible. Live provider tests must be run separately with explicit credentials
and must not be used as the deterministic CI baseline.

## Frontend

```powershell
Set-Location frontend
npm run lint
npm run test
npm run build
```

The frontend test suite uses Vitest and React Testing Library. Playwright is
available through `npm run test:e2e`; browser tests should be added for flows
that require a running backend and database.

## Database migrations

Use a configured PostgreSQL `DATABASE_URL` for development:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

The migration can also be validated against SQLite for local smoke checks. The
application's production database remains PostgreSQL.

## Interpreting results

Report actual pass, skip, and failure counts. Do not treat the mock provider as
evidence of live-provider quality, and do not claim research effectiveness
without running the documented evaluation conditions on an appropriate dataset.