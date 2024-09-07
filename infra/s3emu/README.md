# Object storage emulation

We need a way to test S3 without spending, the idea is to store images in s3 for long term.

exposes as nodeport

http://localhost:32650/ui

by default there is no TLS encryption, it is local-dev. Setting up to my cluster will run via ingress

## Deployment on Local

`helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n s3emu upgrade s3emu helm/s3emu -i -f values.yaml --create-namespace`

## Deployment on Dev

`helm upgrade s3emu . -i -n s3emu --kubeconfig /home/marnus/iot/kubeconfigs/legion -f values.yaml -f secrets://values_secrets.yaml --create-namespace`


## Testing

can use `test.py` to confirm it is working using boto3, it is configured with a compatable Config