# Deploy

## Hikvision Collector

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade collector-hikvision charts/collector_hikvision -i -f charts/collector_hikvision/values.yaml --create-namespace
```

## Preprocessor

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade image-preprocessor charts/image_preprocessor -i -f charts/image_preprocessor/values.yaml --create-namespace
```

## API

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade securia-api charts/securia_api -i -f charts/securia_api/values.yaml --create-namespace
```
