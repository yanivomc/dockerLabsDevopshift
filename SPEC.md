# DevopShift Store — Lab App Spec

> **Audience:** the slides-builder AI for the DevopShift Docker course.
> **Purpose:** describe the lab app, its evolution across topics, the student commands, and the talking points — in chunks a slide generator can map 1:1 to slides.

---

## 1. What this lab is

A small e-commerce-style app (the "DevopShift Store") that students operate from inside a single Docker container in Topic 3, then progressively extend across later topics. The same codebase grows — students never start over.

- **Stack:** Python 3.12, Flask, Jinja templates, Tailwind via CDN (no build step yet — Topic 4 introduces the build).
- **Data in Topic 3:** static `products.json` baked into the image.
- **Purpose:** give every Docker lesson (run, build, volume, network, registry, multi-stage, compose) a concrete app that visibly *changes shape* between topics.

---

## 2. Course at a glance

| Topic | Title | What changes architecturally | Built? |
|-------|-------|-------------------------------|--------|
| 3 | Monolith | One pre-built container, static JSON | ✅ Yes |
| 4 | Build it yourself | Same architecture; student writes Dockerfile, 3-stage progression | ✅ Yes |
| 5 | Persistence | + SQLite on a named volume; cart finally works, walkthrough + bind-mount challenge | ✅ Yes |
| 6 | Sidecar | + Redis on a user-defined network; cache-aside `/products`, default-bridge vs user-defined-network demo | ✅ Yes |
| P2.1 | Multi-stage + Bake | Production-shape image (Tailwind build + gunicorn), Docker Bake orchestrates parallel builds and pushes; absorbs former Topic 7 | ✅ Yes |
| P2.2 | Compose stack | Flask + MySQL + Redis + Ollama (`/recommend`) | Planned |

> **Topic 7 was folded into P2.1.** Bake's `--push` covers everything Topic 7 would have taught (`docker tag` + `docker push` + multi-registry). The architecture timeline no longer contains a Topic 7 stage.

The current branch state: `main` and `topic-3` both point at the Topic 3 build.

**Branching rule for slides:** each topic = one branch. The list above lives in code as `ARCHITECTURE_STAGES` in `app.py`; only the constant `CURRENT_TOPIC` changes between branches. Slides should mirror this — same diagram every slide deck, different highlighted stage.

---

## 3. The Topic 3 lab — what the student does

### 3.1 The one-line goal
> Run a Flask web app inside a container. Don't build it. Don't write a Dockerfile. Just pull, run, and explore.

### 3.2 The eight stages (one slide each works well)

| # | Command | Concept slide title suggestion |
|---|---------|---------------------------------|
| 1 | `docker pull yanivomc/store:1.0` | "Pulling images — layers and tags" |
| 2 | `docker run -d -p 5000:5000 --name store yanivomc/store:1.0` | "Running a container — detached, ports, names" |
| 3 | `docker ps` + browse `http://EC2_IP:5000` | "Verifying it runs" |
| 4 | `docker logs -f store` | "Live logs — Flask request stream" |
| 5 | `docker exec -it store sh` | "Shell into a running container" |
| 6 | `docker stop store` then `docker start store` | "Lifecycle — and what doesn't survive" |
| 7 | `docker inspect store` | "Container metadata — ports, env, mounts" |
| 8 | `docker rm -f store` + `docker container prune` | "Cleanup patterns" |

### 3.3 Pedagogical hooks built into the UI

Things the slides can explicitly tell the student to look at, with the *why*:

| What to point at | Why it's interesting |
|------------------|----------------------|
| The "**Topic 3 · Monolith**" pill in the header | The app *knows* which lesson it represents — sets up the "watch this change in Topic 5" payoff |
| The **Architecture** page (link in header) | Whole-course diagram with current stage pulsing — primes the journey |
| **Container hostname** in the footer | Changes on every `docker run` — proof of container isolation; great for scaling demos later |
| **Views since boot** counter in the footer | Resets when the container restarts — sets up the Topic 5 volume lesson ("how do we keep this?") |
| **"Add to cart · unlocks in Topic 5"** disabled button on product pages | Plants the seed for persistence |
| `/info` endpoint — `hostname`, `env`, `topic`, `views` | Curl-friendly proof of all of the above in one JSON blob |

### 3.4 Suggested talking points the slides can echo

