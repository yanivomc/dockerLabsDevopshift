🔧 Topic 3 Lab — "Running Containers" — Spec Proposal
What Topic 3 Teaches
docker run, flags (-d, -p, -e, --name, --rm), lifecycle (start/stop/rm), exec, logs, inspect, ps, cleanup. No Dockerfile yet — students pull a pre-built image.

The App — devopshift-store Stage 1
For Topic 3, students pull a pre-built image from our registry (we push it ahead of time). They don't build anything yet — that's Topic 4.

What the app should show:

devopshift-store/
├── app.py              # Flask BE — /products, /health, /
├── templates/
│   └── index.html      # Simple storefront UI — product cards
├── requirements.txt
└── products.json       # Static data (no DB yet — Topic 5)
What the student sees in the browser:

A clean storefront — devopshift-store branding
Product cards (5-6 products: laptops, phones, headphones)
A /health endpoint returning JSON — great for curl demos
A /products endpoint returning JSON — shows the API
Why static data (no DB) for Topic 3:

Students aren't running compose yet — one container only
Volume persistence comes in Topic 5
Keeps the docker run command simple: docker run -d -p 5000:5000 --name store devopshift/store:1.0
Lab Stages — Topic 3
Stage	Task	What They Learn
1	docker pull devopshift/store:1.0	Pull from registry, layer downloads
2	docker run -d -p 5000:5000 --name store devopshift/store:1.0	Detached, port mapping, naming
3	docker ps + browse http://EC2_IP:5000	Verify running, see the UI
4	docker logs -f store	Live log streaming, Flask request logs
5	docker exec -it store sh	Shell into running container, explore FS
6	docker stop store + docker start store	Lifecycle — data survives restart (no DB yet)
7	docker inspect store	JSON metadata — ports, mounts, network, env
8	docker rm -f store + docker container prune	Cleanup patterns
The Code We Need to Build
app.py — Flask app:

GET /          → HTML storefront (product cards)
GET /products  → JSON list of products
GET /health    → {"status": "ok", "version": "1.0"}
GET /info      → {"hostname": container_id, "env": ...}  
               # great for showing container isolation
templates/index.html — Simple, clean UI:

DevopShift branding
Product grid (cards with image, name, price)
Shows hostname/container ID in footer — great for scaling demos later
products.json — Static data:

[
  {"id": 1, "name": "DevopShift Laptop", "price": 999, "category": "hardware"},
  {"id": 2, "name": "Cloud Keyboard", "price": 129, "category": "hardware"},
  ...
]
What Gets Added in Later Topics
Topic	Addition to the app
Topic 4	Students write the Dockerfile themselves
Topic 5	SQLite → named volume for cart persistence
Topic 6	Redis sidecar → /cache endpoint, user-defined network
Topic 7	Push their own built image to Docker Hub + GHCR
Part II T1	Multi-stage build — shrink the image
Part II T2	Full Compose: Flask + MySQL + Redis
Part II T2	Add Ollama service → /recommend endpoint
