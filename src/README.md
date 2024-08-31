# Securia Source

## Build and push

### Hikvision Collector

```bash
docker build collector_hikvision/ -t ${REGISTRY_HOST}/securia/collector-hikvision:latest
docker push ${REGISTRY_HOST}/securia/collector-hikvision:latest
```

### Preprocessor

```bash
docker build image_preprocessor/ -t ${REGISTRY_HOST}/securia/image-preprocessor:latest
docker push ${REGISTRY_HOST}/securia/image-preprocessor:latest
```

### API

```bash
docker build securia_api/ -t ${REGISTRY_HOST}/securia/securia-api:latest
docker push ${REGISTRY_HOST}/securia/securia-api:latest
```

### YOLO Processor

```bash
docker build yolo_processor/ -t ${REGISTRY_HOST}/securia/yolo-processor:latest
docker push ${REGISTRY_HOST}/securia/yolo-processor:latest
```

## One Shot

```bash
docker build collector_hikvision/ -t ${REGISTRY_HOST}/securia/collector-hikvision:latest
docker push ${REGISTRY_HOST}/securia/collector-hikvision:latest
docker build image_preprocessor/ -t ${REGISTRY_HOST}/securia/image-preprocessor:latest
docker push ${REGISTRY_HOST}/securia/image-preprocessor:latest
docker build securia_api/ -t ${REGISTRY_HOST}/securia/securia-api:latest
docker push ${REGISTRY_HOST}/securia/securia-api:latest
```
