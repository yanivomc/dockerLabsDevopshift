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
| 4 | Build it yourself | Same architecture; student writes the Dockerfile | Code reused from T3 |
| 5 | Persistence | + SQLite on a named volume (cart survives restarts) | Planned |
| 6 | Sidecar | + Redis on a user-defined network (cache `/products`) | Planned |
| 7 | Publish | + Push to Docker Hub + GHCR | Planned |
| P2.1 | Slim down | Multi-stage build to shrink image | Planned |
| P2.2 | Compose stack | Flask + MySQL + Redis + Ollama (`/recommend`) | Planned |

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

### Topic 4 — Build it yourself *(planned, same code)*
- Students write a Dockerfile from scratch (existing one becomes reference).
- Diagram unchanged. Payoff: "you can produce the same image you pulled in T3."
- Likely slide arc: layers, `COPY`, `RUN`, `CMD`, `.dockerignore`, image size.

### Topic 5 — Persistence *(planned)*
- Add SQLite, expose `/cart` endpoint, mount a named volume at `/data`.
- Diagram adds: `SQLite (volume)`.
- Payoff: views counter / cart survives `docker rm` + `docker run` because the volume persists.

### Topic 6 — Sidecar *(planned)*
- Add a Redis container, user-defined bridge network, cache `/products` reads.
- Diagram adds: `Redis (sidecar)`.
- Payoff: two containers talk by name, not IP.

### Topic 7 — Publish *(planned)*
- Tag and push the image to Docker Hub and GHCR.
- Diagram adds: `Registry` (external).
- Payoff: someone else can `docker pull` your image, just like they did with `yanivomc/store:1.0` in Topic 3.

### Topic P2.1 — Slim down *(planned)*
- Multi-stage Dockerfile. Compare image sizes before/after.
- Diagram unchanged in shape, but the "Flask" pill gets relabeled `Flask (slim)`.

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

```
.
├── app.py                  # Flask routes, ARCHITECTURE_STAGES, CURRENT_TOPIC
├── products.json           # 6 products with specs
├── requirements.txt        # flask==3.0.3
├── Dockerfile              # python:3.12-slim, copy, EXPOSE 5000
├── .dockerignore
├── .gitignore
├── templates/
│   ├── base.html           # shared chrome + architecture badge
│   ├── index.html          # storefront + category filter
│   ├── product.html        # detail page + specs + disabled cart
│   ├── architecture.html   # course timeline
│   ├── 404.html
│   └── _macros.html        # inline SVG product icons
└── CLAUDE.md               # original course-author spec (T3 focused)
```
