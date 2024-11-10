# ArgoCD Project for Infrastructure

This bootstraps the infrastructure project.

## TODO

1. create oci

## Process

1. Deploy argocd
2. deploy this

helm upgrade infrastructure . -n argocd -f values.yaml -f secrets://values_secrets.yaml --install --kubeconfig ~/iot/kubeconfigs/legion