# syntax=docker/dockerfile:1.6
# Stage 1: build the SPA. Stage 2: serve it with nginx (also proxies /api to the backend).
# Build context is the repository root: docker build -f frontend/Dockerfile .
FROM node:26-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ .
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.31-alpine AS prod
RUN rm /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
# Rendered to conf.d/default.conf at start-up; only the three listed variables are substituted.
COPY nginx/prod.conf.template /etc/nginx/templates/default.conf.template
COPY nginx/snippets /etc/nginx/snippets
ENV PORT=80 API_HOST=backend API_PORT=8000 NGINX_ENVSUBST_FILTER="^(PORT|API_HOST|API_PORT)$"
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1/healthz || exit 1
