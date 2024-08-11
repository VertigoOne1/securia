# Securia Source

## Build and push

### Hikvision Collector

```bash
docker build collector_hikvision/ -t 10.0.0.59:5000/securia/collector-hikvision:latest
docker push 10.0.0.59:5000/securia/collector-hikvision:latest
```

## Deploy

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade collector-hikvision helm/charts/collector_hikvision -i -f helm/charts/collector_hikvision/values.yaml --create-namespace
```
