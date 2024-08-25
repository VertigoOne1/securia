# Grafana

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm upgrade -i grafana grafana/grafana --set adminPassword=xxx --kube-context v5-qa -n monitoring
```