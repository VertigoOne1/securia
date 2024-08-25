# Securia Source

## Build and push

### Hikvision Collector

```bash
docker build collector_hikvision/ -t 10.0.0.59:32419/securia/collector-hikvision:latest
docker push 10.0.0.59:32419/securia/collector-hikvision:latest
```

### Preprocessor

```bash
docker build image_preprocessor/ -t 10.0.0.59:32419/securia/image-preprocessor:latest
docker push 10.0.0.59:32419/securia/image-preprocessor:latest
```

### API

```bash
docker build securia_api/ -t 10.0.0.59:32419/securia/securia-api:latest
docker push 10.0.0.59:32419/securia/securia-api:latest
```

## One Shot

```bash
docker build collector_hikvision/ -t 10.0.0.59:32419/securia/collector-hikvision:latest
docker push 10.0.0.59:32419/securia/collector-hikvision:latest
docker build image_preprocessor/ -t 10.0.0.59:32419/securia/image-preprocessor:latest
docker push 10.0.0.59:32419/securia/image-preprocessor:latest
docker build securia_api/ -t 10.0.0.59:32419/securia/securia-api:latest
docker push 10.0.0.59:32419/securia/securia-api:latest
```
