# Securia Source

## Build and push

### Hikvision Collector

```bash
docker build collector_hikvision/ -t 10.0.0.59:5000/securia/collector-hikvision:latest
docker push 10.0.0.59:5000/securia/collector-hikvision:latest
```

### Preprocessor

```bash
docker build image_preprocessor/ -t 10.0.0.59:5000/securia/image-preprocessor:latest
docker push 10.0.0.59:5000/securia/image-preprocessor:latest
```

## Deploy

### Hikvision Collector

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade collector-hikvision helm/charts/collector_hikvision -i -f helm/charts/collector_hikvision/values.yaml --create-namespace
```

### Preprocessor

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade image-preprocessor helm/charts/image_preprocessor -i -f helm/charts/image_preprocessor/values.yaml --create-namespace
```
