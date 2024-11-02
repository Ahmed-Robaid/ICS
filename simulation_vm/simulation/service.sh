#!/bin/bash

# Define the service file path
SERVICE_FILE="/etc/systemd/system/simulation.service"
# Create the systemd service file
cat <<EOL > $SERVICE_FILE
[Unit]
Description=Start Simulation on Boot

[Service]
Type=forking
ExecStart=/bin/bash /home/$(logname)/ICS/simulation_vm/simulation/remote_io/modbus/run_all.sh

[Install]
WantedBy=multi-user.target
EOL

# Reload the systemd daemon to recognize the new service
systemctl daemon-reload

# Enable the service to start on boot
systemctl enable simulation.service
