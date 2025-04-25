
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
sudo -u postgres psql -c "CREATE USER vinatex WITH PASSWORD 'vinatex@2024';"
sudo -u postgres psql -c "CREATE DATABASE vinatex OWNER vinatex;"

# Configure environment variables
echo "Configuring environment variables..."
cat > .env << EOL
DATABASE_URL=postgresql://vinatex:vinatex@2024@localhost/vinatex
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
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOL

sudo ln -s /etc/nginx/sites-available/vinatex /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/vinatex.service << EOL
[Unit]
Description=Vinatex Report Portal
After=network.target

[Service]
User=www-data
WorkingDirectory=$(pwd)
Environment="PATH=/usr/local/bin"
EnvironmentFile=$(pwd)/.env
ExecStart=/usr/local/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 main:app

[Install]
WantedBy=multi-user.target
EOL

# Set permissions
echo "Setting permissions..."
sudo chown -R www-data:www-data .
sudo chmod -R 755 .

# Start and enable service
echo "Starting service..."
sudo systemctl daemon-reload
sudo systemctl start vinatex
sudo systemctl enable vinatex

# Save accounts info
echo "Saving accounts information..."
cat > system_accounts.txt << EOL
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
