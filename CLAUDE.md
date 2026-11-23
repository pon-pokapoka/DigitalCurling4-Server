# DigitalCurling4-Server (pon-pokapoka fork) — notes for Claude Code

A fork of digitalcurling/DigitalCurling4-Server. Its own work, on
`k8s-postgres`, runs the server on Kubernetes: authentication in
Postgres (CloudNativePG), Redis between replicas, manifests in `k8s/`
(see `k8s/README.md`).

## Working in this repo

- **Branches.** Branch from `k8s-postgres` and open a PR against it.
  Never push straight to it. Commits are signed; never bypass a signing
  failure.
- **Upstream stays clean.** This file and the Kubernetes work are not for
  digitalcurling/DigitalCurling4-Server unless proposed on purpose.
  Anything proposed upstream starts from a branch off upstream's
  branch, not `k8s-postgres`.
- **`k8s/` holds only what every cluster needs.** One cluster's settings
  (a fixed ClusterIP, a node's hostname, a PV bound by hostname, an image
  registry) go in a kustomize overlay outside this repository that uses
  `k8s/` as its base, pinned by commit (`?ref=`). Never add them to
  `k8s/`.
- **Images are pinned by commit.** `k8s/image.sh` builds
  `digitalcurling4-server:<short commit>` from the committed sources and
  sets that tag in `k8s/kustomization.yaml`; commit the change. Quote the
  tag: an all-digit short commit is a YAML number.
- **Public repo:** no hostnames, registry addresses, namespaces of a
  real cluster, or passwords. Logins live in the cluster's Secret;
  examples use placeholders (`k8s/secret.example.yaml`, `CHANGE_ME`).
- **Tests:** `pytest` in `tests/`, with the `dev` extra installed
  (`uv sync --extra dev`).
- Write in English.
