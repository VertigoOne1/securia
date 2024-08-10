# Setup local dev k3s cluster

## K3s

https://github.com/k3s-io/k3s

Kubeconfig

--kubeconfig /etc/rancher/k3s/k3s.yaml

```bash
kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml get nodes
```

## KDashboard

```bash
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
helm repo update
helm --kubeconfig /etc/rancher/k3s/k3s.yaml upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard --values kdashboard.yaml
```

### Full Permissions

```bash
kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml -n kubernetes-dashboard apply kdashsuperuser.yaml
kubectl get secret admin-user -n kubernetes-dashboard -o jsonpath={".data.token"} | base64 -d
# copy pasta the token
kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8443:443
# browser -> 8443, paste the token - done
```

### Encountered error

`unable to retrieve the complete list of server APIs: metrics.k8s.io/v1beta1: stale GroupVersion discovery: metrics.k8s.io/v1beta1`

```bash
lk describe apiservice/v1beta1.metrics.k8s.io0
# Review any errors
```

was on wrong port number (443 should be 4443)

sorted out, running

## Access

```bash
kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8443:443
```

https://localhost:8443

