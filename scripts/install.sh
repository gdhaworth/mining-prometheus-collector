#!/usr/bin/env bash

set -ex

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
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
set +x
eval "$(pyenv init -)"
set -x

DESIRED_PYTHON="$(cat /opt/share/mining-prometheus-collector/.python-version)"
if ! pyenv versions | fgrep "$DESIRED_PYTHON" > /dev/null; then
    pyenv install "$DESIRED_PYTHON"
fi

cd /opt/share/mining-prometheus-collector

pip install --upgrade pip
pip install -r requirements.txt

cp etc/mining-collector.service "$HOME"
REPLACE_PYTHON_BIN="$(pyenv which python)"
sed -ri 's|REPLACE_PYTHON_BIN|'"$REPLACE_PYTHON_BIN"'|' "$HOME/mining-collector.service"
sudo cp "$HOME/mining-collector.service" /etc/systemd/system
rm "$HOME/mining-collector.service"
sudo systemctl daemon-reload
sudo systemctl enable --now mining-collector.service
sudo systemctl status mining-collector.service
