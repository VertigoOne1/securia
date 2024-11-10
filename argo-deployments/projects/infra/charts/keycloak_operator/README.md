# ArgoCD - Keycloak Operator for Infrastructure

This bootstraps installs the CRDs and operator for Keycloak deployment

## TODO

1. create oci
2. create helm for keycloak operator deployment (it is static ymls at the moment)

## Process

1. Deploy argocd
2. deploy infrastructure project helm
2. deploy this

helm upgrade keycloak-operator . -n argocd -f values.yaml -f secrets://values_secrets.yaml --install --kubeconfig ~/iot/kubeconfigs/legion