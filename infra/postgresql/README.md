# Containerised PostgreSQL

https://docs.percona.com/percona-operator-for-postgresql/2.0/helm.html#prerequisites

https://github.com/percona/percona-helm-charts/blob/main/charts/pg-operator/README.md

```bash
helm repo add percona https://percona.github.io/percona-helm-charts/
helm repo update
helm --kubeconfig /etc/rancher/k3s/k3s.yaml install pg-operator percona/pg-operator --namespace postgresql --create-namespace
```

## Highly available cluster

3 node cluster is the default

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml install cluster1 percona/pg-db -n postgresql
```

## Local Env

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml upgrade my-pg percona/pg-db \
  --set instances[0].name=test \
  --set instances[0].replicas=1 \
  --set instances[0].dataVolumeClaimSpec.resources.requests.storage=16Gi \
  --set proxy.pgBouncer.replicas=1 \
  --set proxy.pgBouncer.expose.type=NodePort \
  --set finalizers={'percona\.com\/delete-pvc,percona\.com\/delete-ssl'} \
  --set users[0].name=test \
  --set users[0].databases={mytest} \
  --set users[1].name=preproc \
  --set users[1].databases={securia} \
  --set users[2].name=securiaadmin \
  --set users[2].databases={securia} \
  --set users[3].name=securiaapi \
  --set users[3].databases={securia} \
  --install \
  --namespace postgresql
```

## Connection

### From outside

```bash
PGBOUNCER_URI=$(kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml -n postgresql get secrets my-pg-pg-db-pguser-test -o jsonpath="{.data.pgbouncer-uri}" | base64 --decode)
kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml -n postgresql run -i --rm --tty percona-client --image=perconalab/percona-distribution-postgresql:16 --restart=Never -- psql $PGBOUNCER_URI
```

### Dev cluster

PGBOUNCER_URI=$(kubectl --kubeconfig /home/marnus/iot/kubeconfigs/legion -n postgresql get secrets dev-pg-pg-db-pguser-dev -o jsonpath="{.data.pgbouncer-uri}" | base64 --decode)
kubectl --kubeconfig /home/marnus/iot/kubeconfigs/legion -n postgresql run -i --rm --tty percona-client --image=perconalab/percona-distribution-postgresql:16 --restart=Never -- psql $PGBOUNCER_URI

## Dev deployment

### Operator

helm --kubeconfig /home/marnus/iot/kubeconfigs/legion install pg-operator percona/pg-operator --namespace postgresql --create-namespace

### Dev Env

helm --kubeconfig /home/marnus/iot/kubeconfigs/legion upgrade dev-pg percona/pg-db \
  --set instances[0].name=dev \
  --set instances[0].replicas=1 \
  --set instances[0].dataVolumeClaimSpec.resources.requests.storage=16Gi \
  --set instances[0].dataVolumeClaimSpec.storageClassName=nfs-client-ssd \
  --set proxy.pgBouncer.replicas=1 \
  --set proxy.pgBouncer.expose.type=NodePort \
  --set finalizers={'percona\.com\/delete-pvc,percona\.com\/delete-ssl'} \
  --set users[0].name=dev \
  --set users[0].databases={mydev} \
  --set users[1].name=preproc \
  --set users[1].databases={securia} \
  --set users[2].name=securiaadmin \
  --set users[2].databases={securia} \
  --set users[3].name=securiaapi \
  --set users[3].databases={securia} \
  --set users[3].name=keycloak \
  --set users[3].databases={keycloak} \
  --install \
  --namespace postgresql
