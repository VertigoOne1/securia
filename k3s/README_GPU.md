# Enable K3s GPU support

<https://itnext.io/enabling-nvidia-gpus-on-k3s-for-cuda-workloads-a11b96f967b0>

## enable k3s GPU support

https://docs.k3s.io/advanced?_highlight=gpu#nvidia-container-runtime-support

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
&& curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
&& curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
```

```bash
sudo apt install -y nvidia-container-runtime cuda-drivers-fabricmanager-550 nvidia-headless-550-server python3-pip iputils-ping net-tools htop vim
```

```bash
pip3 install gpustat
```

```bash
sync ; reboot
```

then install k3s

add k3s server to hosts file 10.0.0.4 k3s >> hosts

```bash
K3S_TOKEN="K10ced8aa577fbc42665d593b086f65282e079a859f71297996ce44c6d28246a95d::8metsv.fz8zg2j4bye9ofad"
curl -sfL https://get.k3s.io | K3S_URL=https://k3s:6443 K3S_TOKEN=${K3S_TOKEN} sh -
```

and then add the runtime

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: nvidia
handler: nvidia
```

Check if runtime is enabled

```bash
grep nvidia /var/lib/rancher/k3s/agent/etc/containerd/config.toml
```

and then enable detection of GPU features

<https://github.com/NVIDIA/k8s-device-plugin#quick-start>

```kubectl apply -k https://github.com/kubernetes-sigs/node-feature-discovery/deployment/overlays/default?ref=v0.15.0```

```kubectl apply -f https://raw.githubusercontent.com/NVIDIA/gpu-feature-discovery/v0.8.2/deployments/static/gpu-feature-discovery-daemonset.yaml```

Need to update it to run with the correct container runtime - add the following to the daemonset -   runtimeClassName: nvidia

### Monitor GPU

```bash
gpustat -F -i 1
```

### Test images

```text
nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda10.2
docker.io/nvidia/cuda:12.3.1-devel-ubuntu22.04
docker.io/nvidia/cuda:12.3.1-base-ubuntu22.04
docker.io/cemizm/tf-benchmark-gpu --model resnet50 --num_gpus=1
```

Test without kubernetes (this tests the engine)

```bash
# Works
sudo ctr image pull nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda10.2
sudo ctr run --rm --gpus 0 -t nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda10.2 cuda-10

sudo ctr image pull docker.io/cemizm/tf-benchmark-gpu:latest
sudo ctr run --rm --gpus 0 -t docker.io/cemizm/tf-benchmark-gpu:latest tf-bench bash
in container -> ./benchmark.sh --model resnet50
```

if they output anything, your GPU support in docker is good without even having to go to k8s/k3s

### Test on Kubernetes

```yaml
---
apiVersion: v1
kind: Pod
metadata:
  name: nbody-gpu-benchmark
  namespace: default
spec:
  restartPolicy: OnFailure
  runtimeClassName: nvidia  # THIS IS IMPORTANT
  selector:
    matchLabels:
      nvidia.com/gpu.count: 1
  containers:
  - name: cuda-container
    image: nvcr.io/nvidia/k8s/cuda-sample:nbody
    args: ["nbody", "-gpu", "-numbodies=100000", "-benchmark"]
    # resources:
    #   limits:
    #     nvidia.com/gpu.count: 1
    env:
    - name: NVIDIA_VISIBLE_DEVICES
      value: all
    - name: NVIDIA_DRIVER_CAPABILITIES
      value: all
```
