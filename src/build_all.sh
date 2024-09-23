#!/bin/bash
export $(grep -v '^#' .env | xargs -d '\n')
sops -i -d --input-type dotenv --output-type dotenv .env.secrets
export $(grep -v '^#' .env.secrets | xargs -d '\n')
sops -i -e --input-type dotenv --output-type dotenv .env.secrets
docker buildx bake --push --builder=container
# for dir in */; do
#   if [ -d "$dir" ]; then
#     image_name=$(echo "${dir%/}" | tr '-' '_')
#     docker buildx build --push $dir/ -t ${REGISTRY_HOST}/securia/$image_name:latest
#   fi
# done