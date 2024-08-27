# Grafana

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm upgrade grafana grafana/grafana -i -n monitoring --kubeconfig /home/marnus/iot/kubeconfigs/legion -f values.yaml -f secrets://values_secrets.yaml
```