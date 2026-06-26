#!/usr/bin/env sh
set -eu

docker compose -f infra/docker-compose.dev.yml logs -f kairos-api
