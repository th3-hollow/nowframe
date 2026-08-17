#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this updater as root." >&2
    exit 1
fi

script_dir="$(
    CDPATH= cd -- "$(dirname -- "$0")" &&
    pwd
)"

source_dir="$(
    CDPATH= cd -- "$script_dir/.." &&
    pwd
)"

app_root="${NOWFRAME_CONTROL_INSTALL_DIR:-/opt/nowframe-control}"
app_dir="$app_root/app"
venv_dir="$app_root/venv"
release_dir="$app_root/releases"

stamp="$(date +%Y%m%d-%H%M%S)"
candidate="$release_dir/candidate-$stamp"
previous="$release_dir/previous-$stamp"
failed="$release_dir/failed-$stamp"

if [ ! -x "$venv_dir/bin/python" ]; then
    echo "Control-panel virtual environment is missing." >&2
    echo "Run install-control-panel.sh first." >&2
    exit 1
fi

install -d \
    -m 755 \
    -o root \
    -g root \
    "$release_dir" \
    "$candidate" \
    "$candidate/templates" \
    "$candidate/static"

install \
    -m 644 \
    -o root \
    -g root \
    "$source_dir/control_auth.py" \
    "$source_dir/control_core.py" \
    "$source_dir/control_oauth.py" \
    "$source_dir/control_panel.py" \
    "$source_dir/control_secrets.py" \
    "$source_dir/control_server.py" \
    "$source_dir/control_setup.py" \
    "$candidate/"

cp -a \
    "$source_dir/templates/." \
    "$candidate/templates/"

cp -a \
    "$source_dir/static/." \
    "$candidate/static/"

chown -R root:root "$candidate"

find "$candidate" \
    -type d \
    -exec chmod 755 {} \;

find "$candidate" \
    -type f \
    -exec chmod 644 {} \;

"$venv_dir/bin/python" \
    -m pip install \
    -r "$source_dir/requirements-control.txt"

PYTHONPATH="$candidate" \
NOWFRAME_CONTROL_RESTART=0 \
"$venv_dir/bin/python" \
    -m py_compile \
    "$candidate/control_core.py" \
    "$candidate/control_panel.py" \
    "$candidate/control_server.py"

sh -n     "$source_dir/packaging/helpers/nowframe-control-helper"

visudo -cf     "$source_dir/packaging/sudoers/nowframe-control"

systemd-analyze verify     "$source_dir/packaging/systemd/nowframe-control.service"

install     -m 750     -o root     -g root     "$source_dir/packaging/helpers/nowframe-control-helper"     /usr/local/sbin/nowframe-control-helper

install     -m 440     -o root     -g root     "$source_dir/packaging/sudoers/nowframe-control"     /etc/sudoers.d/nowframe-control

install     -m 644     -o root     -g root     "$source_dir/packaging/systemd/nowframe-control.service"     /etc/systemd/system/nowframe-control.service

install -d     -m 755     -o root     -g root     /etc/systemd/system/nowframe.service.d

install     -m 644     -o root     -g root     "$source_dir/packaging/systemd/nowframe-spotify.conf"     /etc/systemd/system/nowframe.service.d/spotify.conf

install     -m 644     -o root     -g root     "$source_dir/packaging/systemd/nowframe-usage.conf"     /etc/systemd/system/nowframe.service.d/usage.conf

systemctl daemon-reload

if [ -d "$app_dir" ]; then
    mv "$app_dir" "$previous"
fi

mv "$candidate" "$app_dir"

systemctl restart nowframe-control.service

attempts=0

while [ "$attempts" -lt 20 ]; do
    if curl \
        --fail \
        --silent \
        --output /dev/null \
        http://127.0.0.1:8080/status
    then
        echo
        echo "NowFrame Control updated successfully."
        echo "Previous release: $previous"
        exit 0
    fi

    attempts=$((attempts + 1))
    sleep 0.5
done

echo "Updated panel failed its health check; rolling back." >&2

systemctl stop nowframe-control.service

mv "$app_dir" "$failed"

if [ -d "$previous" ]; then
    mv "$previous" "$app_dir"
fi

systemctl start nowframe-control.service

echo "Previous application restored." >&2
echo "Failed candidate retained at: $failed" >&2
exit 1
