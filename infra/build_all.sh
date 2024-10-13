#!/bin/bash
export $(grep -v '^#' .env | xargs -d '\n')
export $(grep -v '^#' ../helm/.env | xargs -d '\n')
eval "$(sops -d --input-type dotenv --output-type dotenv .env.secrets | grep -v '^#' | sed 's/^/export /')"
docker buildx bake --push --builder=container
docker buildx prune --all --force