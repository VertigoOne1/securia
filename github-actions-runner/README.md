# Github Actions Runner

To be able to use CI/CD via github Actions to your laptop, you need action runners able to execute on the local cluster

https://github.com/actions/actions-runner-controller/blob/master/docs/installing-arc.md

This also requires cert-manager

## Cert Manager (if not there yet)

```bash
helm repo add jetstack https://charts.jetstack.io --force-update
helm repo update
```

```bash
helm install \
  cert-manager jetstack/cert-manager \
  --kubeconfig /etc/rancher/k3s/k3s.yaml \
  --namespace cert-manager \
  --create-namespace \
  --version v1.15.2 \
  --set crds.enabled=true
```

## Install ARC Controller

```bash
helm repo add actions-runner-controller https://actions-runner-controller.github.io/actions-runner-controller
helm repo update
```

Generate a github PAT with full-control on repo (you need to specify it below)

Create a clusterrolebinding with cluster-admin so the action running can run helm and kubectl against the private cluster

`kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml apply -f arc_superuser_binding.yaml`

```bash
helm upgrade \
  actions-runner-controller \
  actions-runner-controller/actions-runner-controller \
  --kubeconfig /etc/rancher/k3s/k3s.yaml \
  --install \
  --namespace actions-runner-system \
  --create-namespace \
  --set serviceAccount.name=arc-user \
  --set githubWebhookServer.serviceAccount.name=arc-user \
  --set authSecret.create=True \
  --set authSecret.github_token=${GITHUB_PRIVATE_PAT} \
  --wait
```

`kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml apply -f arc_superuser_binding.yaml`

## Deploy a runner for Github Repo

Import to the cluster

```yaml
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: securia-arc-runner
spec:
  replicas: 1
  template:
    spec:
      repository: VertigoOne1/securia
      automountServiceAccountToken: true
      volumeMounts:
       - mountPath: /runner
         name: runner
      volumes:
       - emptyDir: {}
         name: runner
      labels:
        - "local-laptop"
```

## Use it on github actions

add below on every pipeline

```yaml
runs-on: self-hosted  # or local-laptop
```

## Extra

Can use HPA

https://opstree.com/blog/2023/04/18/github-self-hosted-runner-on-kubernetes/

## Test permissions to kubeconfig

Create pipeline with

```yaml
name: Test K8s Access

on: workflow_dispatch

jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - name: print vars
        run: env
      - name: Checkout repo
        uses: actions/checkout@v1
      - uses: azure/setup-kubectl@v1
      - run: kubectl get pods -A
```
