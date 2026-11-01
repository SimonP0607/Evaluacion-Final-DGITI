#!/bin/bash
exec > >(tee /var/log/user-data.log) 2>&1
set -x

dnf install -y git python3-pip
git clone --branch ${repo_branch} --depth 1 ${repo_url} ${app_dir}
python3 -m pip install -r ${app_dir}/app/requirements.txt

cat > /etc/webapp.env <<'ENVEOF'
DB_HOST="${db_host}"
DB_PORT="${db_port}"
DB_NAME="${db_name}"
DB_USER="${db_user}"
DB_PASSWORD="${db_password}"
APP_PORT="${app_port}"
ENVEOF
chmod 600 /etc/webapp.env

cat > /etc/systemd/system/webapp.service <<'UNITEOF'
[Unit]
Description=Agenda de contactos
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${app_dir}/app
EnvironmentFile=/etc/webapp.env
ExecStart=/usr/bin/python3 ${app_dir}/app/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNITEOF

systemctl daemon-reload
systemctl enable --now webapp
