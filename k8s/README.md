# Running on Kubernetes

The server and Redis run as Deployments, and Postgres as a CloudNativePG
`Cluster` with one instance. The server keeps no state of its own, so it can
run several replicas: Postgres holds the matches and the logins, and Redis
carries events between replicas.

All of it runs on one dedicated node, the one labeled
`digitalcurling.io/server=true`. Postgres is pinned there through its local
volume, and the server and Redis require the label. If the node is gone they
stay Pending rather than start elsewhere, since they can't do anything useful
without Postgres. A preference would also be a trap: a pod placed on another
node while this one was briefly unavailable would never move back.

## Prepare the cluster

1. Install the CloudNativePG operator, once per cluster:

    ```bash
    kubectl apply --server-side -f \
      https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.30/releases/cnpg-1.30.1.yaml
    kubectl -n cnpg-system rollout status deploy/cnpg-controller-manager
    ```

1. Label and taint the node, so that only this workload runs there. The
   operator needs another node to run on, because it doesn't tolerate the taint.

    ```bash
    kubectl label node <node> digitalcurling.io/server=true
    kubectl taint node <node> digitalcurling.io/server=true:NoSchedule
    ```

1. Create the data directory on that node. Kubernetes sets its group when the
   pod starts:

    ```bash
    mkdir -p /var/lib/digitalcurling/postgres
    ```

1. Keep `capacity.storage` in `storage.yaml` and `storage.size` in `postgres.yaml` equal, and
   within the node's disk. `postgres.yaml` also sets the memory limits.

## Deploy

1. Create the namespace and the Secret. `users` is a JSON object of username to
   password, the logins that clients use:

    ```bash
    kubectl apply -f k8s/namespace.yaml
    kubectl -n digitalcurling create secret generic dc-server \
      --from-literal=pepper="$(openssl rand -hex 32)" \
      --from-literal=users='{"user0":"CHANGE_ME","user1":"CHANGE_ME"}'
    ```

1. Build the image and load it into the node. No registry is involved: the
   image is imported into the node's containerd, so only that node has it. `IMAGE_IMPORT_CMD` reads a `docker save` tarball
   from stdin on the node:

    ```bash
    IMAGE_IMPORT_CMD='ssh root@<node> ctr -n k8s.io images import -' \
      k8s/image.sh
    ```

    The image is `digitalcurling4-server:<short commit>`, built from the
    committed sources. The script sets that tag in `kustomization.yaml`;
    commit the change.

1. Apply everything:

    ```bash
    kubectl apply -k k8s
    kubectl -n digitalcurling wait cluster/dc-postgres --for=condition=Ready --timeout=5m
    kubectl -n digitalcurling rollout status deploy/dc-server
    ```

    The server's pods wait until CloudNativePG has created the Secret
    `dc-postgres-app`, so `CreateContainerConfigError` is normal for the first
    minute.

1. Point clients in the cluster at
   `http://dc-server.digitalcurling.svc.cluster.local:8080`. The Service has
   IPv4 and IPv6 addresses, and the server listens on both.

   To serve it outside the cluster, put a reverse proxy in front of the
   Service, or add an Ingress. Settings that belong to one cluster (a fixed
   ClusterIP for a proxy on a node, the node's hostname, an image registry)
   go in a kustomize overlay kept with that cluster's configuration, not
   here. See [Local settings](#local-settings).

The `migrate` init container applies `postgres/init/*.sql` and creates the users
in `users` each time a pod starts, so changing a password takes a
`kubectl -n digitalcurling rollout restart deploy/dc-server`.

## Local settings

`k8s/` holds only what every cluster needs. Keep your own cluster's settings
in an overlay outside this repository that uses it as a base, for example:

```yaml
# kustomization.yaml in your own (private) configuration
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - https://github.com/pon-pokapoka/DigitalCurling4-Server//k8s?ref=<commit>
patches:
  # A fixed ClusterIP, for a reverse proxy on a node. Pick it from the
  # static band (the first 256 addresses) of your service range.
  - target: { kind: Service, name: dc-server }
    patch: |
      - op: add
        path: /spec/clusterIP
        value: <address>
```

Apply it with `kubectl apply -k <overlay directory>`. A ClusterIP can't change
in place: to add one to an existing Service, delete the Service first.

## Scaling

Raise `replicas` in `server.yaml`. Each process runs one simulation at a time,
so replicas add throughput and threads don't. Keep
`replicas × (DB_POOL_SIZE + DB_MAX_OVERFLOW)` below `max_connections` in
`postgres.yaml`.

Clients that reuse one connection stay on one replica. It works, because Redis
connects the replicas, but the load is only spread if clients open a new
connection for each match.

Set `time_limit` high for self-play. The clock runs on wall time, so a shot
waiting behind others counts against its team.

## Operations

- **Backups:** none are configured. A single local volume is the only copy of
  the data unless you add one. CloudNativePG can archive to object storage;
  backing up the node's disk also works, as a crash-consistent copy.
- **Restarts:** Postgres takes about half a minute to come back. The server's
  pods go unready and return by themselves, and requests in between fail with
  500, so clients should retry.
- **Removing it:** deleting the `Cluster` leaves the data on the node and the
  PersistentVolume `Released`, because its reclaim policy is `Retain`. A new
  `Cluster` won't bind to it until you clear the PV's `claimRef` and empty the
  directory.
- **Images:** each deploy runs the commit tagged in `kustomization.yaml`, so a
  restart can't change the version. To update, run `k8s/image.sh` on the new
  commit and apply. The image is only on the node it was imported into: if the
  node is rebuilt, import it again. A tag missing from the node makes new pods
  fail with `ErrImagePull`, and the old ones keep running.
