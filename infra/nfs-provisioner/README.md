#### NFS provisioner (for shared storage)

Simpler overall, but requires some extra OS steps to be done (setup a nfs server), but allows dynamic volume creation (storage class support, which makes vraptor deployment easier, and you can move things around easily, add external NFS storage)

OS Side

```bash
sudo apt install -y nfs-kernel-server nfs-common
```

```bash
sudo mkdir /k8s-nfs -p
sudo chown nobody:nogroup /k8s-nfs
```

```bash
echo "/k8s-nfs    127.0.0.1(rw,async,no_subtree_check,no_root_squash)" >> /etc/exports
sudo systemctl restart nfs-kernel-server
```

```bash
helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/
helm -n nfs-provisioner install nfs-subdir-external-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
    --set nfs.server=localhost \ # Don't use that!
    --set nfs.path=/k8s-nfs \
    --create-namespace
```

## Dev SSD extra storage class

```bash
helm --kubeconfig /home/marnus/iot/kubeconfigs/legion -n nfs-ssd install nfs-subdir-external-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner -f values/dev/values-ssd.yaml --create-namespace
```

I already had the other nfs provisioner running, so i disabled rbac, and added in the rbac manually as the clusterrole conflicts