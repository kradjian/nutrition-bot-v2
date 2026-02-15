#!/bin/bash
# Production setup for Nutrition Bot v2

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🥗 Nutrition Bot v2 - Production Setup${NC}"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}⚠️  Please run as root (use sudo)${NC}"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip3 install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Get configuration
echo ""
echo -e "${YELLOW}🔑 Configuration${NC}"
echo "----------------"
read -rp "Enter Telegram Bot Token (from @BotFather): " BOT_TOKEN
read -rp "Enter OpenClaw Gateway Token: " GATEWAY_TOKEN

# Create environment file
cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
GATEWAY_TOKEN=$GATEWAY_TOKEN
EOF

chmod 600 .env
echo -e "${GREEN}✓ Environment saved to .env${NC}"

# Create systemd service
SERVICE_NAME="nutrition-bot-v2"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Nutrition Tracker Bot v2
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=/usr/local/bin:/usr/bin"
EnvironmentFile=$SCRIPT_DIR/.env
ExecStart=/usr/bin/python3 $SCRIPT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Systemd service created${NC}"

# Reload systemd and start service
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

echo ""
echo -e "${GREEN}✅ Nutrition Bot v2 is running!${NC}"
echo ""
echo "Commands:"
echo "  systemctl status $SERVICE_NAME  - Check status"
echo "  systemctl stop $SERVICE_NAME    - Stop bot"
echo "  systemctl start $SERVICE_NAME   - Start bot"
echo "  systemctl restart $SERVICE_NAME - Restart bot"
echo "  journalctl -u $SERVICE_NAME -f  - View logs"
