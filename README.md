# Security-AI

## Review

https://medium.com/@MrBam44/yolo-object-detection-using-opencv-with-python-b6386c3d6fc1

https://github.com/roboflow/supervision?tab=readme-ov-file

https://github.com/WongKinYiu/yolov7?tab=readme-ov-file

https://github.com/ultralytics/ultralytics

https://github.com/AlexanderMelde/SPHAR-Dataset/releases

https://github.com/openlit/openlit

https://huggingface.co/keras-io/low-light-image-enhancement

UI for YoloV8

https://github.com/Paperspace

## Main points

Event driven exception handling with DLQ for CCTV camera scraping

Review securia/SecurAI.drawio for the big-picture

Local dev is k3s + strimzi + kdashboard + percona pstgresql + s3ninja

## Local Links

- Dashboard - https://localhost:32281
- S3 Ninja  - http://localhost:32650/ui
- PGBouncer - 10.0.0.59:32617
- Kafka     - localhost:32394
- Kafka UI  - http://localhost:31202
- Registry  - 10.0.0.59:5000
- Ingres    - 10.0.0.59:443
- API Docs  - http://10.0.0.95:8088/docs

## Secrets management

age + sops + templatisation

## Local dev setup

Review the readmes in:

- k3s
- strimzi
- postgresql
- registry
- s3emu
- github-actions-runner

## Playing with SOPS + AGE

The idea is to create a simple portable way to allow secret decryption to CICD systems regardless of "provider".

- Github Actions -> Secrets
- Azure DevOps -> Secrets / Keyvaults
- AWS -> Vaults
- etc -> etc

You end up customising for each.

A simple "local-dev" way would be to use SOPS and AGE, and setting up an identity for the provider. You only then check
in the private key to the provider, and keep your own, that key can then be used to decrypt any secrets using SOPS rather
than managing the secrets, you manage only the key, which tremendously simplifies templating.

### Generate identities

```bash
age-keygen -o securia.key
age-keygen -o github_actions.key
age-keygen -o azure_devops.key
```

### Encrypt

Here you can encrypt a secret for a specific identity, or multiple identities

```bash
cat image1.jpeg | age -r age1yzynsad4vklswdacwm7jq6hptd9u9n9v3lq9l3xdhfcyke94a9lsa82xh6 > image.jpeg.age
```

### Decrypt

```bash
age -d -i securia.key -o test.jpeg image.jpeg.age
```

or via SOPS

## Token for Kubernetes Dashboard use

```bash
lk -n kubernetes-dashboard get secrets admin-user -o yaml | yq .data.token | base64 -d
```

## Database bootstrap

The bootstrap and user creation is handled by the percona operator helm chart.

The passwords are collected from the cluster secrets. In future i'll set them to inject as a secret and map via ENV using envYAML routines

Setting access is still a pain

below works in dbbeaver

```sql
@set name = securiaapi
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public to ${name};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${name};
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ${name};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO ${name};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO ${name};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO ${name};
```

## Ultralytics review

with gpu support

```bash
sudo docker run -it --ipc=host --gpus all -v ./pics_http:/pics_http ultralytics/ultralytics:latest bash
```

## without gpu support

```bash
sudo docker run -it --ipc=host -v ./pics_http:/pics_http ultralytics/ultralytics:latest bash
```

## Models

Here's the information converted into a markdown table:

| Model | Filenames | Task |
|-------|-----------|------|
| YOLOv8 | yolov8n.pt yolov8s.pt yolov8m.pt yolov8l.pt yolov8x.pt | Detection |
| YOLOv8-seg | yolov8n-seg.pt yolov8s-seg.pt yolov8m-seg.pt yolov8l-seg.pt yolov8x-seg.pt | Instance Segmentation |
| YOLOv8-pose | yolov8n-pose.pt yolov8s-pose.pt yolov8m-pose.pt yolov8l-pose.pt yolov8x-pose.pt yolov8x-pose-p6.pt | Pose/Keypoints |
| YOLOv8-obb | yolov8n-obb.pt yolov8s-obb.pt yolov8m-obb.pt yolov8l-obb.pt yolov8x-obb.pt | Oriented Detection |
| YOLOv8-cls | yolov8n-cls.pt yolov8s-cls.pt yolov8m-cls.pt yolov8l-cls.pt yolov8x-cls.pt | Classification |

## Tests

```bash
yolo segment predict model=yolov8n-seg.pt source='/pics_http/image_20240810_121023.jpg' imgsz=640 save_txt=true
```

```bash
yolo detect predict model=yolov8l.pt source='/pics_http/image_20240810_13*.jpg' imgsz=640 save_txt=true
```

## Typical output

```text
image 1/24 /pics_http/image_20240810_131411.jpg: 544x640 (no detections), 903.8ms
image 2/24 /pics_http/image_20240810_131417.jpg: 544x640 (no detections), 874.6ms
image 3/24 /pics_http/image_20240810_131422.jpg: 544x640 (no detections), 882.0ms
image 4/24 /pics_http/image_20240810_131427.jpg: 544x640 (no detections), 886.1ms
image 5/24 /pics_http/image_20240810_131432.jpg: 544x640 (no detections), 872.5ms
image 6/24 /pics_http/image_20240810_131437.jpg: 544x640 (no detections), 844.9ms
image 7/24 /pics_http/image_20240810_131442.jpg: 544x640 (no detections), 871.9ms
image 8/24 /pics_http/image_20240810_131447.jpg: 544x640 (no detections), 1311.1ms
image 9/24 /pics_http/image_20240810_131452.jpg: 544x640 (no detections), 1480.4ms
image 10/24 /pics_http/image_20240810_131457.jpg: 544x640 (no detections), 1421.8ms
image 11/24 /pics_http/image_20240810_131503.jpg: 544x640 (no detections), 1477.3ms
image 12/24 /pics_http/image_20240810_131508.jpg: 544x640 1 person, 1396.7ms
image 13/24 /pics_http/image_20240810_131513.jpg: 544x640 1 person, 1 bottle, 1384.9ms
image 14/24 /pics_http/image_20240810_131518.jpg: 544x640 1 person, 1 handbag, 1509.5ms
image 15/24 /pics_http/image_20240810_131523.jpg: 544x640 1 person, 1416.9ms
image 16/24 /pics_http/image_20240810_131528.jpg: 544x640 (no detections), 1331.6ms
image 17/24 /pics_http/image_20240810_131533.jpg: 544x640 (no detections), 1356.8ms
image 18/24 /pics_http/image_20240810_131539.jpg: 544x640 (no detections), 1488.3ms
image 19/24 /pics_http/image_20240810_131544.jpg: 544x640 (no detections), 1381.9ms
image 20/24 /pics_http/image_20240810_131549.jpg: 544x640 1 person, 1381.1ms
image 21/24 /pics_http/image_20240810_131554.jpg: 544x640 (no detections), 1361.0ms
image 22/24 /pics_http/image_20240810_131559.jpg: 544x640 (no detections), 1343.6ms
image 23/24 /pics_http/image_20240810_131604.jpg: 544x640 (no detections), 1334.7ms
image 24/24 /pics_http/image_20240810_131610.jpg: 544x640 (no detections), 1386.0ms
```

`securia/pics_http/results/image_20240810_131508.jpg`