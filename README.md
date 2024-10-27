# Security-AI

Currently securia because i spelled like an idiot.. i was thinking actually SECURAI.

## Summary

Securia is a highly scalable, containerised image classifier and object detector based on YOLO. Every image capture is split by recorder-channel to kafka, which is consumed by
any number of preprocessors, shipped to s3 and then processed by any number of YOLO processors. Output is then processed to PostgreSQL, fronted
by FastAPI driven streamlit dashboard for data driven analytics around
your CCTV camera metadata extracted from the above processes.

## Review

<https://medium.com/@MrBam44/yolo-object-detection-using-opencv-with-python-b6386c3d6fc1>

<https://github.com/roboflow/supervision?tab=readme-ov-file>

<https://github.com/WongKinYiu/yolov7?tab=readme-ov-file>

<https://github.com/ultralytics/ultralytics>

<https://github.com/AlexanderMelde/SPHAR-Dataset/releases>

<https://github.com/openlit/openlit>

<https://huggingface.co/keras-io/low-light-image-enhancement>

UI for YoloV8

<https://github.com/Paperspace>

## Project Diagram

[Project Diagram](SecurAI.drawio)

## Main points

Event driven exception handling with DLQ for CCTV camera scraping, object prediction and cropping.

Review [Project Diagram](SecurAI.drawio) for the big-picture

Local dev is k3s + strimzi + kdashboard + percona pstgresql + s3ninja

Dev is k3s + strimzi + rancher + harbor + percona + s3ninja + github actions

## TODO


- llm dev - implement the guard, collection of recent events -> context -> response
- llm dev - implement the analyst, function -> llm -> pydantic -> dataset -> llm -> response
- ui dev - detections, xyxy overlays
- ui dev - per recorder configuration of yolo and llm settings, ignored objects, static objects

- create additional tables to manage user preferences to detection filters, confidence levels and recorders and channels
- user_preferences, user_recorder_attachment, recorder_preferences, channel_preferences, detection_preferences. basically a preference management overlay
- seen_detections table to manage which detections are "interesting"
- add sqlalchemy preferrence filter query stacking where possible... eeeish
- ui development
- ui dev - llm - implement image description extraction into channel description with edits
- detection filtering and ignore list
- detection summaries across recorder

- builds current take about 8 minutes, which is not bad, but i can get it lower
  - https://www.kenmuse.com/blog/building-github-actions-runner-images-with-a-tool-cache/
  - https://gha-cache-server.falcondev.io/getting-started

- metric system development, start getting that together
- sqlalchemy can export to collectd `docker pull collectd/ci:focal_amd64`

- training and xyxy overlays
- implement "remember me" cookies, and expiry notifications for ui
- test crop extraction and population
- test crop storage and repopulation (to reduce storage/transfer costs by only storing the crops and no event backgrounds by overlaying the crops)
- expand api auth to keycloak and social auth

- bug - the kafka needs to be more "safe" on exit, the exit loop is just crashing it out.
- also implement proper aging on the topics, were going to run out of space quickly in odd places.
- video stream server for live dash? (grab latest images, collage them and display?)
- switch collectors to central driven enrolment style (collector api polling for what to collect, with scaling)
- add ability to mark a user as disabled
- user driven recorder creation and attachment to collectors
- also develop out a image movement cluster analysis for lightweight, non-yolo based detection as first round identification in parallel
- collector registration system, which allows linking recorders to collectors
- kafkaadmin routine to create topics with the correct partition count based on channel and recorder creation
- bug - increase partition counts to at least 5 per topic to allow better balancing to processors - will be rolled into kafkadmin routines
- check if transaction-id is not mis-used in our case, there was a future purpose to it, but it might need to to be re-engineered already.
- configure securia charts to use the secrets from percona operator via secret injection, then database user management is automated, same for kafkauser
- longer term, were going to be multi-tenant, this requires ownership and membership systems

## In Testing

## DONE

