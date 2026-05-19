# Topic 6 — Sidecar

You can build (Topic 4), run (Topic 3), and persist (Topic 5). Today: **two containers talking to each other**.

The app now wants to cache `/products` reads through Redis. Redis is its own container. The lesson is *how* they find each other — by name, not by IP — and what you have to set up for that to work.

The repo ships with a `Dockerfile` (same shape as Topic 5; the only change today is `redis` in `requirements.txt`) and the app already does cache-aside reads against Redis. You don't have to write any Python.

---

## Setup — Rebuild the image

```bash
docker build -t store:topic6 .
```

The rebuild adds the `redis` Python client. Nothing else changed.

---

## Walkthrough

### Step 1 — Run Flask alone. Watch the cache fail closed.

```bash
docker rm -f store 2>/dev/null
docker volume create store-data 2>/dev/null
docker run -d -p 5000:5000 --name store -v store-data:/data store:topic6
```

Open http://localhost:5000/cache:

```json
{ "connected": false, "redis_host": "redis", ... }
```

The app is *trying* to reach a host called `redis` that doesn't exist yet. `/products` still works — it falls through to the in-memory data when the cache is unreachable. **Cache-aside is supposed to fail gracefully.** Good design.

Look at the footer of any page: **`Cache: ✗ disconnected`**.

### Step 2 — Start Redis. Try to connect on the default bridge.

```bash
docker run -d --name redis redis:7-alpine
```

`store` and `redis` are now both running, both attached to Docker's **default bridge network**. Reload `/cache`:

```json
{ "connected": false, ... }
```

Still disconnected. Why?

```bash
docker exec store getent hosts redis
# → (no output, exit 2)

docker network inspect bridge --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
# → store      172.17.0.2/16
# → redis      172.17.0.3/16
```

Both containers are there. Both have IPs. But `getent hosts redis` returns nothing — **the default bridge has no automatic DNS for container names.** Disabled since Docker 1.10.

You *could* reach Redis by IP (`172.17.0.3`), but IPs change every time you `docker run`. That's not a stable contract between services.

### Step 3 — Fix it with a user-defined network

```bash
docker rm -f store redis
docker network create store-net
```

> **Implicit vs explicit, again:** Docker doesn't auto-create networks on first use the way it auto-creates volumes — you must run `docker network create` (or use Compose, which calls this for you). Networks are always explicit.

```bash
docker run -d --name redis --network store-net redis:7-alpine
docker run -d --name store --network store-net -p 5000:5000 \
  -v store-data:/data store:topic6
```

Reload `/cache`:

```json
{ "connected": true, "redis_host": "redis", "hits": 0, "misses": 1, ... }
```

`misses: 1` because the first `/cache` call populated the products cache. Now refresh `/products` a few times:

```json
{ "hits": 6, "misses": 1, "ratio": 0.857 }
```

The hit ratio climbs. The footer flips to **`Cache: ✓ 85%`** in green.

### Step 4 — Inspect the user-defined network

```bash
docker network inspect store-net --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
# → store      172.18.0.3/16
# → redis      172.18.0.2/16

docker exec store getent hosts redis
# → 172.18.0.2  redis
```

On a user-defined network, **Docker runs an embedded DNS server** that resolves container names to their current IPs. That's the entire payoff of this lesson.

---

## Fix it yourself

Two challenges. Try them before peeking at [solutions/CHALLENGE.md](solutions/CHALLENGE.md).

### Challenge A — Same network, third container

Run a one-shot `redis-cli` container on `store-net`. From it:
1. List all the cache keys (`KEYS *`).
2. Read the cached product list (`GET products:all`).
3. Flush the cache (`FLUSHALL`).
4. Refresh `/cache` in your browser — verify hits and misses reset to 0 and the next `/products` is a miss.

You should not need to know any container's IP. Name resolution does all the work.

### Challenge B (stretch) — Two store containers, one cache

Run a second `store` container on the same `store-net` and a different host port (e.g. 5001). Add an item to the cart from one, refresh the other — same items (volume) **and** same cache stats (Redis). Why does this work where two SQLite writers from Topic 5's Challenge B fought each other? (Hint: Redis is a server, not a file.)

---

## Cleanup

```bash
docker rm -f store store2 redis 2>/dev/null
docker network rm store-net
docker volume rm store-data
```

---

## Pedagogical hooks the slides can call out

| What | Why it lands |
|------|--------------|
| Footer flips `Cache: ✗` → `Cache: ✓ 85%` | Live, visible payoff for one `docker network create` + `--network` |
| `getent hosts redis` empty on default bridge, populated on user-defined | One-line proof of the DNS difference |
| `/cache` `hits` and `misses` counters in Redis | Both Flask containers share the same metrics — same Redis = same state |
| `docker volume` auto-creates, `docker network` does not | Tiny consistency lesson that primes Compose (P2.2) |
| Cache-aside falls back gracefully when Redis is down | Real-world resilience pattern — slides can name it explicitly |
