# Registry Creds runner

Installs registry pull secret in every namespace

```bash
kubectl apply -f registry_secret_operator.yaml

export DOCKER_USERNAME=username
export DOCKER_PASSWORD=mypassword
export DOCKER_EMAIL=me@example.com

kubectl create secret docker-registry harbor-registry-cred \
  --namespace kube-system \
  --docker-username=$DOCKER_USERNAME \
  --docker-password=$DOCKER_PASSWORD \
  --docker-email=$DOCKER_EMAIL

kubectl apply cluster_pull_secret.yaml
```
