# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- API reference and curl-session screenshots in the README.
- CodeQL code scanning workflow (Python, JavaScript/TypeScript and Actions) and Dependabot updates for pip, npm, Docker and GitHub Actions.
- Roadmap tracked as GitHub issues under the v0.2.0 milestone.
- This changelog.

### Changed

- CI workflow runs with a read-only `GITHUB_TOKEN` by default.
- README backend test count updated to the current suite (28).

## [0.1.1] - 2026-10-25

### Fixed

- Release builds push images to lowercase GHCR paths (`ghcr.io/akibullah/docker-fastapi-react-template/backend` and `/web`); the mixed-case path made the v0.1.0 release build fail ([#1](https://github.com/AkibUllah/docker-fastapi-react-template/pull/1)).
- The SSH deploy job is opt-in via the `DEPLOY_ENABLED=true` repository variable; without it a release builds and publishes images only.

## [0.1.0] - 2026-10-25

First public release.

### Added

- FastAPI backend with async SQLAlchemy 2.0, Alembic migrations (async `env.py`), pydantic-settings, JWT access and rotating refresh tokens with a Redis denylist, bcrypt passwords, users CRUD with self/superuser authorisation, liveness/readiness probes and JSON logs with `X-Request-ID`.
- React 18 + TypeScript SPA with TanStack Query, React Router, react-hook-form + zod, an axios client with a single shared refresh on 401, and protected/superuser-only routes.
- nginx serving SPA and API from one origin with security headers, SPA fallback and asset caching.
- Development and production compose stacks (hot reload, Postgres 16, Redis 7, multi-stage non-root images, one-shot migrate service).
- Makefile, CI on Python 3.10/3.11 and Node 18/20 with image builds, an example GHCR + SSH deploy workflow, pre-commit config and three ADRs.
- Live demo kit: Swagger UI on GitHub Pages, Codespaces dev container and Render blueprint.

### Fixed

- Managed Postgres URLs are accepted, a superuser can be created at start-up, and the nginx upstream is configurable.

[Unreleased]: https://github.com/AkibUllah/docker-fastapi-react-template/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/AkibUllah/docker-fastapi-react-template/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/AkibUllah/docker-fastapi-react-template/releases/tag/v0.1.0