- "You didn't build this — someone built it once, you pulled it. That's the point of registries."
- "The container's hostname is its container ID. `exec` into another one, you'll see a different ID."
- "Restart the container and the view counter goes back to zero. Hold that thought — Topic 5."
- "Notice the architecture diagram. Every topic adds a box. Today there's one."

---

## 4. App surface — endpoints and pages

### 4.1 HTTP endpoints (live in `app.py`)

| Method | Path | Returns | Notes |
|--------|------|---------|-------|
| GET | `/` | HTML — storefront grid | Optional `?category=laptops\|phones\|headphones` for filter |
| GET | `/product/<id>` | HTML — product detail page | 404 if unknown id |
| GET | `/architecture` | HTML — course-wide architecture timeline | Highlights current `CURRENT_TOPIC` |
| GET | `/products` | JSON — full product list | Same `?category=` filter as `/` |
| GET | `/products/<id>` | JSON — single product | 404 if unknown id |
| GET | `/health` | JSON — `{"status":"ok","version":"1.0"}` | Use this in curl demos |
| GET | `/info` | JSON — hostname, env, topic, views | Best single endpoint to show "this container, right now" |

### 4.2 Pages (in `templates/`)

| Template | Renders on | Purpose |
|----------|------------|---------|
| `base.html` | every page | Shared chrome — header, nav, Topic badge, footer with hostname + views |
| `index.html` | `/` | Product grid with category filter chips |
| `product.html` | `/product/<id>` | Large illustration, tagline, description, specs table, disabled cart |
| `architecture.html` | `/architecture` | Vertical timeline of all 7 course stages |
| `404.html` | any unknown path | Friendly "Back to store" |
| `_macros.html` | (imported) | Inline SVG icons per category |

### 4.3 Static data — `products.json`

Six products across three categories. Each has: `id`, `name`, `price`, `category`, `tagline`, `description`, `specs` (dict).

| id | name | price | category |
|----|------|-------|----------|
| 1 | DevopShift Laptop Pro | $1499 | laptops |
| 2 | DevopShift Laptop Air | $999 | laptops |
| 3 | DevopShift Phone X | $899 | phones |
| 4 | DevopShift Phone Mini | $599 | phones |
| 5 | DevopShift Headphones Pro | $299 | headphones |
| 6 | DevopShift Earbuds | $149 | headphones |

---

## 5. Visual design — for slide screenshots and brand consistency

### 5.1 Palette
- **Background:** `slate-900` body, `slate-950` header/footer (dark theme).
- **Primary accent:** `cyan-400` for the "Devop" wordmark, prices, hover states, "Topic" badge.
- **Category gradients on product cards/heroes:**
  - laptops → `from-cyan-500 to-blue-700`
  - phones → `from-fuchsia-500 to-purple-700`
  - headphones → `from-amber-500 to-rose-600`
- **Architecture component pills (by `kind`):**
  - client → slate
  - app → cyan
  - storage → emerald
  - cache → rose
  - AI → fuchsia
  - external → amber

### 5.2 Brand wordmark
`<span class="text-cyan-400">Devop</span><span class="text-white">Shift</span>` — cyan "Devop", white "Shift". Sub-line: "A learning lab for the DevopShift Docker course."

### 5.3 Product illustrations
Inline SVG (no binary images): outlined laptop, outlined phone, outlined headphone arc. Rendered white at 95% opacity on the category gradient. Slides can show them or describe them — they're not the focal point; they're a visual anchor.

### 5.4 Architecture timeline visual
Vertical list, left-border rail of `slate-800`, each stage = card. Current stage gets a **pulsing cyan dot** on the rail and a **"You are here"** pill. Components inside each card are colored pills separated by `→` arrows.

> **Slide tip:** the `/architecture` page screenshotted at each branch's state is the cleanest single visual you can put on a "today we are here" slide.

---

## 6. Running the container — reference commands for slides

### 6.1 Topic 3 — students don't build, they pull

```bash
# Pull
docker pull yanivomc/store:1.0

# Run, detached, port-mapped, named
docker run -d -p 5000:5000 --name store yanivomc/store:1.0

# Inspect, curl, log, exec
docker ps
curl http://localhost:5000/health
docker logs -f store
docker exec -it store sh

# Lifecycle
docker stop store
docker start store

# Cleanup
docker rm -f store
docker container prune
```

