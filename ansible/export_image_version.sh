#!/bin/sh
set -eu

if [ -n "${CI_COMMIT_TAG+x}" ]; then
  IMAGE_VERSION=$CI_COMMIT_TAG
elif [ "$CI_PIPELINE_SOURCE" != "web" ] && [ "$CI_COMMIT_BRANCH" = "develop" ]; then
  IMAGE_VERSION=$CI_PIPELINE_ID
elif [ -n "$CI_COMMIT_BRANCH" ]; then
  # Convert to lowercase
  IMAGE_VERSION=$(echo "$CI_COMMIT_BRANCH" | tr '[:upper:]' '[:lower:]')
fi

export IMAGE_VERSION
