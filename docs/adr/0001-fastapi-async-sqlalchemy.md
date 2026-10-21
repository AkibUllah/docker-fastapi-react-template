# ADR 0001: FastAPI with async SQLAlchemy 2.0

Date: 2026-10-21 · Status: accepted

## Context

Client projects that start from this template are typically I/O-bound APIs: they
call Postgres, Redis, payment providers (bKash, SSLCommerz) and SMS gateways, and
spend most of a request waiting on the network. We want one worker process to
handle many concurrent requests without a thread pool per connection, typed
request/response models, and generated OpenAPI documentation for the frontend team.

## Decision

Use FastAPI on uvicorn with SQLAlchemy 2.0 in asyncio mode (asyncpg driver in
production, aiosqlite in tests). Pydantic v2 models define the API contract and
settings. Business logic lives in `app/services`, which take an `AsyncSession` and
know nothing about HTTP, so it can be reused from scripts and background jobs.

## Consequences

- Every DB access must be awaited; blocking libraries have to be wrapped in
  `run_in_threadpool`. Reviewers should watch for sync drivers sneaking in.
- Tests run against SQLite in memory with the same async session code, so the
  suite needs no services and finishes in seconds.
- SQLAlchemy 2.0 typed `Mapped[...]` columns give mypy coverage of the models.
- The async stack rules out a few Django-ecosystem conveniences (admin, forms);
  for admin-heavy products the Django templates in the portfolio are a better fit.
