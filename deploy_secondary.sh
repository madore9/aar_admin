#!/bin/bash
#
# Deploy script for secondary Docker containers on EC2
# Usage: ./deploy_secondary.sh <app-name> <app-path> [port]
#
# Example: ./deploy_secondary.sh myadmin /admin 8000
# Result: App accessible at https://<host>/admin/
#
# This script adds routing WITHOUT impacting the existing MCP server.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
APP_NAME="${1:-}"
APP_PATH="${2:-}"
APP_PORT="${3:-8000}"
EC2_HOST="${EC2_HOST:-10.138.149.157}"
PEM_FILE="${PEM_FILE:-myharvard-dev-mcp.pem}"

usage() {
    echo "Usage: $0 <app-name> <app-path> [port]"
    echo ""
    echo "Arguments:"
    echo "  app-name    Name of your application (e.g., 'myadmin', 'django-app')"
    echo "  app-path    URL path prefix (e.g., '/admin', '/portal')"
    echo "  port        Internal port (default: 8000)"
    echo ""
    echo "Examples:"
    echo "  $0 myadmin /admin 8000"
    echo "  $0 django-app /myapp 8000"
    echo "  $0 admin-panel /admin 9000"
    echo ""
    echo "Environment variables:"
    echo "  EC2_HOST       EC2 host (default: 10.138.149.157)"
    echo "  PEM_FILE        SSH key file (default: myharvard-dev-mcp.pem)"
    exit 1
}

# Validate inputs
if [ -z "$APP_NAME" ] || [ -z "$APP_PATH" ]; then
    usage
fi

# Sanitize app name (alphanumeric and hyphens only)
if ! [[ "$APP_NAME" =~ ^[a-zA-Z][a-zA-Z0-9-]*$ ]]; then
    echo -e "${RED}Error: App name must start with a letter and contain only alphanumeric characters and hyphens${NC}"
    exit 1
fi

# Ensure app_path starts with /
if [[ ! "$APP_PATH" == /* ]]; then
    APP_PATH="/$APP_PATH"
fi

# Ensure app_path ends with /
if [[ ! "$APP_PATH" == / ]]; then
    APP_PATH="${APP_PATH}/"
fi

echo -e "${GREEN}=== Secondary App Deployment Script ===${NC}"
echo "App Name: $APP_NAME"
echo "App Path: $APP_PATH"
echo "App Port: $APP_PORT"
echo "EC2 Host: $EC2_HOST"
echo ""

# Check if local files exist
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NGINX_CONF="$PROJECT_DIR/nginx.conf"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

if [ ! -f "$NGINX_CONF" ]; then
    echo -e "${RED}Error: nginx.conf not found at $NGINX_CONF${NC}"
    exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: docker-compose.yml not found at $COMPOSE_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}=== Step 1: nginx configuration snippet ===${NC}"
echo "Add this to nginx.conf inside the 'server' block, before the closing '}' :"
echo ""
cat <<EOF

    # --- $APP_NAME (deployed via deploy_secondary.sh) ---
    upstream $APP_NAME {
        server $APP_NAME:$APP_PORT;
    }

    location $APP_PATH {
        proxy_pass http://$APP_NAME/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header Authorization \$http_authorization;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
EOF

echo ""
echo -e "${YELLOW}=== Step 2: docker-compose.yml service snippet ===${NC}"
echo "Add this to docker-compose.yml under 'services:' :"
echo ""
cat <<EOF

  $APP_NAME:
    build:
      context: ../$APP_NAME
    expose:
      - "$APP_PORT"
    environment:
      - APP_NAME=$APP_NAME
      - APP_PATH=$APP_PATH
      - APP_PORT=$APP_PORT
    networks:
      - mcp-net
    volumes:
      - ${APP_NAME}-data:/app/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:$APP_PORT/health/')"]
      interval: 30s
      timeout: 5s
      retries: 3
EOF

echo ""
echo -e "${YELLOW}=== Step 3: Commands to run on EC2 ===${NC}"
echo ""
echo "After copying your app to ~/${APP_NAME}/ on EC2:"
echo ""
echo "  # Rebuild and restart ONLY this app (won't affect MCP)"
echo "  cd ~/peoplesoft_mcp"
echo "  sudo docker compose build $APP_NAME"
echo "  sudo docker compose up -d $APP_NAME"
echo ""
echo "  # Check status"
echo "  sudo docker compose ps $APP_NAME"
echo ""
echo "  # View logs"
echo "  sudo docker compose logs $APP_NAME --tail=50"
echo ""

echo -e "${YELLOW}=== Step 4: Push and deploy from local ===${NC}"
echo ""
echo "Run this from your local machine to deploy:"
echo ""
echo "  # Upload nginx config changes (coordinate with team)"
echo "  scp -i $PEM_FILE nginx.conf ec2-user@\${EC2_HOST}:~/peoplesoft_mcp/nginx.conf"
echo ""
echo "  # Reload nginx (non-disruptive)"
echo "  ssh -i $PEM_FILE ec2-user@\${EC2_HOST} \"sudo docker exec nginx-prod nginx -s reload\""
echo ""
echo "  # Upload and deploy your app"
echo "  rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \\"
echo "    -e \"ssh -i $PEM_FILE\" \\"
echo "    ~/path/to/${APP_NAME}/ \\"
echo "    ec2-user@\${EC2_HOST}:~/${APP_NAME}/"
echo ""
echo "  ssh -i $PEM_FILE ec2-user@\${EC2_HOST} \\"
echo "    \"cd ~/peoplesoft_mcp && sudo docker compose build $APP_NAME && sudo docker compose up -d $APP_NAME\""
echo ""

echo -e "${GREEN}=== Next Steps ===${NC}"
echo ""
echo "1. Copy your Django app code to EC2 at ~/${APP_NAME}/"
echo ""
echo "2. Add your app-specific environment variables to ~/.env on EC2"
echo ""
echo "3. Coordinate with the team to add nginx routing (nginx -s reload is non-disruptive)"
echo ""
echo "4. Deploy: sudo docker compose up -d $APP_NAME"
echo ""
echo -e "${GREEN}Your app will be available at: https://<host>${APP_PATH}${NC}"