### 6.2 Useful env vars the image already supports
| Var | Default | Purpose |
|-----|---------|---------|
| `PORT` | `5000` | Override the Flask listening port — handy when 5000 is taken locally (e.g., macOS AirPlay) |
| `APP_ENV` | `dev` | Shown verbatim in `/info` — good `-e APP_ENV=production` demo |

---

## 7. Per-topic deltas — what the slide deck for each topic should highlight

### Topic 3 — Monolith *(built)*
- One container, static JSON inside it.
- Architecture diagram: `Browser → Flask + products.json`
- Pedagogical payoff: containers run; views counter resets on restart (sets up T5).

### Topic 4 — Build it yourself *(built)*
- Same app, no Dockerfile in the repo — students write one across three stages.
- Diagram unchanged: `Browser → Flask + products.json`.
- **Three-stage progression** (one Dockerfile per stage, each in `solutions/` as reference):
  1. **Naive** — `python:3.12`, `COPY . .`, single `pip install`. Builds and runs, ~1 GB.
  2. **Cached** — `python:3.12-slim`, `requirements.txt` copied first, `--no-cache-dir`, explicit copies. ~150 MB; code edits don't bust the pip layer.
  3. **Secure** — adds non-root `app` user (`useradd` + `USER`) and a `HEALTHCHECK` against `/health` using `urllib` (no `curl` in slim).
- Suggested slide arc per stage: build, run, inspect (`docker images`, `docker inspect`, `docker ps` STATUS), then a discussion prompt — e.g. "why does running as non-root matter?"
- Pedagogical payoff: by the end, students have produced the same image they pulled in Topic 3, plus understand *why* the production image looks the way it does (slim, cached, hardened).
- Talking points for slides:
  - "Same code as Topic 3 — the difference today is the Dockerfile."
  - "Touch `app.py`, rebuild. In stage 1, pip re-runs. In stage 2, it doesn't. That's the cache."
  - "`docker ps` STATUS shows `(healthy)` once the HEALTHCHECK kicks in — proof the container can self-report."

### Topic 5 — Persistence *(built)*
- App now has a real `/cart` (HTML at `/cart`, JSON cart count in `/info`). The disabled "Add to cart" button from earlier topics is enabled.
- SQLite at `/data/store.db` stores **both** the cart and the views counter. `DB_PATH` env var overrides the default.
- **No Dockerfile shipped at root** — students evolve their Topic 4 "secure" Dockerfile. The reference answer lives at `solutions/Dockerfile.with-volume` (adds `mkdir -p /data`, `chown app:app /data`, and a `VOLUME /data` declaration).
- **Setup mini-task** before the walkthrough: students add the three Dockerfile lines themselves, *then* build. Reinforces Topic 4 and motivates `VOLUME` as the explicit "this path is for persistent data" declaration.
- **Lab shape** — setup → walkthrough → break it → fix it → fix-it-yourself:
  1. Build & run without `-v` — add to cart — `docker rm -f` — run fresh — cart is empty. The pain.
  2. `docker volume create store-data` + `-v store-data:/data` — repeat the rm/run dance — cart persists.
  3. `docker volume ls` / `docker volume inspect` — point at the Mountpoint as proof.
  4. Brief bind-mount contrast (`-v $(pwd)/dev-data:/data`) — same data, now visible on the host.
- **Fix-it-yourself challenges** (`solutions/CHALLENGE.md`):
  - **A:** wire up the bind mount themselves, prove `./dev-data/store.db` exists, peek with `sqlite3`.
  - **B (stretch):** two containers sharing the same named volume on different ports — demonstrate the cart appearing in both, then surface `database is locked` under concurrent writes (sets up the MySQL move in P2.2).
- Talking points for slides:
  - "The button you've been clicking on since Topic 3 finally works."
  - "Same image, same code — the difference is one `-v` flag."
  - "Named volumes hide the data. Bind mounts expose it. Pick based on whether you're running in production or on your laptop."
  - "Concurrent SQLite writers hit lock errors. That's why P2.2 swaps to MySQL — same volume lesson, different database."

