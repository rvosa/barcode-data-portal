#!/bin/sh
set -eu

docker pull hashicorp/vault:latest
# check if VAULT_TOKEN is empty if so exit with error
if [ -z "$VAULT_TOKEN" ]; then
  echo "VAULT_TOKEN is empty - could not get token from vault"
  exit 1
fi

mkdir ansible/inventory
mkdir ansible/inventory/group_vars
mkdir ansible/inventory/host_vars

# Retrieve hosts inventory
FULL_SECRET_PATH="kv2/$VAULT_PATH/hosts"
docker run --cap-add=IPC_LOCK --env VAULT_TOKEN hashicorp/vault:latest vault kv get -field data --format=yaml -address="$VAULT_SERVER_URL" "$FULL_SECRET_PATH" > "ansible/inventory/hosts.yml"

# Retrieve all group_vars
FULL_SECRET_PATH="kv2/$VAULT_PATH/group_vars"
CONFIGS=$(docker run --cap-add=IPC_LOCK --env VAULT_TOKEN hashicorp/vault:latest vault kv list -address="$VAULT_SERVER_URL" "$FULL_SECRET_PATH" | tail -n +3)
for config in $CONFIGS; do
    docker run --cap-add=IPC_LOCK --env VAULT_TOKEN hashicorp/vault:latest vault kv get -field data --format=yaml -address="$VAULT_SERVER_URL" "$FULL_SECRET_PATH/${config}" > "ansible/inventory/group_vars/${config}.yml"
done

# Retrieve all host_vars, remove comments '#' when hosts_vars are needed
FULL_SECRET_PATH="kv2/$VAULT_PATH/host_vars"
CONFIGS=$(docker run --cap-add=IPC_LOCK --env VAULT_TOKEN hashicorp/vault:latest vault kv list -address="$VAULT_SERVER_URL" "$FULL_SECRET_PATH" | tail -n +3)
for config in $CONFIGS; do
    docker run --cap-add=IPC_LOCK --env VAULT_TOKEN hashicorp/vault:latest vault kv get -field data --format=yaml -address="$VAULT_SERVER_URL" "$FULL_SECRET_PATH/${config}" > "ansible/inventory/host_vars/${config}.yml"
done
