#!/bin/bash
apt-get update
apt-get upgrade -y
apt-get install apache2 -y
echo "<html><body><h1>Welcome</h1>" > /var/www/index.html
echo "I was generated from user-data and cloud-init" >> /var/www/index.html
echo "</body></html>" >> /var/www/index.html
