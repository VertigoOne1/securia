# S3 Emulator

Uses S3Ninja

https://github.com/scireum/s3ninja

## Deployment

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n s3emu upgrade s3emu . -i -f values.yaml --create-namespace
```
