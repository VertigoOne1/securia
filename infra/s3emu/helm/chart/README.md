# S3 Emulator

Uses S3Ninja

https://github.com/scireum/s3ninja

## Deployment

### Local

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n s3emu upgrade s3emu . -i -f values/local/values.yaml --create-namespace
```

### Dev

```bash
helm --kubeconfig legion -n s3emu upgrade s3emu . -i -f values/dev/values.yaml -f secrets://values/dev/values_secrets.yaml --create-namespace
```
