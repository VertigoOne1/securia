# Securia UI

## Deployment

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade securia-ui . -i -f values.yaml --create-namespace
```
