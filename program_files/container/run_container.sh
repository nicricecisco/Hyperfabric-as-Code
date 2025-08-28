#!/usr/bin/env bash
set -euo pipefail

# ---------------------------
# CONFIGURATION
# ---------------------------

IMAGE_NAME="nicricecisco/hyperfabric-as-code-container:latest"
CONTAINER_NAME="hyperfabric-as-code-container"
VOLUME_NAME="hyperfabric_workspace"
HOST_PORT="8080"
CONTAINER_PORT="8080"
#WORKSPACE_DIR="./workspace"  # Optional bind mount for testing (comment out to use only named volume)

# ---------------------------
# DETECT RUNTIME
# ---------------------------

if command -v podman >/dev/null 2>&1; then
    RUNTIME="podman"
elif command -v docker >/dev/null 2>&1; then
    RUNTIME="docker"
else
    echo "Error: Neither podman nor docker is installed."
    echo "Please install podman (recommended) or docker, then re-run this script."
    exit 1
fi

echo "Using container runtime: $RUNTIME"

# ---------------------------
# CREATE NAMED VOLUME IF MISSING
# ---------------------------

if ! $RUNTIME volume inspect "$VOLUME_NAME" >/dev/null 2>&1; then
    echo "Creating named volume: $VOLUME_NAME"
    $RUNTIME volume create "$VOLUME_NAME"
fi

# ---------------------------
# REMOVE OLD CONTAINER (IF ANY)
# ---------------------------

if $RUNTIME ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}\$"; then
    echo "Removing old container: $CONTAINER_NAME"
    $RUNTIME rm -f "$CONTAINER_NAME"
fi

# ---------------------------
# OPTIONAL: pull the latest image (works for public GHCR without login)
# ---------------------------

echo "Pulling latest image..."
$RUNTIME pull "$IMAGE_NAME" || true

# ---------------------------
# RUN CONTAINER
# ---------------------------

echo "Starting container..."
$RUNTIME run -d \
    --name "$CONTAINER_NAME" \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    --mount type=volume,src="$VOLUME_NAME",dst=/workspace \
    $IMAGE_NAME

echo  "Container '$CONTAINER_NAME' is running on http://localhost:${HOST_PORT}"
