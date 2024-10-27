# GPU Metrics

```bash
helm repo add utkuozdemir https://utkuozdemir.org/helm-charts
helm --kubeconfig /home/marnus/iot/kubeconfigs/legion upgrade --install -n gpu-metrics gpu-metrics utkuozdemir/nvidia-gpu-exporter
```

set to only the machine with the gpu, yes it can be smarter, just playing around.

```yaml
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchFields:
              - key: metadata.name
                operator: In
                values:
                - marnus-legion
```