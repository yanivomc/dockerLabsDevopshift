# Reference Dockerfiles — Topic 4

Three Dockerfiles, each better than the last. The lab walks through them in order; use these as reference if you get stuck.

| File | Stage | What changed | Cache-friendly? | Image size | Runs as root? | Healthcheck? |
|------|-------|--------------|-----------------|------------|----------------|---------------|
| `Dockerfile.naive` | 1 | Just enough to build and run. `FROM python:3.12`, single `COPY .`, no pip flags. | No | ~1 GB | Yes | No |
| `Dockerfile.cached` | 2 | `python:3.12-slim`, requirements copied first, `--no-cache-dir`, explicit copies. | Yes | ~150 MB | Yes | No |
| `Dockerfile.secure` | 3 | Adds a non-root `app` user and a `HEALTHCHECK` against `/health`. | Yes | ~150 MB | No | Yes |

## Trying each one

```bash
# Stage 1
docker build -f solutions/Dockerfile.naive -t store:naive .
docker images store:naive

# Stage 2
docker build -f solutions/Dockerfile.cached -t store:cached .
docker images store:cached

# Stage 3
docker build -f solutions/Dockerfile.secure -t store:secure .
docker run -d -p 5000:5000 --name store store:secure
docker inspect store --format '{{.Config.User}}'   # → app
docker ps                                          # STATUS includes (healthy)
```

## Spoiler policy

Write your own first. Peek only after you have something that builds.
