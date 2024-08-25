# Strimzi

## Cluster

https://strimzi.io/docs/operators/latest/deploying#deploying-cluster-operator-helm-chart-str

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n kafka --create-namespace install strimzi-cluster-operator oci://quay.io/strimzi-helm/strimzi-kafka-operator
```

https://github.com/strimzi/strimzi-kafka-operator/tree/0.42.0/examples

```bash
kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml apply -f dev_strimzi_cluster.yaml
```

## Kafka UI

```bash
helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
helm repo update
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n kafka install kafka-ui kafka-ui/kafka-ui --values kafka-ui-values.yaml
```

## Testing/Sample Python

requires some kafka pips, i already have it elsewhere, simple enough

```bash
./test_connection.py
```
