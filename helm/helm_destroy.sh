#!/bin/bash
export $(grep -v '^#' .env | xargs -d '\n')
export $(grep -v '^#' ../src/.env | xargs -d '\n')
sops -i -d --input-type dotenv --output-type dotenv ../src/.env.secrets
export $(grep -v '^#' ../src/.env.secrets | xargs -d '\n')
sops -i -e --input-type dotenv --output-type dotenv ../src/.env.secrets

helmfile destroy --kubeconfig /etc/rancher/k3s/k3s.yaml

