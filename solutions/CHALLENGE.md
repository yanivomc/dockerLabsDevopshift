# Topic P2.1 — Stretch challenges

The three stages in `LAB.md` are the lab. These are stretch goals once everything builds and pushes cleanly.

## Stretch A — Multi-platform images

A single `target` can produce both `linux/amd64` and `linux/arm64` images in one bake call (so Apple Silicon laptops and x86 servers pull the right one).

```hcl
target "store-app" {
  context    = "./store"
  dockerfile = "Dockerfile"
  tags       = ["${REGISTRY}/store:${TAG}", "${REGISTRY}/store:latest"]
  platforms  = ["linux/amd64", "linux/arm64"]
}
```

Bake needs a builder that supports multi-platform — `docker buildx create --use --name multi` once, then `docker buildx bake --push` does the rest. Note that `--push` is required for multi-platform (the local docker daemon can only load one architecture).

## Stretch B — Two registries in one bake

Bake will push a single image to *every* tag listed in `tags`. So pushing the same artifact to Docker Hub and GHCR is just two tags:

```hcl
target "store-app" {
  tags = [
    "${REGISTRY}/store:${TAG}",
    "${REGISTRY}/store:latest",
    "ghcr.io/${REGISTRY}/store:${TAG}",
    "ghcr.io/${REGISTRY}/store:latest",
  ]
}
```

Auth both registries first (`docker login` for Docker Hub, `docker login ghcr.io` for GHCR). Then `docker buildx bake --push` writes to both in one shot.

## Why these matter

- **Multi-platform** is what real registries actually serve. Mac M-series laptops have made `arm64` images non-negotiable.
- **Multiple registries** is how teams handle vendor lock-in (mirror to a private registry), residency (region-specific mirrors), and air-gapped customers (internal registry only).

Both stretches use the same Bake file — that's the whole point of the abstraction.
