# ADR 0003: Alembic for schema migrations

Date: 2026-10-21 · Status: accepted

## Context

`Base.metadata.create_all()` is fine for a prototype but cannot alter existing
tables, has no history and cannot be reviewed in a pull request. Production
databases outlive application versions and need forward and backward paths.

## Decision

Manage the schema with Alembic. `alembic/env.py` is async-aware (it uses
`async_engine_from_config` and `run_sync`) and reads the URL from the same
`Settings` object as the application, so there is exactly one place where the
database location is configured. Migrations are run explicitly: the dev compose
runs `alembic upgrade head` before starting uvicorn, and the production stack has
a one-shot `migrate` service invoked by `make prod-up` and by the deploy workflow
before the new backend image starts. Autogenerate is used to draft revisions
(`make makemigration m="..."`) but every revision is reviewed by hand, in
particular for data migrations and index concurrency.

## Consequences

- CI applies `upgrade head` and `downgrade base` against SQLite to catch broken
  revision chains early; Postgres-specific operations must be guarded or tested
  in an integration job.
- The application never creates tables itself; tests call `create_all` directly
  because they want a throwaway schema, not a migration history.
- Zero-downtime deploys require expand/contract migrations; this is a process
  rule for the team, not something the tooling can enforce.
