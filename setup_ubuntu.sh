#!/bin/bash

# Update system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "Installing required packages..."
sudo apt install -y python3 python3-pip postgresql postgresql-contrib nginx

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install flask flask-login flask-sqlalchemy flask-wtf flask-babel gunicorn psycopg2-binary email-validator werkzeug routes pandas openpyxl xlsxwriter

# Setup PostgreSQL
echo "Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE USER vinatex WITH PASSWORD 'vinatex2024';"
sudo -u postgres psql -c "CREATE DATABASE vinatex OWNER vinatex;"

# Configure environment variables
echo "Configuring environment variables..."
cat > .env << EOL
DATABASE_URL=postgresql://vinatex:vinatex2024@localhost/vinatex
SESSION_SECRET=vinatex-report-portal-secret-$(openssl rand -hex 12)
FLASK_APP=main.py
FLASK_ENV=production
EOL

# Configure Nginx
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/vinatex << EOL
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://0.0.0.0:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOL

sudo ln -s /etc/nginx/sites-available/vinatex /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# Create systemd service
echo "Creating systemd service..."
APP_DIR=$(pwd)

sudo tee /etc/systemd/system/vinatex.service << EOL
[Unit]
Description=Vinatex Report Portal
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment="PATH=/usr/local/bin"
EnvironmentFile=${APP_DIR}/.env
ExecStart=/usr/local/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# Set correct permissions
echo "Setting permissions..."
mkdir -p instance
touch instance/vinatex.db
touch .env

chmod -R 755 .
chmod 660 .env
chmod 660 instance/vinatex.db
chmod 775 instance

# Start and enable service
echo "Starting service..."
sudo systemctl daemon-reload
sudo systemctl start vinatex
sudo systemctl enable vinatex

# Save accounts info
echo "Saving accounts information..."
cat > ./system_accounts.txt << EOL
System Accounts Information
=========================

Database:
- Host: localhost
- Database: vinatex
- Username: vinatex
- Password: vinatex@2024

Service Account:
- User: www-data
- Service: vinatex.service
- Port: 5000

Web Server:
- Nginx configuration: /etc/nginx/sites-available/vinatex
- Port: 80

Environment Variables:
- Location: $(pwd)/.env
EOL

echo "Setup completed! Check system_accounts.txt for important account information."