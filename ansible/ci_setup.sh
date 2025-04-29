#!/bin/sh
set -eu

basedir=$(dirname "$0")

# check if VAULT_TOKEN is empty if so exit with error
if [ -z "$VAULT_TOKEN" ]; then
  echo "VAULT_TOKEN is empty - could not get token from vault"
  exit 1
fi

ANSIBLE_DEPLOY_KEY=$(docker run --cap-add=IPC_LOCK --env VAULT_TOKEN hashicorp/vault:latest vault kv get -field ANSIBLE_DEPLOY_KEY -address="$VAULT_SERVER_URL" "kv2/$VAULT_PATH/cicd")
if [ -z "$ANSIBLE_DEPLOY_KEY" ]; then
  echo "ANSIBLE_DEPLOY_KEY is empty - could not get deploy key from vault"
  exit 1
fi

mkdir -m 700 "$basedir/secrets"
echo "$ANSIBLE_DEPLOY_KEY" | base64 -d > "$basedir/secrets/id_ed25519"
chmod 400 "$basedir/secrets/id_ed25519"
