#!/bin/sh
set -eu

if [ -z ${1+x} ]; then
  echo Missing name argument
  exit 1
fi
name=$1
image=$CI_REGISTRY_IMAGE/$name:build_$CI_COMMIT_REF_SLUG

docker pull "$image"

if [ -n "${CI_COMMIT_TAG+x}" ]; then
  docker tag "$image" "$CI_REGISTRY_IMAGE/$name:$CI_COMMIT_TAG"
  docker push "$CI_REGISTRY_IMAGE/$name:$CI_COMMIT_TAG"
  exit 0
fi

docker tag "$image" "$CI_REGISTRY_IMAGE/$name:$CI_COMMIT_REF_SLUG"
docker tag "$image" "$CI_REGISTRY_IMAGE/$name:$CI_COMMIT_SHA"
docker tag "$image" "$CI_REGISTRY_IMAGE/$name:$CI_PIPELINE_ID"

if [ "$CI_COMMIT_BRANCH" = "develop" ]; then
  docker tag "$image" "$CI_REGISTRY_IMAGE/$name:latest"
  docker push "$CI_REGISTRY_IMAGE/$name:latest"
fi

docker push "$CI_REGISTRY_IMAGE/$name:$CI_COMMIT_REF_SLUG"
docker push "$CI_REGISTRY_IMAGE/$name:$CI_COMMIT_SHA"
docker push "$CI_REGISTRY_IMAGE/$name:$CI_PIPELINE_ID"
