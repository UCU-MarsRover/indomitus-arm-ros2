#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONTAINER_NAME="roboarm_humble"

xhost +local:docker >/dev/null 2>&1 || true

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[INFO] Container ${CONTAINER_NAME} already exists."
    echo "[INFO] Starting existing container..."
    docker start "${CONTAINER_NAME}" >/dev/null
    docker exec -it "${CONTAINER_NAME}" bash
    exit 0
fi

docker run -it \
    --name "${CONTAINER_NAME}" \
    --net=host \
    --ipc=host \
    --privileged \
    -e DISPLAY="${DISPLAY}" \
    -e QT_X11_NO_MITSHM=1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "${PROJECT_DIR}":/ws/src/Roboarm \
    -w /ws \
    roboarm_humble:latest \
    bash
