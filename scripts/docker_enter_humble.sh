#!/usr/bin/env bash
set -e

CONTAINER_NAME="roboarm_humble"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[INFO] Container is not running. Starting it..."
    docker start "${CONTAINER_NAME}" >/dev/null
fi

docker exec -it "${CONTAINER_NAME}" bash