- token expiry issue - fixed, login routine reuse bug
- connection pool issues - fixed, background task manager not returning connections
- pruning system background task manager - done
- Turn gpustat --json into prometheus metrics (will need to watch temps) - no longer necessary, have nvidia exporter in cluster now
- working on improved deployment pipeline - arogocd is done, works pretty good!
- user create api is missing the optional fields, i think they are just not mapped - fixed
- simplify the ACL checker into something oneliny to reduce the code duplication for the api controller - don't think it is possible yet
- channel descriptions and friendly names are vital for LLM integration, make it easier to do by providing a preview image
- ui dev - multipage navigator, build out pages - done
- ui dev - a bit more fleshed out - done
- develop image/psql pruning system, it gets out of control pretty quick, also needed to be able to delete anyway - done, images and metadata staggered pruning
- i think i have a decent baseline now on approaching streamlit ui development - done
- profile management - lightweight version done, yes i'm putting off the image stuff - done
- channel management - done
- next up is recorder management - done
- busy with a basic user management ui - done
- fixed bug with recorder_uuid and bulletproofed the db create on new
- revamped the authentication for all services, and added ACL checks for get services as well to have a role of at least guest for GET, all other CRUD needs at least user, and user manipulation needs your user to be above any other user - done
- cleaned up logger code and fixed scheduler code as well - done
- migrated all services from flask to fastapi, and introduced asyncio - done
- introduced /health endpoint so kubernetes can pay attention to it - done
- bug - the containers do not exit/restart properly sometimes. such as when the api service is unavailable. - this is now much improved
- improved authentication handling class for services that talk to the api, including token refresh handling - done
- improved scheduler module code, it should no longer now be "blocking"
- turfflehog scan confirms no secrets in repo - done
- removed all other secrets from github actions, only the AGE secret is there now, the rest is SOPS managed! - done
- added harbor LB IP instead of running to the internet router - done (there has got to be an operator for that really) - build time down to 2 mins
- setup cicd cache based building for images - done
- optimised build with docker buildx bake, and setup layer caching=max to harbor - done (8 minutes now)
- increased temp storage for job-runner, might have to give it a PVC eventually.. my 256Gb root drives are getting tiny - done
- move arc runners to homelab - done
- work on the CICD automation for securia deployment to dev (SOPS setup in github actions) - done
- bug - recorders by uri not right - switched to UUID
- bug - kafka services don't scan for topic changes over time, so new topics don't find the prefixes - Refreshes every 30 seconds now
- refactored authentication for microservices to the db driven version, standardised to authbearer class
- introduced uuid for recorders to avoid conflicts and the bug
- create access control and hierarchy of who can edit what - done
- create role based access sytem - super, admin, user, guest. user and up can CRUD, guest can R - done
- create the rest of the crud for system admin and management - done
- implemented a startup admin user creation routine, the password is printed in console logs once, if you lose it, you will need to delete the user in the db - done
- implemented a user login system with ability to link users(owners) to recorders, and set the basics for role based access to the system too - done
- implemented user datatables and ownership linking fields - done
- implemented a basic good enough for now api authentication system using JWT - done (to test widely) - done
- migrate any secret information to SOPS - done
- move main stack to server side with github actions - in testing
- full install the stack into dev (minimum feature set to include xyxy extraction) - done
- test yolo helm on gpu server - done (gpu is a must, some numbers below on performance)
- strimzi deployment on dev - done
- helm secrets - done
- full grafana deployment - done
- move nfs provisioner to server - done, 800Gb space
- deploy s3 emulation - done
- redeploy harbor - done
- deploy postgresql to dev cluster - done
- move s3 to nfs provisioner eventually for more storage - done
- redeploy keycloak - done

## Some lessons

### CPU vs GPU

An i7 compared against a laptop T500 with 2Gb RAM, the GPU can process an image is about 60ms, while the CPU takes 1200ms.

Thus, single channel is fine at 2-5s interval on CPU, but anything more will fall behind. It runs via eventing so it will just start lagging further and further. If you stop the cameras, it will catch up again.

### Streamlit

So here is how i approach streamlit after some hours, it probably a "duh" moment, but that is just me. Basically think of the code as a script that executes top to bottom that renders the page every time you interact or something else interacts with it, so if you want to control a thing, you would if it out and if it in, or use state variables to if them in and out. State variables are your friends, but also an enemy. Certain things like button states obviously "stick". so if you lets say have a workflow with multiple dataframes that click through, you need to be careful not to "reset" higher up code, or basically remember that the first dataframes needs to render again when you interact "anything" on the page, so you can get access to the lower levels again, thus your python "script" tree needs to exec through to the same paths you want, top to bottom every time anything happens on the page.

## Building and Deployment Pipeline

### CICD Sumary

- Github Actions
- actions-runner in homelab cluster with access to the cluster for helm and kubectl
- clusterpullsecrets used to not need to worry about it, pipelined
- helmfile in use plus SOPS/AGE in /helm for declarative git based control and templating
- docker buildx bake, definition for securia from docker-compose.yaml in /src, which is also then provides declarative git control
- docker-compose includes caching system to local registry, in cluster, significantly speeding up containerised building/downloading
- coredns modified to point all cluster services to loadbalancer ips (Traefik LB), avoiding any packets bouncing to firewall

## Local Dev Env Links

- Dashboard - <https://localhost:32281>
- S3 Ninja  - <http://localhost:32650/ui>
- PGBouncer - 10.0.0.59:32617
- Kafka     - localhost:32394
- Kafka UI  - <http://localhost:31202>
- Registry  - 10.0.0.59:32419
- Ingres    - 10.0.0.59:443
- API Docs  - <http://localhost:30578/docs>

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

The idea is to create a simple portable way to allow secret decryption to any CICD systems regardless of "provider".

Typically

- Github Actions -> Secrets/EnvSecrets/RepoSecrets
- Azure DevOps -> Secrets / Keyvaults
- AWS -> Vaults
- GCP KMS -> secrets

You end up customising CICD for each and they both have slightly different interactions and requirements and flows.

A simple "local-dev-managed" way would be to use SOPS and AGE, and setting up an identity each for the provider(s).

Set up the right way, this extends to any pipeline provider and system
as the same process applies.

You then only need to provide the AGE identity to the provider as a secret, instead of the secrets for the applications.

They can then decrypt any secrets using SOPS/helm rather than you managing the secrets at the provider.

In future, this can be swapped easily to use a cloud key providers to encrypt and decrypt, thus allowing much bigger teams of people to contribute while still being CICD agnostic and define access via provider/arn role based security.

<https://github.com/trufflesecurity/trufflehog> can be used to check the repo for any secret leaks

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

Encrypting/decryipting dotenv files

```bash
sops -i -e --input-type dotenv --output-type dotenv .env.secrets
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

- <https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8l.pt>

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

## Clean slate start up

- push images
- push charts
- deploy application
- connect to api/docs - login with anything to create superuser
- check the logs for the initial superuser details
- login with the superuser on api/docs and create the necessary users for the other services
- create your own admin user if you want
- restart services


## Further research

https://github.com/defog-ai/sqlcoder


