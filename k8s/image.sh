#!/usr/bin/env bash
# Build the server image from a commit, push it to a registry or load it into
# the node's containerd, and point k8s/kustomization.yaml at it.
#
#   k8s/image.sh [<git ref>]        # default HEAD
#
# The image is digitalcurling4-server:<short commit>, built from the committed
# sources at <git ref>, so local changes don't leak in.
# IMAGE_IMPORT_CMD loads a `docker save` tarball from stdin on the node, e.g.
#   IMAGE_IMPORT_CMD='ssh root@<node> ctr -n k8s.io images import -'
# IMAGE_REGISTRY pushes it to a registry instead, as
# $IMAGE_REGISTRY/digitalcurling4-server:<short commit> (docker login first);
# point your overlay's images: newName there.
# With neither set, the image is only built, and you load it yourself.
set -euo pipefail

if [[ $# -gt 1 ]]; then
  sed -n '2,16p' "$0" >&2
  exit 1
fi
ref="${1:-HEAD}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
commit="$(git -C "$repo_root" rev-parse --short "$ref^{commit}")"
image="digitalcurling4-server:$commit"

git -C "$repo_root" archive --format=tar "$commit" | docker build \
  --label org.opencontainers.image.source=https://github.com/pon-pokapoka/DigitalCurling4-Server \
  --label org.opencontainers.image.revision="$(git -C "$repo_root" rev-parse "$commit")" \
  --label org.opencontainers.image.licenses=MIT \
  -t "$image" -
echo "built $image" >&2

if [[ -n "${IMAGE_REGISTRY:-}" ]]; then
  remote="${IMAGE_REGISTRY%/}/$image"
  docker tag "$image" "$remote"
  docker push "$remote"
  echo "pushed $remote" >&2
elif [[ -n "${IMAGE_IMPORT_CMD:-}" ]]; then
  docker save "$image" | bash -c "$IMAGE_IMPORT_CMD"
  echo "imported $image" >&2
else
  echo "Neither IMAGE_REGISTRY nor IMAGE_IMPORT_CMD is set: load $image into the node yourself." >&2
fi

kustomization="$repo_root/k8s/kustomization.yaml"
sed -i -E "/- name: digitalcurling4-server/{n;s/newTag: .*/newTag: $commit/}" "$kustomization"
echo "k8s/kustomization.yaml now uses $image: commit it, then kubectl apply -k k8s" >&2