### Topic 6 — Sidecar *(built)*
- Adds the `redis` Python client (only change to `requirements.txt`), a cache-aside layer over `/products` (30 s TTL, JSON-encoded payload), a new HTML-free `/cache` endpoint exposing `{connected, redis_host, hits, misses, ratio, ttl_remaining}`, and a small footer pill that flips green when the cache is up.
- Hits and misses are stored in Redis itself (`cache:hits`, `cache:misses`) so multiple Flask containers share one set of counters — same Redis = same state.
- Cache fails closed: when Redis is unreachable, `/products` falls through to the in-memory list. The app stays up; the footer just shows `Cache: ✗ disconnected`. Real-world resilience pattern, named explicitly in the LAB.
- **Lab shape** — setup (rebuild) → walkthrough → break it → fix it → fix-it-yourself:
  1. Run Flask alone with `-v` for the volume from Topic 5. `/cache` shows disconnected.
  2. Start `redis:7-alpine`, no network flag. `docker exec store getent hosts redis` returns *nothing* — Docker's **default bridge** has no automatic DNS for container names. The two containers can ping by IP, but IPs change.
  3. `docker network create store-net`, re-run both containers with `--network store-net`. `getent` now resolves, footer flips to **`Cache: ✓`**, hit ratio climbs as you refresh `/products`.
  4. `docker network inspect store-net` — point at the embedded DNS.
- **Fix-it-yourself challenges** (`solutions/CHALLENGE.md`):
  - **A:** run a one-shot `redis-cli` container on `store-net`, `KEYS *`, `FLUSHALL`, watch `/cache` reset. Demonstrates that DNS is a network property, not a Flask property.
  - **B (stretch):** two `store` containers on different ports sharing the same Redis (and the same volume). Both see the same cart **and** the same cache stats — sets up "why a database server beats a database file" right before the MySQL move in P2.2.
- Talking points for slides:
  - "Default bridge: containers can ping by IP. User-defined network: containers can ping by name."
  - "`docker volume` auto-creates, `docker network` does not — that's intentional. Networks are a contract."
  - "The footer changed from a red ✗ to a green ✓ because of *one* `docker run` flag: `--network store-net`."
  - "Two Flask containers, one Redis. Same hit counters in both — that's what 'shared state' actually means."

### Topic P2.1 — Multi-stage + Bake *(built)*
- **Repo layout changes for the first time**: sub-folders `store/` (Flask context) and `redis/` (custom image context), `docker-bake.hcl` at root, `solutions/` parallels both.
- **App evolves to production shape**, not just packaging:
  - Tailwind CDN replaced by a real build step. `store/package.json` ships the Tailwind CLI dep; templates reference `static/style.css`. The CDN `<script>` warning ("not for production") is gone.
  - `python app.py` (Flask dev server) replaced by `gunicorn -w 4 -b 0.0.0.0:5000 app:app`. `gunicorn` added to `requirements.txt`. The dev-server warning is gone from `docker logs`.
- **Three-stage Dockerfile** for `store/`:
  1. `css` — `node:20-alpine`, `npx tailwindcss --minify`. Node toolchain (~100 MB) does not ship.
  2. `pybuild` — `python:3.12-slim`, `pip install --prefix=/install`. Pip cache + build tooling don't ship.
  3. runtime — `python:3.12-slim`, `COPY --from=css …`, `COPY --from=pybuild …`, non-root `app` user, `HEALTHCHECK`, `VOLUME /data`, `CMD gunicorn …`.
- **Custom Redis image** in `redis/`: `FROM redis:7-alpine` + `apk add curl` + `COPY redis.conf` + `HEALTHCHECK redis-cli ping`. The `redis.conf` carries two opinionated lines: `maxmemory 256mb`, `appendonly yes`.
- **Docker Bake** in `docker-bake.hcl`: two targets (`store-app`, `store-db`), each with `:p2.1` + `:latest` tags and registry-side `cache-from` / `cache-to`. `group "default"` builds both. `docker buildx bake` builds in parallel; `bake --push` publishes — which is what subsumes Topic 7.
- **Lab shape** — setup → three stages → run-the-stack → stretch:
  - **Stage 1**: rewrite `store/Dockerfile` as multi-stage (reference: `solutions/Dockerfile.store`).
  - **Stage 2**: write `redis/Dockerfile` (reference: `solutions/Dockerfile.redis`).
  - **Stage 3**: fill TODO gaps in `docker-bake.hcl` (reference: `solutions/docker-bake.hcl`).
  - Run the full stack with the baked images and confirm production fingerprints: styled UI from local build, gunicorn workers in logs, no dev-server warning.
