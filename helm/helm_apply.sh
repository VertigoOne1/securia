#!/bin/bash

export KUBECONFIG=/home/marnus/iot/kubeconfigs/legion
export SOPS_AGE_KEY_FILE=${HOME}/iot/securia/securia.key
helmfile apply

