# Topic 4 — Build it yourself

You ran this app in Topic 3 by pulling a pre-built image. Today you build it.

## What's in the repo

```
app.py
products.json
requirements.txt
templates/
LAB.md           (this file)
solutions/       (reference Dockerfiles — peek only if stuck)
```

You have **no Dockerfile**. Write one.

## Goal

By the end of this lab you'll have written three Dockerfiles, each better than the last:

1. **Naive** — enough to build and run.
2. **Cached** — slim base + layer ordering so rebuilds are fast.
3. **Secure** — non-root user with a working `HEALTHCHECK`.

The app listens on port `5000` and serves `/health`, `/products`, and the HTML store at `/`.

---

## Stage 1 — Naive: make it work

Write a file named `Dockerfile` that:

- Uses `python:3.12` as the base.
- Sets `/app` as the working directory.
- Copies everything in with `COPY . .`.
- Installs dependencies: `pip install -r requirements.txt`.
- Exposes port 5000.
- Runs `python app.py`.

Then build, run, and check:

```bash
docker build -t store:naive .
docker run -d -p 5000:5000 --name store store:naive
curl http://localhost:5000/health
docker images store:naive
```

**Discuss:**
- How big is the image?
- Touch `app.py` and rebuild. Does `pip install` re-run?

---

## Stage 2 — Cached: smaller and faster rebuilds

Rewrite your `Dockerfile`:

- Base: `python:3.12-slim`.
- Copy `requirements.txt` and `pip install` **before** copying your code.
- Use `pip install --no-cache-dir`.
- Copy code files explicitly (e.g. `COPY app.py products.json ./`, `COPY templates ./templates`).

```bash
docker rm -f store
docker build -t store:cached .
docker images store:cached
# Touch app.py and rebuild — only the COPY layer should redo
docker run -d -p 5000:5000 --name store store:cached
```

**Discuss:**
- What shrunk? By how much?
- Why is the rebuild faster?
- What did `--no-cache-dir` save you?

---

## Stage 3 — Secure: non-root + healthcheck

Add to your `Dockerfile`:

- A non-root user named `app` (`useradd ...`), then switch with `USER app`.
- A `HEALTHCHECK` that hits `/health` and considers the container unhealthy if it fails.

```bash
docker rm -f store
docker build -t store:secure .
docker run -d -p 5000:5000 --name store store:secure
docker inspect store --format '{{.Config.User}}'   # expect: app
docker ps                                          # STATUS shows (healthy) after ~10s
```

**Discuss:**
- Why does running as non-root matter?
- What happens to `docker ps` STATUS if `/health` starts returning 500?

---

## Stuck?

Reference Dockerfiles for all three stages live in `solutions/`. Write your own first.
