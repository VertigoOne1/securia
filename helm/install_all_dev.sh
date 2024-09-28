#!/bin/bash
export $(grep -v '^#' .env | xargs -d '\n')
export $(grep -v '^#' ../src/.env | xargs -d '\n')
sops -i -d --input-type dotenv --output-type dotenv ../src/.env.secrets
export $(grep -v '^#' ../src/.env.secrets | xargs -d '\n')
sops -i -e --input-type dotenv --output-type dotenv ../src/.env.secrets
helmfile apply --kubeconfig /etc/rancher/k3s/k3s.yaml
# helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade collector-hikvision charts/collector_hikvision -i -f ${VALUES_PATH}/collector_hikvision/values.yaml -f secrets://${VALUES_PATH}/collector_hikvision/values_secrets.yaml --create-namespace
# helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade image-preprocessor charts/image_preprocessor -i -f ${VALUES_PATH}/image_preprocessor/values.yaml -f secrets://${VALUES_PATH}/image_preprocessor/values_secrets.yaml --create-namespace
# helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade securia-api charts/securia_api -i -f ${VALUES_PATH}/securia_api/values.yaml -f secrets://${VALUES_PATH}/securia_api/values_secrets.yaml --create-namespace
# helm --kubeconfig /etc/rancher/k3s/k3s.yaml -n securia upgrade securia-ui charts/securia_ui -i -f ${VALUES_PATH}/securia_ui/values.yaml -f secrets://${VALUES_PATH}/securia_ui/values_secrets.yaml --create-namespace
# #helm --kubeconfig /home/marnus/iot/kubeconfigs/legion -n securia upgrade yolo-processor charts/yolo_processor -i -f ${VALUES_PATH}/yolo_processor/values.yaml -f secrets://${VALUES_PATH}/yolo_processor/values_secrets.yaml --create-namespace