# Securia Source

## Build and push

Options are

### Buildx bake

#### Setup containerised building

```bash
docker buildx create --name=container --driver=docker-container --use --bootstrap
```

#### Usage

```bash
docker buildx bake --push --builder=container
```

### Compose

```bash
docker-compose build
docker-compose push
```

### Shortcut

```bash
./build_all.sh
```

### Individual

### Hikvision Collector

```bash
docker buildx build collector_hikvision/ -t ${REGISTRY_HOST}/securia/collector-hikvision:latest
docker push ${REGISTRY_HOST}/securia/collector-hikvision:latest
```

### Preprocessor

```bash
docker buildx build image_preprocessor/ -t ${REGISTRY_HOST}/securia/image-preprocessor:latest
docker push ${REGISTRY_HOST}/securia/image-preprocessor:latest
```

### API

```bash
docker buildx build securia_api/ -t ${REGISTRY_HOST}/securia/securia-api:latest
docker push ${REGISTRY_HOST}/securia/securia-api:latest
```

### YOLO Processor

```bash
docker buildx build yolo_processor/ -t ${REGISTRY_HOST}/securia/yolo-processor:latest
docker push ${REGISTRY_HOST}/securia/yolo-processor:latest
```
