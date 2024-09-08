# Security-AI

Currently securia because i spelled like an idiot.. i was thinking actually SECURAI.

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

## Project Diagram

[Project Diagram](SecurAI.drawio)

## Main points

Event driven exception handling with DLQ for CCTV camera scraping, object prediction and cropping.

Review [Project Diagram](SecurAI.drawio) for the big-picture

Local dev is k3s + strimzi + kdashboard + percona pstgresql + s3ninja

## Some lessons

CPU vs GPU

An i7 compared against a laptop T500 with 2Gb RAM, the GPU can process an image is about 60ms, while the CPU takes 1200ms.

Thus, single channel is fine at 2-5s interval on CPU, but anything more will fall behind. It runs via eventing so it will just start lagging further and further. If you stop the cameras, it will catch up again.

## TODO

- test crop extraction and population
- work on the CICD automation for securia deployment to dev (SOPS setup in github actions)
- migrate any secret information to SOPS - good progress
- move main stack to server side with github actions - halfway
- full install the stack into dev (minimum feature set to include xyxy extraction)
- ui development - streamlit looks promising
- Turn gpustat --json into prometheus metrics (will need to watch temps)
- work on OIDC integration
- test yolo helm on gpu server - done (gpu is a must, some numbers below on performance)
- configure securia charts to use the secrets from percona operator via injection
- strimzi deployment on dev - done
- helm secrets - done
- full grafana deployment - done
- move nfs provisioner to server - done, 800Gb space
- deploy s3 emulation - done
- redeploy harbor - done
- deploy postgresql to dev cluster - done
- move s3 to nfs provisioner eventually for more storage - done
- redeploy keycloak - done

## Local Dev Env Links

- Dashboard - https://localhost:32281
- S3 Ninja  - http://localhost:32650/ui
- PGBouncer - 10.0.0.59:32617
- Kafka     - localhost:32394
- Kafka UI  - http://localhost:31202
- Registry  - 10.0.0.59:32419
- Ingres    - 10.0.0.59:443
- API Docs  - http://localhost:30578/docs

## Local dev setup

Review the readmes in [infra](infra) folder:

- k3s
- strimzi
- postgresql
- registry
- s3emu
- github-actions-runner

## Secrets management

age + sops + helm + vscode

The idea is to create a simple portable way to allow secret decryption to CICD systems regardless of "provider".

- Github Actions -> Secrets/EnvSecrets/RepoSecrets
- Azure DevOps -> Secrets / Keyvaults
- AWS -> Vaults
- etc -> etc

You end up customising for each and they both have slightly different interactions.

A simple "local-dev-managed" way would be to use SOPS and AGE, and setting up an identity each for the provider(s).

You then only need to provide that identity to the provider as a secret, instead of the secrets for the applications.

They can then decrypt any secrets using SOPS/helm rather than you managing the secrets at the provider.

## AGE + SOPS

### Installation

install AGE

```bash
mkdir age_setup ; cd age_setup
curl -LO https://github.com/FiloSottile/age/releases/download/v1.2.0/age-v1.2.0-linux-amd64.tar.gz
tar xvfp age-v1.2.0-linux-amd64.tar.gz
sudo mv age/age /usr/local/bin/age
sudo mv age/age-keygen /usr/local/bin/age-keygen
sudo chmod +x /usr/local/bin/age
sudo chmod +x /usr/local/bin/age-keygen
rm -r age_setup
age --version
```

install SOPS

```bash
mkdir age_setup ; cd age_setup
curl -LO https://github.com/getsops/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64
mv sops-v3.9.0.linux.amd64 /usr/local/bin/sops
chmod +x /usr/local/bin/sops
sops --version
```

### Generate identities

generate as needed for any system that needs to be able to decrypt, CICD, friends, not family.

```bash
age-keygen -o securia.key
age-keygen -o github_actions.key
age-keygen -o azure_devops.key
```

### Create sops config file

see .sops.yaml in the repo

Basically it contains the identities that we need to be able to decrypt files, and the files we want to stay encrypted as a regex match.

I elected to use `*_secrets.yaml` (as i will mostly be encrypting yaml values for helm or otherwise yaml manifests).

### Encrypt Process

You can encrypt any file, sops will pick up the keys from .sops.yaml. -i is for "in-place"

```bash
echo "text: hello there" > test.yaml
sops --config .sops.yaml encrypt -i test.yaml
```

### Decrypt Process

```bash
export SOPS_AGE_KEY_FILE=${HOME}/iot/securia/securia.key
sops --config .sops.yaml decrypt -i test.yaml
```

It is safe to try and decrypt any file, if it does not have the SOPS metadata, it does nothing, so you can loop over all files safely if you need to mass decrypt.

### VSCode

This extension looks at the path regex in your .sops.yaml and automagically encrypt and decrypts files that match, allowing you to edit files directly, and it seamlessly handles encryption and decryption in the background

[VSCode SOPS](https://marketplace.visualstudio.com/items?itemName=signageos.signageos-vscode-sops)

### Helm integration

```bash
helm plugin install https://github.com/jkroepke/helm-secrets
```

Then you can you use protobuff like this to trigger the plugin, which will read the SOPS_AGE_KEY_FILE env var for the identity to use to decrypt, it will decrypt if the public key was in the .sops.yaml.

`helm upgrade name . -f normal_values.yaml -f secrets://secrets.yaml`

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

### Requirements for docker gpu support

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

```bash
sudo docker run -it --ipc=host --gpus all -v ./test_images:/pics_http ultralytics/ultralytics:latest bash
```

## without gpu support

```bash
sudo docker run -it --ipc=host -v ./test_images:/pics_http ultralytics/ultralytics:latest bash
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

- https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8l.pt

## Tests

```bash
yolo segment predict model=yolov8n-seg.pt source='/pics_http/*' imgsz=640 save_txt=true
```

```bash
yolo detect predict model=yolov8l.pt source='/pics_http/*' imgsz=960 save_txt=true
```

## Yolo performance testing

yolov8l.pt

- NVIDIA GeForce GTX 1650, 3889MiB - 95ms - can possibly fit 2x pods
- NVIDIA T500 2Gb, 1871MiB - 74ms - uses all memory, single pod only
- Intel Core(TM) i7-1165G7 2.80GHz - 950ms - single channel only (at 2 sec intervals)

## Image Change Detection Methods

- Image differencing: Comparing corresponding pixels between two images and identifying areas where values differ significantly.
- Background subtraction: Creating a model of the background and detecting changes by comparing new frames against this model.
- Feature-based methods: Extracting and comparing features (e.g., edges, corners, or SIFT features) between images to identify changes.
- Deep learning approaches: Using convolutional neural networks (CNNs) or other deep learning architectures to learn and detect changes automatically.
- Motion detection: Analyzing pixel changes between consecutive frames in video to identify moving objects.
- Thresholding: Applying a threshold to the difference image to highlight areas of significant change.
- Change vector analysis: Comparing multi-spectral or multi-temporal images to detect changes in land cover or use.
- Object-based change detection: Segmenting images into objects and comparing their properties between images.