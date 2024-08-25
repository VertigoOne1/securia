# Harbor

you know, for images

<https://goharbor.io/>

```bash
helm repo add harbor https://helm.goharbor.io
helm repo update
helm --kubeconfig /home/marnus/iot/kubeconfigs/legion upgrade --install --create-namespace -n harbor harbor harbor/harbor -f harbor_values.yaml -f secrets://harbor_secrets.yaml --dry-run
```

