#!/bin/bash
VALUES_PATH=values/local
export SOPS_AGE_KEY_FILE=${HOME}/iot/securia/securia.key
helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade collector-hikvision charts/collector_hikvision -i -f ${VALUES_PATH}/collector_hikvision/values.yaml -f secrets://${VALUES_PATH}/collector_hikvision/values_secrets.yaml --create-namespace
# helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade image-preprocessor charts/image_preprocessor -i -f ${VALUES_PATH}/image_preprocessor/values.yaml -f secrets://${VALUES_PATH}/image_preprocessor/values_secrets.yaml --create-namespace
# helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade securia-api charts/securia_api -i -f ${VALUES_PATH}/securia_api/values.yaml -f secrets://${VALUES_PATH}/securia_api/values_secrets.yaml --create-namespace
# helm --kubeconfig /home/marnus/iot/kubeconfigs/legion -n securia upgrade yolo-processor charts/yolo_processor -i -f ${VALUES_PATH}/yolo_processor/values.yaml -f secrets://${VALUES_PATH}/yolo_processor/values_secrets.yaml --create-namespace