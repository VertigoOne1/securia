# Strimzi

## Cluster

https://strimzi.io/docs/operators/latest/deploying#deploying-cluster-operator-helm-chart-str

```bash
helm install strimzi-cluster-operator oci://quay.io/strimzi-helm/strimzi-kafka-operator --kubeconfig /home/marnus/iot/kubeconfigs/legion -n kafka --create-namespace
```

https://github.com/strimzi/strimzi-kafka-operator/tree/0.42.0/examples

```bash
kubectl --kubeconfig --kubeconfig /home/marnus/iot/kubeconfigs/legion apply -f dev/strimzi_cluster.yaml
```

## Kafka UI

```bash
helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
helm repo update
helm --kubeconfig --kubeconfig /home/marnus/iot/kubeconfigs/legion -n kafka upgrade -i kafka-ui kafka-ui/kafka-ui --values dev/kafka-ui-values.yaml --values secrets://dev/kafka-ui-values_secrets.yaml
```

## Testing/Sample Python

requires some kafka pips, i already have it elsewhere, simple enough

```bash
./test_connection.py
```
