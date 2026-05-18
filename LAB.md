# Topic 5 — Persistence

You can run a container (Topic 3) and build one (Topic 4). Today: make the data survive when the container does not.

This branch ships with a working `Dockerfile` and a real `/cart` page — the disabled button from Topic 3 is finally enabled. The app stores its data in SQLite at `/data/store.db` *inside* the container.

The lesson is about *behaviour*: why data dies, and how volumes fix it.

---

## Walkthrough

### Step 1 — Run without a volume. Feel the pain.

```bash
docker build -t store:topic5 .
docker run -d -p 5000:5000 --name store store:topic5
```

Open http://localhost:5000. Add a few items to your cart. Refresh — the count in the nav rises. Visit `/cart` — items are there.

Now destroy the container and start a fresh one from the same image:

```bash
docker rm -f store
docker run -d -p 5000:5000 --name store store:topic5
```

Visit `/cart`. **Empty.**

> The container's writable layer was destroyed with `docker rm`. The SQLite file lived inside that layer. The data is gone because the storage went with the container.

### Step 2 — Add a named volume.

```bash
docker rm -f store
docker volume create store-data
docker run -d -p 5000:5000 --name store -v store-data:/data store:topic5
```

Add items again. Then:

```bash
docker rm -f store
docker run -d -p 5000:5000 --name store -v store-data:/data store:topic5
```

Visit `/cart`. **Your items are still there.** The volume outlived the container.

### Step 3 — Inspect the volume

```bash
docker volume ls
docker volume inspect store-data
```

`Mountpoint` is where Docker stores the volume on the host. On a real engine you cannot read it directly (it lives under Docker's root, owned by root). On macOS / Docker Desktop it lives inside the LinuxKit VM — same idea.

### Step 4 — Bind mount as a contrast

Named volumes hide the data. A *bind mount* makes the same data visible on your host filesystem — useful for local development and for poking at the DB with tools.

```bash
docker rm -f store
mkdir -p ./dev-data
docker run -d -p 5000:5000 --name store -v "$(pwd)/dev-data:/data" store:topic5
```

After adding items, on your host:

```bash
ls ./dev-data
sqlite3 ./dev-data/store.db 'SELECT * FROM cart_items;'   # if you have sqlite3
```

You can see and edit the file with normal host tools.

> **Named volume vs bind mount — when to use each:**
> - **Named volume** for *production data*: lifecycle owned by Docker, portable across machines, survives `docker rm`.
> - **Bind mount** for *development*: you can edit/inspect the data with host tools, but the path is host-specific.

---

## Fix it yourself

Two challenges. Try them before peeking at [solutions/CHALLENGE.md](solutions/CHALLENGE.md).

### Challenge A — Bind mount, end to end

Wire up a fresh container that bind-mounts a directory of your choosing onto `/data`. Confirm by listing the directory on the host and seeing `store.db`. Bonus: open the DB with `sqlite3` and run a `SELECT` against `cart_items`.

### Challenge B (stretch) — Two containers, one volume

Two developers want to share the same cart data. Run two containers on different host ports (e.g. `5000` and `5001`), both pointing at the same named volume. Add an item via one container, verify the other one sees it.

When it works, also try to make both containers add items at the same time and notice what happens. (Hint: SQLite is single-writer. This is exactly *why* Topic P2.2 swaps to MySQL.)

---

## Cleanup

```bash
docker rm -f store store2 2>/dev/null
docker volume rm store-data
rm -rf ./dev-data
```

---

## Pedagogical hooks the slides can call out

| What | Why it lands |
|------|--------------|
| The cart works for the first time ever | Pays off the disabled "unlocks in Topic 5" button students saw three labs ago |
| Footer **"Views (persisted)"** counter | Was "resets on restart" before; the tooltip change literally tells the story |
| `/cart` page's cyan callout | Tells the student exactly which `docker run` flag is doing the work |
| `docker volume inspect` Mountpoint | Tangible proof there's *somewhere* on disk holding the bytes |
| Bind mount + `sqlite3 ./dev-data/store.db` | Lets students see "containerised app, host-visible data" simultaneously |
