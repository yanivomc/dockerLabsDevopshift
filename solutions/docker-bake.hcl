# docker-bake.hcl — reference answer for Topic P2.1.
#
# `docker buildx bake` reads this file and builds every target in
# `group "default"` in parallel. Add `--push` to publish in the same step.

variable "TAG" {
  default = "p2.1"
}

variable "REGISTRY" {
  default = "yanivomc"  # change to your Docker Hub or GHCR namespace
}

target "store-app" {
  context    = "./store"
  dockerfile = "Dockerfile"
  tags = [
    "${REGISTRY}/store:${TAG}",
    "${REGISTRY}/store:latest",
  ]
  cache-from = ["type=registry,ref=${REGISTRY}/store:cache"]
  cache-to   = ["type=registry,ref=${REGISTRY}/store:cache,mode=max"]
}

target "store-db" {
  context    = "./redis"
  dockerfile = "Dockerfile"
  tags = [
    "${REGISTRY}/store-db:${TAG}",
    "${REGISTRY}/store-db:latest",
  ]
  cache-from = ["type=registry,ref=${REGISTRY}/store-db:cache"]
  cache-to   = ["type=registry,ref=${REGISTRY}/store-db:cache,mode=max"]
}

group "default" {
  targets = ["store-app", "store-db"]
}
