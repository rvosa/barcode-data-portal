#!/bin/sh
set -eu

if [ -z ${CACHE_TAG1+x} ] || [ -z ${CACHE_TAG2+x} ]; then
  echo Missing cache tag variables
  exit 2
fi

basedir=$(dirname "$0")

# Build fastapi-app container
name="fastapi-app"

docker pull "$CI_REGISTRY_IMAGE/$name:$CACHE_TAG1" || true
docker pull "$CI_REGISTRY_IMAGE/$name:$CACHE_TAG2" || true
docker build --pull --cache-from "$CI_REGISTRY_IMAGE/$name:$CACHE_TAG1" --cache-from "$CI_REGISTRY_IMAGE/$name:$CACHE_TAG2" \
  --tag "$CI_REGISTRY_IMAGE/$name:build_$CI_COMMIT_REF_SLUG" -f "$basedir/Dockerfile" .
docker push "$CI_REGISTRY_IMAGE/$name:build_$CI_COMMIT_REF_SLUG"

# Build socketserver-logging container
name="socketserver-logging"

docker pull "$CI_REGISTRY_IMAGE/$name:$CACHE_TAG1" || true
docker pull "$CI_REGISTRY_IMAGE/$name:$CACHE_TAG2" || true
docker build --pull --cache-from "$CI_REGISTRY_IMAGE/$name:$CACHE_TAG1" --cache-from "$CI_REGISTRY_IMAGE/$name:$CACHE_TAG2" \
  --tag "$CI_REGISTRY_IMAGE/$name:build_$CI_COMMIT_REF_SLUG" -f "$basedir/Dockerfile.socketserver_logging" .
docker push "$CI_REGISTRY_IMAGE/$name:build_$CI_COMMIT_REF_SLUG"