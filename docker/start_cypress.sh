#!/bin/sh
set -eu

docker create \
    --name barcode-data-portal_cypress \
    --network barcode-data-portal_web \
    -v "$PWD/src/cypress":/usr/src/app \
    -v "$PWD/src/cypress/node_modules":/usr/src/app/node_modules \
    cypress/base sh -c \
  "set -eu
  getent hosts traefik | awk '{ print \$1\" boldsystems.dryrun.link\" }' >> /etc/hosts
  cd /usr/src/app

  npm install
  npx cypress install
  npx cypress run"

docker start --attach barcode-data-portal_cypress
