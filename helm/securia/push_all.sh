#!/bin/bash
export $(grep -v '^#' .env | xargs -d '\n')
export $(grep -v '^#' ../src/.env | xargs -d '\n')
eval "$(sops -d --input-type dotenv --output-type dotenv ../src/.env.secrets | grep -v '^#' | sed 's/^/export /')"

echo "${REGISTRY_PASSWORD}" | helm registry login -u ${REGISTRY_USERNAME} --password-stdin ${REGISTRY_HOST}
helm package charts/collector_hikvision --version ${CHART_VERSION}
helm package charts/collector_simulator --version ${CHART_VERSION}
helm package charts/image_preprocessor --version ${CHART_VERSION}
helm package charts/securia_api --version ${CHART_VERSION}
helm package charts/securia_maintenance --version ${CHART_VERSION}
helm package charts/securia_ui --version ${CHART_VERSION}
helm package charts/yolo_processor --version ${CHART_VERSION}

helm push collector-hikvision-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia/charts
helm push collector-simulator-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia/charts
helm push image-preprocessor-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia/charts
helm push securia-api-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia/charts
helm push securia-maintenance-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia/charts
helm push securia-ui-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia/charts
helm push yolo-processor-${CHART_VERSION}.tgz oci://harbor.marnus.com:443/securia/charts

rm *tgz