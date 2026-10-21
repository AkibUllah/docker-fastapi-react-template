# ADR 0002: nginx in front of the API and the SPA

Date: 2026-10-21 · Status: accepted

## Context

The frontend is a static Vite build and the backend is uvicorn. Browsers need
both on one origin to avoid CORS and cookie complications, static files should be
served with proper caching headers, and uvicorn should not be the process that
terminates slow clients or large uploads.

## Decision

Run nginx as the only published container. In production it serves the SPA
bundle from the image built in `frontend/Dockerfile`, falls back to `index.html`
for client-side routes, caches hashed `/assets/` for a year, gzips text
responses, sets security headers (CSP, nosniff, frame-ancestors) and proxies
`/api/` to the backend with `X-Forwarded-*` and `X-Request-ID` headers. In
development the same proxy sits in front of the Vite dev server (including the
HMR websocket) so the app is exercised through the same paths it will use in
production.

## Consequences

- Backend CORS configuration is only needed for local tooling that bypasses the
  proxy (e.g. Vite on :5173 calling :8000 directly).
- TLS termination is expected one hop earlier (cloud load balancer, Caddy or
  certbot-managed nginx on the host); the compose file publishes plain HTTP.
- Request IDs assigned by nginx are propagated to backend logs, which makes
  tracing a user report through both layers straightforward.
