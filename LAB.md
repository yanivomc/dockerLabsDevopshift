# Topic P2.1 — Multi-stage + Bake

You can build, run, persist, and cache. Today: **make the image production-shaped, build everything in one command, and push.**

Three lessons stacked on the same lab:

1. **Multi-stage builds** — separate the build-time toolchain from what actually ships.
2. **Custom upstream images** — extend `redis:7-alpine` with our own config and healthcheck.
3. **Docker Bake** — declare every image your service needs in one file and `docker buildx bake` builds them in parallel. `--push` publishes them.

This topic also **subsumes the publishing lesson** — Bake does the `tag` + `push` story too.

## What changed in the app since Topic 6

Two real production moves you'll see in the Dockerfile:

- **Tailwind built locally**, not from CDN. The old `<script src="cdn.tailwindcss.com">` was a dev-only convenience that warned in the browser console. Templates now reference `static/style.css`, which a build step has to produce. The branch ships with a `package.json` and a `tailwind.config.js` for that.
- **gunicorn replaces `python app.py`**. The Flask dev server prints a "do not use in production" warning every time it boots — gunicorn is the real WSGI server. `requirements.txt` gained `gunicorn==22.0.0`.

The Python code is unchanged from Topic 6. The lab is entirely about how you *package and ship* the unchanged code.

## Repo layout — first time we have sub-folders

```
.
├── store/                  # Flask app — full build context
│   ├── app.py
│   ├── products.json
│   ├── requirements.txt
│   ├── package.json        # Tailwind CLI dep
│   ├── tailwind.config.js
│   ├── src/input.css       # Tailwind source
│   ├── templates/
│   └── Dockerfile          # topic-6's single-stage Dockerfile — you'll rewrite it
├── redis/                  # custom Redis image — full build context
│   ├── redis.conf
│   └── (Dockerfile)        # you'll write this
├── docker-bake.hcl         # skeleton with TODO gaps
└── solutions/
    ├── README.md
    ├── Dockerfile.store
    ├── Dockerfile.redis
    ├── docker-bake.hcl
    └── CHALLENGE.md        # multi-platform + multi-registry stretches
```

The two sub-folders are deliberate — Bake's `context` is per-target, so each image gets its own folder.

---

## Stage 1 — Multi-stage the store app

The current `store/Dockerfile` is Topic 6's single-stage build. Today you turn it into **three** stages.

### Why three

| Stage | Base | What it does | What it leaves behind |
|-------|------|--------------|------------------------|
| `css` | `node:20-alpine` | `npx tailwindcss -i src/input.css -o static/style.css --minify` | Node toolchain (~100 MB) |
| `pybuild` | `python:3.12-slim` | `pip install --prefix=/install -r requirements.txt` | pip cache, build temp files |
| (final) | `python:3.12-slim` | `COPY --from=css …`, `COPY --from=pybuild …`, run gunicorn as non-root | Nothing extra |

The final image ships **only the runtime**. Node never sees your production server.

### Your task

Rewrite `store/Dockerfile` into a three-stage build. Keep everything from Topic 5's secure outcome (non-root `app` user, `VOLUME /data`, healthcheck) — those still apply.

