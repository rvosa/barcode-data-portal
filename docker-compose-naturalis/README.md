# Naturalis Docker setup

## Standalone

The docker-compose files in the Standalone directory can be used for local development. 
This includes the complete site, including the FastAPI application and the Couchbase cluster. 
Note that you will be able to import some sample data into the cluster, 
but that it's impossible to load the complete BOLD data.

You can start the application using

`docker compose -f docker-compose-naturalis/standalone/docker-compose.yml up -d`

## Cluster

BOLD needs a dedicated Couchbase cluster to function properly, 
the size of which is impossible to replicate on a local machine. 
The deployment of Couchbase is handled in a dedicated 
[Ansible repository](https://gitlab.com/naturalis/bii/bge/ansible-bold). 
Contrary to other Naturalis applications, the versioning of Couchbase and Traefik therefore 
are handled outside this application repository. Only the versioning of the FastAPI application itself 
is handled in this repo.

## Precommit gitleaks

This project has been protected by [gitleaks](https://github.com/gitleaks/gitleaks).
The pipeline is configured to scan on leaked secrets.

To be sure you do not push any secrets,
please [follow our guidelines](https://docs.aob.naturalis.io/standards/secrets/),
install [precommit](https://pre-commit.com/#install)
and run the commands:

 * `pre-commit autoupdate`
 * `pre-commit install`