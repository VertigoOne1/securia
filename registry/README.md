# Local Docker registry

Running containers requires a registry, this installs one in the cluster.

https://github.com/twuni/docker-registry.helm

```bash
helm repo add twuni https://helm.twun.io
helm repo update
```

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml install twuni/docker-registry -n docker-registry --create-namespace
```

## Using an insecure registry (on local)

https://www.oreilly.com/library/view/kubernetes-in-the/9781492043270/app03.html

`sudo vi /etc/docker/daemon.json`

add insecure registry

```json
{
  "insecure-registries" : [
    "your_ip_here:5000"
   ]
 }
```

restart docker

### Testing

```bash
docker pull nginx
docker tag nginx your_ip_here:5000/nginx
docker push your_ip_here:5000/nginx
```

## Add insecure registry (k3s)

https://docs.k3s.io/installation/private-registry

`sudo vi /etc/rancher/k3s/registries.yaml`

```yaml
mirrors:
  "10.0.0.59:5000":
    endpoint:
      - "http://10.0.0.59:5000"
```

`sudo systemctl restart k3s`

### Testing

```bash
docker pull nginx
docker tag nginx your_ip_here:5000/nginx
docker push your_ip_here:5000/nginx