- **Stretch challenges** (`solutions/CHALLENGE.md`):
  - **A — Multi-platform** (`linux/amd64,linux/arm64`) via `platforms = [...]` on the target.
  - **B — Multi-registry** push (Docker Hub + GHCR) by listing additional tags.
- Talking points for slides:
  - "The image you ship is what runs. Everything else is build-time scaffolding."
  - "`docker logs` used to say 'do not use the development server'. Now it says workers started."
  - "Bake is just a manifest of what to build. `--push` extends it to what to ship."
  - "Multi-platform images aren't optional anymore — Apple Silicon laptops pulled the rug on x86-only builds."

### Topic P2.2 — Compose stack *(planned)*
- Full Compose: Flask + MySQL (replaces SQLite) + Redis + Ollama for `/recommend`.
- Diagram: `Browser → Flask → MySQL` + `Redis` + `Ollama`.
- Payoff: declarative orchestration vs the `docker run` flags they've memorized.

---

## 8. Out of scope — do NOT include in early slides
- Kubernetes, Helm, swarm — different course.
- Authentication, real payments — never; it's a teaching app.
- Cart functionality before Topic 5 — the button is intentionally disabled and labeled.
- `/recommend` (Ollama) before P2.2.
- Multi-stage Dockerfile before P2.1.

---

## 9. Tone for course content
- Practical, hands-on, slightly dry.
- Lead with the command, follow with the why.
- Reuse the app's own copy where possible — "Block out the entire open office", "The flagship pager" — keeps brand voice consistent between slide and screen.
- No hype, no emojis (the app itself uses none).

---

## 10. File map (for slides showing the codebase)

**Topic P2.1 branch** (current `main`) — **first branch with sub-folders**:

```
.
├── store/                  # Flask app — Bake build context "./store"
│   ├── app.py              # CURRENT_TOPIC="P2.1", Topic 7 entry removed
│   ├── products.json
│   ├── requirements.txt    # adds gunicorn==22.0.0
│   ├── package.json        # tailwindcss CLI (devDependencies)
│   ├── tailwind.config.js  # scans templates/**/*.html
│   ├── src/input.css       # @tailwind base/components/utilities
│   ├── .dockerignore
│   ├── templates/
│   │   ├── base.html       # <link rel="stylesheet" href="/static/style.css">
│   │   ├── index.html
│   │   ├── product.html
│   │   ├── cart.html
│   │   ├── architecture.html
│   │   ├── 404.html
│   │   └── _macros.html
│   └── Dockerfile          # topic-6 single-stage — students rewrite this
├── redis/                  # custom Redis image — Bake build context "./redis"
│   ├── redis.conf          # maxmemory 256mb + appendonly yes
│   └── (Dockerfile)        # students write this
├── docker-bake.hcl         # skeleton with TODO gaps
├── solutions/
│   ├── README.md
│   ├── Dockerfile.store    # multi-stage reference (Node + pybuild + runtime)
│   ├── Dockerfile.redis    # custom redis reference
│   ├── docker-bake.hcl     # filled-in Bake reference
│   └── CHALLENGE.md        # multi-platform + multi-registry stretches
├── .gitignore
├── LAB.md                  # P2.1 setup + 3 stages + run + stretch
├── SPEC.md                 # this file
└── CLAUDE.md               # original course-author spec (T3 focused)
```

**Sub-folders are new in P2.1** — every previous branch was flat at the root. The split is intentional: `docker buildx bake` declares one `context` per target, and each target's context is its own folder.

**How earlier branches differ:**
- **`topic-3`**: flat layout, root `Dockerfile`, no `LAB.md` / `solutions/` / `cart.html`, app.py uses in-memory `Counter`, no SQLite, no Redis, "Add to cart" button disabled.
- **`topic-4`**: flat layout, **no** root `Dockerfile` (students write it), `solutions/Dockerfile.{naive,cached,secure}` reference set. No SQLite or Redis.
- **`topic-5`**: flat layout, no root `Dockerfile` (students evolve their Topic 4 one), `solutions/Dockerfile.with-volume` reference. App has SQLite but no Redis; footer shows "Views (persisted)" but no Cache pill.
- **`topic-6`**: flat layout, root `Dockerfile` is back (same shape as topic-5's `with-volume`). App has both SQLite and Redis cache-aside. Footer has the Cache ✓/✗ pill. Templates still use Tailwind CDN, Flask still runs via `python app.py`.
