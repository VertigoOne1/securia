# Setup local dev k3s cluster

## K3s

https://github.com/k3s-io/k3s

Kubeconfig

--kubeconfig /etc/rancher/k3s/k3s.yaml

```bash
kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml get nodes
```

## Add node

curl -sfL https://get.k3s.io | K3S_URL=https://k3s:6443 K3S_TOKEN=!vault |
                                                                  $ANSIBLE_VAULT;1.1;AES256
                                                                  30323762333934393332366339356462313761383339363938396239343963643861363230613363
                                                                  6131663863336464393633303539353036643639656233320a646561326237653135356530653364
                                                                  34353162626638613435333766663137613633353931626432373535333162343134313835393136
                                                                  3736333937323033350a333334343964616265396135343835303935313733343166393965313863
                                                                  61653331353032313531646234646230323664626662613137336163313364633034326631633466
                                                                  36366536633133646435306336333766336430366261393164356534336530326163396439616465
                                                                  62656166643963346236303536626531343361323438303939643835306566353038396433353536
                                                                  33393737323030376530613862383664396531613463663863383039643934363366323962646637
                                                                  33383637346133373364386562643062643932393134643837653362333136316661366239623762
                                                                  6639323233333030613834323062653936383633366538626131

## KDashboard

```bash
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
helm repo update
helm --kubeconfig /etc/rancher/k3s/k3s.yaml upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard --values kdashboard.yaml
```

### Changes

- set the service to nodeport, so it sticks to a port

https://localhost:32281

### TODO

- zoink everything via traefik ingress to 443.. so you get a nice clean working cert

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

## redirect to https

Annotation:

traefik.ingress.kubernetes.io/router.entrypoints: web, websecure
traefik.ingress.kubernetes.io/router.middlewares: default-redirectscheme@kubernetescrd

Middleware:

apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: redirect-http-to-https
spec:
  redirectScheme:
    scheme: https
    permanent: true

