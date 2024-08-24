# YOLO Preprocessor

## Deployment

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade yolo-processor . -i -f values.yaml --create-namespace
```
