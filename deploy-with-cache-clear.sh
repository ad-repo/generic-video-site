#!/bin/bash

echo "🚀 Deploying with cache clearing..."

# Stop containers
echo "Stopping containers..."
sudo docker-compose -f docker-compose.yml down

# Ensure persistent database directory exists with proper permissions for SQLite
echo "Setting up persistent database directory..."
mkdir -p /volume1/dockerdata/generic-video-site/db
chmod 777 /volume1/dockerdata/generic-video-site/db
echo "✅ Database will persist in /volume1/dockerdata/generic-video-site/db/"

# Remove old image
echo "Removing old image..."
sudo docker rmi nas3/generic-video-site:local 2>/dev/null || echo "No old image to remove"

# Clean up everything
echo "Cleaning up Docker system..."
sudo docker system prune -af

# Remove any cached layers
echo "Removing build cache..."
sudo docker builder prune -af

# Rebuild with no cache using BuildKit
echo "Building new image with no cache using BuildKit..."
# Set environment variables for the entire command
sudo bash -c 'export DOCKER_BUILDKIT=1 && export COMPOSE_DOCKER_CLI_BUILD=1 && docker-compose -f docker-compose.yml build --no-cache --pull'

# Start containers
echo "Starting containers..."
sudo docker-compose -f docker-compose.yml up -d

echo "✅ Deployment completed with cache clearing!"
echo "Check your browser for the updated site."
echo "If you still see old content, try hard refresh (Ctrl+F5 or Cmd+Shift+R)"
