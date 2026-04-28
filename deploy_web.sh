#!/bin/bash

KEY="key-for-virginia.pem"
USER="ec2-user"

echo "=============================="
echo " EC2 WEB SERVER SETUP TOOL "
echo "=============================="

read -p "Enter EC2 Public IP: " IP

if [ ! -f "$KEY" ]; then
    echo "❌ Key file not found: $KEY"
    exit 1
fi

if [ ! -f "index.html" ]; then
    echo "❌ index.html not found in current folder"
    exit 1
fi

chmod 400 "$KEY"

echo "📂 Copying index.html to EC2..."
scp -o StrictHostKeyChecking=no -i "$KEY" index.html "$USER@$IP:/home/$USER/"

echo "⚙️ Configuring Web Server..."

ssh -o StrictHostKeyChecking=no -i "$KEY" "$USER@$IP" << EOF

sudo yum update -y
sudo yum install -y httpd

sudo systemctl start httpd
sudo systemctl enable httpd

sudo cp /home/$USER/index.html /var/www/html/

echo "Web server configured successfully"

EOF

echo ""
echo "✅ DONE!"
echo "🌐 Open in browser: http://$IP"
