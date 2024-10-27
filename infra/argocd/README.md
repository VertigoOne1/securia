# ArgoCD - Helm based deployment

## Remove manual argocd installation

```bash
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

## Helm based installation

```bash
helm repo add argo 'https://argoproj.github.io/argo-helm'
helm repo update
```

```bash
helm upgrade argocd argo/argo-cd -i -n argocd --create-namespace -f values_legion.yaml --kube-context legion --dry-run
```

## Add SOPS secret to argo (can additionally extend to Azure KeyVault)

kubectl create secret generic -n argocd age-secret --from-file /home/marnus/iot/securia/argocd.key --context legion


## gRPC

ArgoCD metrics - prometheus ->
ArgoCD Rollouts -> adds ability to do phased rollouts

Next step is to enable SOPS and helmfile

then, create application


