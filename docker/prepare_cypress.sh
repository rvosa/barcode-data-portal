#!/bin/sh
set -eu

# Create symlink to db_data for sample data
mkdir -p data && ln -s ../db_data data/sample_data
# Directory for Couchbase data
mkdir -m 777 data/couchbase

# Create .env
cat <<EOF >> .env
DATA_PATH=./data
IMAGE_VERSION=${IMAGE_VERSION}
FQDN="boldsystems.dryrun.link"
COUCHBASE_DROP_CLUSTER_ON_START=true
APP_NAME="fastapi-app"
APP_PORT=8000
REDIS_HOST=redis
REDIS_PORT=6379
COUCHBASE_ENDPOINT="couchbase://couchbase"
COUCHBASE_USER=Administrator
COUCHBASE_PASSWORD=password
EOF

# Use the default docker-compose file that runs the site as localhost
docker run --rm -v "$PWD":"$PWD":ro -v /var/run/docker.sock:/var/run/docker.sock:ro \
   docker compose -f "$PWD/docker-compose-naturalis.yml" up -d
