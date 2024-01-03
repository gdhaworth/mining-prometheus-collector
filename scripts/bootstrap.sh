#!/usr/bin/env bash

set -ex

if ! which git > /dev/null 2>&1; then
    echo 'Error: No git found on PATH'
    exit 1
fi

if [[ -d /opt/share/mining-prometheus-collector ]]; then
    echo 'Error: Install directory already exists: /opt/share/mining-prometheus-collector'
    exit 2
fi

sudo mkdir -p /opt/share
sudo git clone https://github.com/gdhaworth/mining-prometheus-collector.git /opt/share/mining-prometheus-collector
cd /opt/share/mining-prometheus-collector
./scripts/install.sh
