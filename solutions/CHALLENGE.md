# Topic 5 — Challenge solutions

Write your own first. These are the reference answers for after you have something working.

## Challenge A — Bind mount, end to end

```bash
docker rm -f store 2>/dev/null
mkdir -p ./dev-data
docker run -d -p 5000:5000 --name store \
  -v "$(pwd)/dev-data:/data" \
  store:topic5

# Visit http://localhost:5000, add a product to the cart.

ls ./dev-data
# → store.db

sqlite3 ./dev-data/store.db '.tables'
# → cart_items  page_views

sqlite3 ./dev-data/store.db 'SELECT product_id, quantity, added_at FROM cart_items;'
# → rows for whatever you added
```

### Why this is interesting

Same container, same image — but the data file is now sitting in your home directory. You can edit it, back it up with `cp`, or even hand-edit rows with `sqlite3`.

> **Watch the user IDs.** The container runs as user `app` (uid 1000). On a Linux host, the file appears owned by host uid 1000 (which may or may not be you). On macOS / Docker Desktop, the VM transparently maps it back to your user. This is one place where dev experience differs across platforms.

---

## Challenge B (stretch) — Two containers, one volume

```bash
docker volume create store-data
docker rm -f store1 store2 2>/dev/null

docker run -d -p 5000:5000 --name store1 -v store-data:/data store:topic5
docker run -d -p 5001:5000 --name store2 -v store-data:/data store:topic5
```

Add an item via http://localhost:5000, then visit http://localhost:5001/cart — same items.

### Now try to break it

```bash
# Hammer both endpoints with concurrent writes.
for i in $(seq 1 50); do
  curl -s -X POST http://localhost:5000/cart/add/1 -o /dev/null &
  curl -s -X POST http://localhost:5001/cart/add/2 -o /dev/null &
done
wait
docker logs store1 2>&1 | grep -i 'lock' | head
docker logs store2 2>&1 | grep -i 'lock' | head
```

You may see `database is locked` errors. SQLite is built for **one writer at a time** and serialises everything via file locks. Those locks work on local filesystems and on `volume` and `bind` mounts to a local path, but they do **not** work over NFS or some network filesystems.

### Why this matters for the rest of the course

- **Topic 6 — Sidecar**: we keep SQLite but add a Redis cache in front of it. Reads stop hitting SQLite as often, so the writer bottleneck matters less.
- **Topic P2.2 — Compose stack**: we swap SQLite for MySQL. MySQL is a server, not a file — it is built for many clients writing at once. The volume lesson is identical; only the database changes.

The volume teaches us *how* to persist. SQLite teaches us *why we'll outgrow it*.

---

## Cleanup

```bash
docker rm -f store store1 store2 2>/dev/null
docker volume rm store-data
rm -rf ./dev-data
```
