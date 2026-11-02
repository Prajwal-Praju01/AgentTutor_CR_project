# Architecture

AgentTutor is a Flask application factory plus a React/Vite client.

## Runtime layers

- `backend/app/api/routes` exposes versioned HTTP contracts.
- `backend/app/services` handles authentication and cross-cutting application
  behavior.
- `backend/app/tutoring` orchestrates course-aware, hint-first tutoring.
- `backend/app/debugging` implements task state, question branching, response
  verification, and fix validation.
- `backend/app/retrieval` extracts, chunks, embeds, searches, and cites course
  documents.
- `backend/app/llm` provides provider adapters, prompt versions, and structured
  output schemas.
- `backend/app/models` contains the SQLAlchemy persistence model.
- `frontend/src/features` contains route-level user workflows connected through
  `frontend/src/services/api.ts`.

## State and safety

Messages, student-model snapshots, debugging tasks, question nodes, proposed
fixes, verification results, and LLM call metadata are persisted. JWTs are
accepted only by the backend and provider credentials are never sent to the
browser. The default mock provider is deterministic for local development and
tests; live-provider behavior requires explicit configuration.

Student code is not executed in the Flask process. Code execution remains
disabled by default and must use an isolated runner before being enabled.

## Database

Alembic migrations are in `backend/migrations/versions`. PostgreSQL is the
production target; SQLite is used by the test suite for isolated fast tests.
