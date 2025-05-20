#!/bin/bash
set -e

# Configuration
REMOTE_USER="your-ssh-user"
REMOTE_HOST="your-onprem-server-ip-or-hostname"
REMOTE_APP_DIR="/path/to/your/app"
LOCAL_BUILD=${1:-false}  # Set to 'true' to build locally before deploying

# Files to copy to the server
FILES=("Dockerfile" "requirements.txt" "main.py" "tools.py" "utils.py" "agent.py" "static_workflow.py" "docker-compose.prod.yml")

# Create .env.prod from .env if it doesn't exist
if [ ! -f .env.prod ]; then
    echo "Creating .env.prod from .env"
    cp .env .env.prod
    echo "Please review and update .env.prod with production values"
    exit 1
fi

echo "Deploying to $REMOTE_USER@$REMOTE_HOST:$REMOTE_APP_DIR"

# Create remote directory
echo "Creating remote directory..."
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_APP_DIR"

# Copy files
echo "Copying files..."
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        scp "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_APP_DIR/"
    else
        echo "Warning: $file not found, skipping..."
    fi
done

# Copy production environment file
scp .env.prod "$REMOTE_USER@$REMOTE_HOST:$REMOTE_APP_DIR/.env"

# Build and deploy
echo "Building and deploying..."
ssh $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_APP_DIR && \
    echo 'Stopping and removing existing containers...' && \
    docker-compose -f docker-compose.prod.yml down && \
    echo 'Pulling latest changes...' && \
    git pull && \
    echo 'Building new image...' && \
    docker-compose -f docker-compose.prod.yml build --no-cache && \
    echo 'Starting services...' && \
    docker-compose -f docker-compose.prod.yml up -d && \
    echo 'Cleaning up...' && \
    docker system prune -f"

echo "Deployment complete!"
