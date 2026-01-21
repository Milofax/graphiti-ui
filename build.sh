#!/bin/bash
# Build Graphiti UI container

set -e

cd "$(dirname "$0")"

echo "Building Graphiti UI container..."
docker build -t graphiti-ui:latest .

echo ""
echo "Done."
echo ""
echo "For local development:"
echo "  docker compose -f docker-compose.example.yml up -d"
echo ""
echo "For production (from /v/graphiti/):"
echo "  docker compose up -d"
