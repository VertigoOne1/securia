# Image Preprocessor

## Deployment

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade securia-api . -i -f values.yaml --create-namespace
```
