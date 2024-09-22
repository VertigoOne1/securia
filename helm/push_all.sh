#!/bin/bash
VERSION=1.1.0

helm registry login -u ${LOCAL_REGISTRY_USER} -p ${LOCAL_REGISTRY_PASS} harbor.marnus.com:443
helm package charts/collector_hikvision --version ${VERSION}
helm package charts/image_preprocessor --version ${VERSION}
helm package charts/securia_api --version ${VERSION}
helm package charts/securia_ui --version ${VERSION}
helm package charts/yolo_processor --version ${VERSION}

helm push collector-hikvision-${VERSION}.tgz oci://harbor.marnus.com:443/securia
helm push image-preprocessor-${VERSION}.tgz oci://harbor.marnus.com:443/securia
helm push securia-api-${VERSION}.tgz oci://harbor.marnus.com:443/securia
helm push securia-ui-${VERSION}.tgz oci://harbor.marnus.com:443/securia
helm push yolo-processor-${VERSION}.tgz oci://harbor.marnus.com:443/securia

rm *tgz