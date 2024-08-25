# Local Docker registry

Running containers requires a registry, this installs one in the cluster on my laptop.

https://github.com/twuni/docker-registry.helm

```bash
helm repo add twuni https://helm.twun.io
helm repo update
```

```bash
helm --kubeconfig /etc/rancher/k3s/k3s.yaml install twuni/docker-registry -n docker-registry --create-namespace
```

## Docker - Using an insecure registry (on local)

https://www.oreilly.com/library/view/kubernetes-in-the/9781492043270/app03.html

`sudo vi /etc/docker/daemon.json`

add insecure registry

```json
{
  "insecure-registries" : [
    "your_ip_here:32419"
   ]
 }
```

`sudo systemctl restart docker`

### Testing

```bash
docker pull nginx
docker tag nginx your_ip_here:32419/nginx
docker push your_ip_here:32419/nginx
```

## K3s - Add insecure registry

https://docs.k3s.io/installation/private-registry

`sudo vi /etc/rancher/k3s/registries.yaml`

```yaml
mirrors:
  "10.0.0.59:32419":
    endpoint:
      - "http://10.0.0.59:32419"
```

`sudo systemctl restart k3s`

### Testing

can be done once you have some containers build