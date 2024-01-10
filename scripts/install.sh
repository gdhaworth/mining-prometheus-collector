#!/usr/bin/env bash

set -ex

NVIDIA_EXPORTER_VERSION='1.2.0'

if [[ "$(id -un)" == 'root' ]]; then
    echo 'Error: running as root, should run as normal user with sudo privileges'
    exit 1
fi

cd "$HOME"

if [[ ! -d "$HOME/.pyenv" ]]; then
    sudo env DEBIAN_FRONTEND=noninteractive apt-get update
    sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y \
            build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev \
            xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
    git clone https://github.com/pyenv/pyenv.git "$HOME/.pyenv"
fi

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
set +x
eval "$(pyenv init -)"
set -x

DESIRED_PYTHON="$(cat /opt/share/mining-prometheus-collector/.python-version)"
if ! pyenv versions | fgrep "$DESIRED_PYTHON" > /dev/null; then
    pyenv install "$DESIRED_PYTHON"
fi

cd /opt/share/mining-prometheus-collector
sudo git pull origin main

pip install --upgrade pip
pip install -r requirements.txt

WORKDIR="$(mktemp -d)"
trap 'rm -rf -- "$WORKDIR"' EXIT

cp etc/mining-collector.service "$WORKDIR"
REPLACE_PYTHON_BIN="$(pyenv which python)"
sed -ri 's|REPLACE_PYTHON_BIN|'"$REPLACE_PYTHON_BIN"'|' "$WORKDIR/mining-collector.service"
sudo cp "$WORKDIR/mining-collector.service" /etc/systemd/system

sudo cp etc/nvidia_gpu_exporter.service /etc/systemd/system
cd "$WORKDIR"
EXPORTER_TAR="nvidia_gpu_exporter_${NVIDIA_EXPORTER_VERSION}_linux_x86_64.tar.gz"
wget "https://github.com/utkuozdemir/nvidia_gpu_exporter/releases/download/v$NVIDIA_EXPORTER_VERSION/$EXPORTER_TAR"
tar xf $EXPORTER_TAR
sudo mv nvidia_gpu_exporter /usr/local/bin
sudo chown root:root /usr/local/bin/nvidia_gpu_exporter
if ! fgrep nvidia_gpu_exporter /etc/passwd > /dev/null; then
    sudo useradd -r -s /sbin/nologin -md /var/lib/nvidia_gpu_exporter nvidia_gpu_exporter
fi

sudo systemctl daemon-reload

sudo systemctl stop mining-collector.service || true
sudo systemctl enable mining-collector.service
sudo systemctl start mining-collector.service
sudo systemctl status mining-collector.service

sudo systemctl stop nvidia_gpu_exporter.service || true
sudo systemctl enable nvidia_gpu_exporter.service
sudo systemctl start nvidia_gpu_exporter.service
sudo systemctl status nvidia_gpu_exporter.service
