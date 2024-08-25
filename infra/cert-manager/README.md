# Cert Manager

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm upgrade ${HELM_EXTRA_ARGS} -i \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

then apply the two manifests