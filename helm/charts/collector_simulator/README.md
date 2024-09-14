# Simulator Collector

## Deployment

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade simulator-collector . -i -f values.yaml --create-namespace
```
