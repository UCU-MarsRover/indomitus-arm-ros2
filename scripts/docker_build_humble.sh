#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

docker build \
  -f docker/Dockerfile.humble \
  -t roboarm_humble:latest \
  .
