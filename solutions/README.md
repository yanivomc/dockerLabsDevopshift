# Topic P2.1 — Solutions

Three reference answers for the three stages of the lab:

| File | Stage | What it answers |
|------|-------|------------------|
| [`Dockerfile.store`](Dockerfile.store) | Stage 1 — Multi-stage the store app | Three-stage build: Tailwind in `node:20-alpine`, Python deps in `python:3.12-slim` builder, runtime in `python:3.12-slim` with `gunicorn`. Compiled CSS + installed packages copied forward, Node and build tools don't ship. |
| [`Dockerfile.redis`](Dockerfile.redis) | Stage 2 — Custom Redis image | `FROM redis:7-alpine`, `apk add curl`, bakes in `redis.conf`, `HEALTHCHECK` via `redis-cli ping`. |
| [`docker-bake.hcl`](docker-bake.hcl) | Stage 3 — Docker Bake | Two targets (`store-app`, `store-db`), each with `:p2.1` + `:latest` tags and `cache-from` / `cache-to` for incremental builds against the registry. Default group builds both. |

## Spoiler policy

Write your own first. The Bake target especially — getting the `tags` and `cache-from` lines right is part of the lesson. Peek after you have something `docker buildx bake --print` accepts.
