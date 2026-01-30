#!/bin/sh
set -eu

if [ -n "${CI_COMMIT_TAG+x}" ]; then
  CACHE_TAG1=$CI_COMMIT_SHA
  CACHE_TAG2=$CI_COMMIT_BEFORE_SHA
elif [ "$CI_COMMIT_BRANCH" = "main" ]; then
  CACHE_TAG1=main
  CACHE_TAG2=$CI_COMMIT_BEFORE_SHA
elif [ "$CI_COMMIT_BRANCH" = "develop" ]; then
  CACHE_TAG1=develop
  CACHE_TAG2=$CI_COMMIT_BEFORE_SHA
else
  CACHE_TAG1=develop
  CACHE_TAG2=$CI_COMMIT_REF_SLUG
fi

export CACHE_TAG1
export CACHE_TAG2
