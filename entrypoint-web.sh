#!/usr/bin/env bash
set -e

# Write the app's DB config file (the CPM-for-File target) from env on first boot.
# CPM-for-File rewrites the db_password= line in place on rotation, so we must NOT
# regenerate it once it exists.
mkdir -p /data
if [ ! -f /data/db-config.txt ]; then
  cat > /data/db-config.txt <<EOF
db_host=${DB_HOST}
db_port=${DB_PORT:-3306}
db_name=${DB_NAME:-customer_db}
db_user=${DB_USER:-app_user}
db_password=${DB_PASSWORD}
EOF
fi

# Start SSH, then run the web app in the foreground.
mkdir -p /run/sshd
/usr/sbin/sshd
exec python3 /app/app.py