Things to remember:
- Tailwind needs `package.json`, `tailwind.config.js`, `src/input.css`, **and** `templates/` (so it can scan classes). Copy all four into the css stage.
- Python deps: `pip install --prefix=/install` puts them in a relocatable tree. Copy `/install` to `/usr/local` in the final stage so they end up on `sys.path` automatically.
- Switch the `CMD` to gunicorn: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`.

### Verify

```bash
docker build -t store:p2.1 ./store
docker images store:p2.1
# REPOSITORY   TAG     IMAGE ID       CREATED         SIZE
# store        p2.1    <id>           <seconds ago>   ~180MB
```

Compare with the topic-6 image (`store:topic6`) — yours should be a similar size or smaller, but the difference is that **no Node, no build tooling, no pip cache** ships. Run it and confirm:

```bash
docker volume create store-data 2>/dev/null
docker network create store-net 2>/dev/null
docker run -d --rm --name redis-tmp --network store-net redis:7-alpine
docker run -d --name store --network store-net -p 5000:5000 -v store-data:/data store:p2.1
curl http://localhost:5000/health
docker logs store | head    # gunicorn boot lines, not the Flask dev warning
docker rm -f store redis-tmp
```

> **Stuck?** [`solutions/Dockerfile.store`](solutions/Dockerfile.store) is the reference answer.

---

## Stage 2 — Custom Redis image

The `redis/` folder ships with a `redis.conf` (two lines: `maxmemory 256mb` + `appendonly yes`). You write the Dockerfile that bakes that config into a custom image.

### Your task

Create `redis/Dockerfile`:

- `FROM redis:7-alpine`
- `apk add --no-cache curl` (alpine doesn't ship curl; we use it for ad-hoc poking)
- `COPY redis.conf /usr/local/etc/redis/redis.conf`
- `HEALTHCHECK` running `redis-cli ping | grep -q PONG`
- `CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]`

### Verify

```bash
docker build -t store-db:p2.1 ./redis
docker run -d --rm --name redis-test store-db:p2.1
sleep 1
docker exec redis-test redis-cli PING
# → PONG
docker exec redis-test redis-cli CONFIG GET maxmemory
# → 1) "maxmemory"
# → 2) "268435456"     (= 256 MB in bytes)
docker rm -f redis-test
```

> **Stuck?** [`solutions/Dockerfile.redis`](solutions/Dockerfile.redis).

---

## Stage 3 — Docker Bake: one command for everything

Bake declares all your build targets in `docker-bake.hcl` and builds them **in parallel**. With `--push`, it tags and publishes in the same step — which is why this topic also covers what would have been Topic 7.

### Your task

Open [`docker-bake.hcl`](docker-bake.hcl). It has four TODO gaps:

1. `REGISTRY` variable: set the default to your Docker Hub namespace (e.g. `yanivomc`) or `ghcr.io/<user>`.
2. `target "store-app"`: add a second tag — `:latest` alongside the `:${TAG}`.
3. `target "store-app"`: add `cache-from = ["type=registry,ref=${REGISTRY}/store:cache"]` and a `cache-to` line so subsequent builds reuse layers from the registry.
4. `target "store-db"`: fill `context`, `dockerfile`, `tags` — same shape as `store-app` but pointing at `./redis` and `store-db`.
5. `group "default"`: list both targets so a bare `docker buildx bake` builds both.

### Verify

```bash
# Print the resolved spec without building
docker buildx bake --print

# Build both images in parallel, locally
docker buildx bake
docker images | grep -E '(store|store-db)' | head

# Push to your registry (auth first)
docker login
docker buildx bake --push
```

If the print step shows both targets and the build produces two new tags, you're done.

> **Stuck?** [`solutions/docker-bake.hcl`](solutions/docker-bake.hcl).

---

## Run the whole stack with your baked images

```bash
docker network create store-net 2>/dev/null
docker volume create store-data 2>/dev/null

docker run -d --name redis --network store-net store-db:p2.1
docker run -d --name store --network store-net -p 5000:5000 \
  -v store-data:/data store:p2.1
```

Open http://localhost:5000:
- Page is styled (Tailwind built locally, no CDN warning in console).
- `/cache` shows connected, hit ratio climbs as you browse.
- `docker logs store` shows gunicorn workers, **no** "development server" warning.
- `docker inspect store --format '{{.Config.Cmd}}'` shows `gunicorn -w 4 -b 0.0.0.0:5000 app:app`.

---

## Stretch challenges

See [`solutions/CHALLENGE.md`](solutions/CHALLENGE.md) for two production-shape stretches you can do with the same Bake file:

- **Multi-platform images** (`linux/amd64,linux/arm64`) for x86 servers + Apple Silicon laptops.
- **Push to two registries** (Docker Hub + GHCR) in the same `bake --push`.

---

## Cleanup

```bash
docker rm -f store redis 2>/dev/null
docker network rm store-net
docker volume rm store-data
```

---

## Pedagogical hooks the slides can call out

| What | Why it lands |
|------|--------------|
| `docker images store:p2.1` shows no Node | Concrete proof multi-stage worked — what built the CSS isn't in the runtime |
| `docker logs store` shows gunicorn workers, no Flask dev warning | "Production server" is no longer a slide claim — it's a log line |
| `docker buildx bake` builds two unrelated images in one keystroke | The DX win that justifies all the YAML/HCL |
| `--push` does it all at once | The Topic-7 publish lesson, now zero extra commands |
| `cache-from` / `cache-to` over the registry | Cross-machine layer reuse — the move that makes CI builds fast |
