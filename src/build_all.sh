#!/bin/bash
export $(grep -v '^#' .env | xargs -d '\n')
export $(grep -v '^#' ../helm/.env | xargs -d '\n')
sops -i -d --input-type dotenv --output-type dotenv .env.secrets
export $(grep -v '^#' .env.secrets | xargs -d '\n')
sops -i -e --input-type dotenv --output-type dotenv .env.secrets
docker buildx bake --push --builder=container
docker buildx prune --all