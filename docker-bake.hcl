# DevopShift Store — Docker Bake spec (Topic P2.1)
#
# Fill the TODO gaps so `docker buildx bake` builds both images
# (store-app and store-db) in parallel. Use `--push` to publish.

variable "TAG" {
  default = "p2.1"
}

variable "REGISTRY" {
  default = "localhost"  # TODO: change to your registry (e.g. yanivomc, ghcr.io/yanivomc)
}

# ----------------------------------------------------------------------------
# Targets — one per image we publish.

target "store-app" {
  context    = "./store"
  dockerfile = "Dockerfile"
  tags       = ["${REGISTRY}/store:${TAG}"]   # TODO: add a :latest tag alongside
  # TODO: add a cache-from line that reads from this image's own registry tag
}

target "store-db" {
  # TODO: fill context (./redis)
  # TODO: fill dockerfile (Dockerfile)
  # TODO: fill tags — at least ${REGISTRY}/store-db:${TAG}
}

# ----------------------------------------------------------------------------
# Groups — what `docker buildx bake` builds when no target is named.

group "default" {
  # TODO: list both targets so a bare `docker buildx bake` builds them
  targets = []
}
