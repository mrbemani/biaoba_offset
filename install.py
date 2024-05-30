# install script

import sys
import os

if getattr(sys, 'frozen', False):
    APP_BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
elif __file__:
    APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HOME = os.environ.get("HOME", "/root")
USER = os.environ.get("USER", "root")

PYTHON_BIN = "/usr/bin/python3"

os.chdir(APP_BASE_DIR)

# install apt packages
os.system("apt-get update")
os.system("apt-get install -y python3 python3-pip python3-opencv build-essential libssl-dev libffi-dev python3-dev")
os.system(f"pip3 install -r {APP_BASE_DIR}/requirements.txt")

# create start.sh script
start_sh_content = f"""#!/bin/bash
cd {APP_BASE_DIR}
{PYTHON_BIN} {APP_BASE_DIR}/server.py
"""

with open(f"{APP_BASE_DIR}/start.sh", "w") as f:
    f.write(start_sh_content)

# add execution permission to start.sh
os.system(f"chmod +x {APP_BASE_DIR}/start.sh")

# setup service
service_name = "biaoba"
service_file = f"/etc/systemd/system/{service_name.lower()}.service"
service_file_content = f"""[Unit]
Description=
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart={APP_BASE_DIR}/start.sh
WorkingDirectory={APP_BASE_DIR}
Restart=on-failure
# Setup environment if needed
Environment="HOME={HOME}" "USER={USER}"

[Install]
WantedBy=multi-user.target
"""

with open(service_file, "w") as f:
    f.write(service_file_content)

os.system(f"chmod 644 {service_file}")
os.system(f"systemctl daemon-reload")
os.system(f"systemctl enable {service_name.lower()}.service")
os.system(f"systemctl start {service_name.lower()}.service")
os.system(f"systemctl status {service_name.lower()}.service")

