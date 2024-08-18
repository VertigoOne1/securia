## Deploy

### Hikvision Collector

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade collector-hikvision helm/charts/collector_hikvision -i -f helm/charts/collector_hikvision/values.yaml --create-namespace
```

### Preprocessor

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade image-preprocessor helm/charts/image_preprocessor -i -f helm/charts/image_preprocessor/values.yaml --create-namespace
```

### API

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade securia-api helm/charts/securia_api -i -f helm/charts/securia_api/values.yaml --create-namespace
```
