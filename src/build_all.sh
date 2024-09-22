#!/bin/bash
export $(grep -v '^#' .env | xargs -d '\n')
for dir in */; do
  if [ -d "$dir" ]; then
    image_name=$(echo "${dir%/}" | tr '-' '_')
    docker buildx build --push $dir/ -t ${REGISTRY_HOST}/securia/$image_name:latest
  fi
done