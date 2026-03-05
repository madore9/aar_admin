#!/bin/bash
#
# Full deployment script for secondary Docker containers on EC2
# This script updates nginx.conf and docker-compose.yml automatically
#
# Usage:
#   ./deploy_secondary_full.sh <app-name> <app-path> [port]
#
# Example: ./deploy_secondary_full.sh myadmin /admin 8000

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Config
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
    exit 1
}

# Validate
if [ -z "$APP_NAME" ] || [ -z "$APP_PATH" ]; then
    usage
fi

# Sanitize
if ! [[ "$APP_NAME" =~ ^[a-zA-Z][a-zA-Z0-9-]*$ ]]; then
    echo -e "${RED}Error: App name must start with a letter and contain only alphanumeric and hyphens${NC}"
    exit 1
fi

[[ ! "$APP_PATH" == /* ]] && APP_PATH="/$APP_PATH"
[[ ! "$APP_PATH" == / ]] && APP_PATH="${APP_PATH}/"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NGINX_CONF="$PROJECT_DIR/nginx.conf"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Secondary App Deployment${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "App Name: $APP_NAME"
echo "App Path: $APP_PATH"
echo "App Port: $APP_PORT"
echo ""

# Check files exist
[ ! -f "$NGINX_CONF" ] && echo -e "${RED}Error: nginx.conf not found${NC}" && exit 1
[ ! -f "$COMPOSE_FILE" ] && echo -e "${RED}Error: docker-compose.yml not found${NC}" && exit 1

# Check if already deployed
if grep -q "upstream $APP_NAME {" "$NGINX_CONF" 2>/dev/null; then
    echo -e "${YELLOW}Warning: $APP_NAME already exists in nginx.conf${NC}"
    read -p "Update existing? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Generate nginx upstream config
NGINX_UPSTREAM="
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
    }"

# Generate compose service
COMPOSE_SERVICE="
  $APP_NAME:
    build:
      context: ../$APP_NAME
    expose:
      - \"$APP_PORT\"
    environment:
      - APP_NAME=$APP_NAME
      - APP_PATH=$APP_PATH
      - APP_HOST=0.0.0.0
      - APP_PORT=$APP_PORT
    networks:
      - mcp-net
    volumes:
      - ${APP_NAME}-data:/app/data
    healthcheck:
      test: [\"CMD\", \"python\", \"-c\", \"import urllib.request; urllib.request.urlopen('http://localhost:$APP_PORT/health/')\"]
      interval: 30s
      timeout: 5s
      retries: 3"

echo -e "${YELLOW}[1/4] Updating nginx.conf...${NC}"

# Add nginx upstream before the closing server brace
sed -i.bak "s/^}$/$NGINX_UPSTREAM\n}/" "$NGINX_CONF"
echo "  Added upstream + location block for $APP_PATH"

echo -e "${YELLOW}[2/4] Updating docker-compose.yml...${NC}"

# Add service to compose file (before networks section)
sed -i.bak "s/^networks:/$COMPOSE_SERVICE\n\nnetworks:/" "$COMPOSE_FILE"
echo "  Added service: $APP_NAME"

echo -e "${YELLOW}[3/4] Backing up original files...${NC}"
if [ -f "$NGINX_CONF.bak" ]; then
    mv "$NGINX_CONF.bak" "$NGINX_CONF.backup.$(date +%Y%m%d%H%M%S)"
fi
if [ -f "$COMPOSE_FILE.bak" ]; then
    mv "$COMPOSE_FILE.bak" "$COMPOSE_FILE.backup.$(date +%Y%m%d%H%M%S)"
fi
echo "  Backups created"

echo -e "${YELLOW}[4/4] Generating deployment helper script...${NC}"

# Generate deployment script for the app
DEPLOY_SCRIPT="$PROJECT_DIR/deploy_${APP_NAME}.sh"
cat > "$DEPLOY_SCRIPT" <<DEPLOYSCRIPT
#!/bin/bash
# Deployment script for $APP_NAME
# Run from your local machine

set -e

APP_NAME="$APP_NAME"
APP_PATH="$APP_PATH"
APP_PORT="$APP_PORT"
EC2_HOST="${EC2_HOST:-10.138.149.157}"
PEM_FILE="${PEM_FILE:-myharvard-dev-mcp.pem}"

echo "Deploying $APP_NAME to EC2..."

# 1. Sync app code
echo "Syncing $APP_NAME to EC2..."
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' \\
    -e "ssh -i $PEM_FILE" \\
    ~/path/to/$APP_NAME/ \\
    ec2-user@$EC2_HOST:/home/ec2-user/$APP_NAME/

# 2. Build and start container
echo "Building and starting $APP_NAME..."
ssh -i $PEM_FILE ec2-user@$EC2_HOST << 'EOF'
    cd ~/peoplesoft_mcp
    sudo docker compose build $APP_NAME
    sudo docker compose up -d $APP_NAME
    echo "Container status:"
    sudo docker compose ps $APP_NAME
EOF

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
echo "App URL: https://<your-host>$APP_PATH"
echo ""
echo "To view logs:"
echo "  ssh -i $PEM_FILE ec2-user@$EC2_HOST 'sudo docker compose logs $APP_NAME --tail=50'"
DEPLOYSCRIPT

chmod +x "$DEPLOY_SCRIPT"
echo "  Created: deploy_${APP_NAME}.sh"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Configuration Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Updated files:"
echo "  - nginx.conf (added $APP_NAME upstream)"
echo "  - docker-compose.yml (added $APP_NAME service)"
echo "  - deploy_${APP_NAME}.sh (deployment helper)"
echo ""
echo "Next steps:"
echo ""
echo "1. Add your app code to ~/peoplesoft_mcp/../$APP_NAME/ on EC2"
echo ""
echo "2. Deploy to EC2:"
echo "   ./deploy_${APP_NAME}.sh"
echo ""
echo "   Or manually:"
echo "   ssh -i $PEM_FILE ec2-user@$EC2_HOST"
echo "   cd ~/peoplesoft_mcp"
echo "   sudo docker compose build $APP_NAME"
echo "   sudo docker compose up -d $APP_NAME"
echo ""
echo "3. Your app will be at: https://<host>$APP_PATH"
echo ""
echo -e "${YELLOW}NOTE: nginx config changes require a reload on EC2:${NC}"
echo "   sudo docker exec nginx-prod nginx -s reload"
echo ""
