#!/bin/bash
REGISTRY_HOST=harbor.marnus.com:443
docker build collector_hikvision/ -t ${REGISTRY_HOST}/securia/collector-hikvision:latest
docker push ${REGISTRY_HOST}/securia/collector-hikvision:latest
docker build collector_simulator/ -t ${REGISTRY_HOST}/securia/collector-simulator:latest
docker push ${REGISTRY_HOST}/securia/collector-simulator:latest
docker build image_preprocessor/ -t ${REGISTRY_HOST}/securia/image-preprocessor:latest
docker push ${REGISTRY_HOST}/securia/image-preprocessor:latest
docker build securia_api/ -t ${REGISTRY_HOST}/securia/securia-api:latest
docker push ${REGISTRY_HOST}/securia/securia-api:latest
docker build securia_ui/ -t ${REGISTRY_HOST}/securia/securia-ui:latest
docker push ${REGISTRY_HOST}/securia/securia-ui:latest
docker build yolo_processor/ -t ${REGISTRY_HOST}/securia/yolo-processor:latest
docker push ${REGISTRY_HOST}/securia/yolo-processor:latest