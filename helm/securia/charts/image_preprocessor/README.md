# Image Preprocessor

## Deployment

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade image-preprocessor . -i -f values.yaml --create-namespace
```
