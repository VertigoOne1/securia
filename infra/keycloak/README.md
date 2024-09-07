# Keycloak

<https://github.com/bitnami/charts/tree/main/bitnami/keycloak/>

```bash
helm --kubeconfig /home/marnus/iot/kubeconfigs/legion upgrade --install --create-namespace -n keycloak keycloak oci://registry-1.docker.io/bitnamicharts/keycloak -f values.yaml -f secrets://values_secrets.yaml
```

## Note

need to run `GRANT ALL ON SCHEMA public TO keycloak;` on psql db if external postgresql is used