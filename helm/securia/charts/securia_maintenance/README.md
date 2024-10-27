# Securia Maintenance

## Deployment

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade securia-maintenance . -i -f values.yaml --create-namespace
```
