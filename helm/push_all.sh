#!/bin/bash
export $(grep -v '^#' .env | xargs -d '\n')
export $(grep -v '^#' ../src/.env | xargs -d '\n')
sops -i -d --input-type dotenv --output-type dotenv ../src/.env.secrets
export $(grep -v '^#' ../src/.env.secrets | xargs -d '\n')
sops -i -e --input-type dotenv --output-type dotenv ../src/.env.secrets

helm registry login -u ${REGISTRY_USERNAME} -p ${REGISTRY_PASSWORD} harbor.marnus.com:443
helm package charts/collector_hikvision --version ${CHART_VERSION}
helm package charts/image_preprocessor --version ${CHART_VERSION}
helm package charts/securia_api --version ${CHART_VERSION}
helm package charts/securia_ui --version ${CHART_VERSION}
helm package charts/yolo_processor --version ${CHART_VERSION}

helm push collector-hikvision-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia
helm push image-preprocessor-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia
helm push securia-api-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia
helm push securia-ui-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia
helm push yolo-processor-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia

rm *tgz