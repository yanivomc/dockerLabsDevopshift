# Topic 6 — Challenge solutions

Write your own first. These are reference answers for after you have something working.

## Challenge A — Same network, third container

Run a one-shot `redis-cli` on `store-net` and talk to Redis by name:

```bash
# List the cache keys
docker run --rm --network store-net redis:7-alpine \
  redis-cli -h redis KEYS '*'
# → cache:hits
# → cache:misses
# → products:all
```

```bash
# Read the cached payload (truncated)
docker run --rm --network store-net redis:7-alpine \
  redis-cli -h redis GET products:all | head -c 200
```

```bash
# Flush everything
docker run --rm --network store-net redis:7-alpine \
  redis-cli -h redis FLUSHALL
# → OK
```

Now refresh http://localhost:5000/cache in your browser:

```json
{ "connected": true, "hits": 0, "misses": 0, "ttl_remaining": null, ... }
```

Hit `/products` once more — `misses: 1` and a new TTL appears.

### Why this is interesting

You named **one** thing (`redis`) and resolved it from **two different containers** (your `store` *and* this one-shot `redis-cli`). Neither knew the IP. Docker's embedded DNS server on `store-net` did the work. That's the entire promise of user-defined networks.

---

## Challenge B (stretch) — Two store containers, one cache

```bash
docker rm -f store store2 2>/dev/null
docker run -d --name store  --network store-net -p 5000:5000 -v store-data:/data store:topic6
docker run -d --name store2 --network store-net -p 5001:5000 -v store-data:/data store:topic6
```

Add an item via http://localhost:5000, then visit http://localhost:5001/cart — same items (shared volume) **and** http://localhost:5001/cache shows the *same* hit/miss counters as http://localhost:5000/cache.

### Why this scales where SQLite did not

In Topic 5's Challenge B, two Flask containers writing to the same SQLite file hit `database is locked` because SQLite is a **file with locks**, designed for one writer at a time.

Redis is a **server process**. It accepts connections from any number of clients and serialises commands internally — there are no host-side locks to contend over. Two store containers, ten store containers, a Lambda function — they all just open a TCP connection and ask.

That distinction (file-based store vs. server-based store) is the reason Topic P2.2 moves from SQLite to MySQL: same volume lesson, but now the database can keep up with multiple containers.

---

## Cleanup

```bash
docker rm -f store store2 redis 2>/dev/null
docker network rm store-net
docker volume rm store-data
```
