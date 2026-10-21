# syntax=docker/dockerfile:1.6
# Stage 1: build the SPA. Stage 2: serve it with nginx (also proxies /api to the backend).
# Build context is the repository root: docker build -f frontend/Dockerfile .
FROM node:18-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ .
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine AS prod
RUN rm /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/prod.conf /etc/nginx/conf.d/default.conf
COPY nginx/snippets /etc/nginx/snippets
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1/healthz || exit 1
