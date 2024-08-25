### Keycloak

<https://github.com/bitnami/charts/tree/main/bitnami/keycloak/>

```bash
helm ${HELM_EXTRA_ARGS} upgrade --install --create-namespace -n keycloak keycloak oci://registry-1.docker.io/bitnamicharts/keycloak -f helm/values/keycloak.yaml --set auth.adminPassword=xxx
```