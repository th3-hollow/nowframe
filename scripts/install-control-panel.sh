#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this installer as root." >&2
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

state_dir="${NOWFRAME_CONTROL_STATE_DIR:-/var/lib/nowframe-control}"
usage_dir="${NOWFRAME_USAGE_DIR:-/var/lib/nowframe}"
settings_dir="${NOWFRAME_SETTINGS_DIR:-/etc/nowframe}"

service_user="${NOWFRAME_CONTROL_USER:-nowframe-control}"
service_group="$service_user"

spotify_env_source="${NOWFRAME_SPOTIFY_ENV_SOURCE:-/root/.nowframe_env}"
spotify_cache_source="${NOWFRAME_SPOTIFY_CACHE_SOURCE:-/root/.nowframe_spotify_cache}"
old_usage_source="${NOWFRAME_USAGE_SOURCE:-/root/.local/state/nowframe/spotify_api_usage.csv}"

required_files="
control_core.py
control_panel.py
control_server.py
requirements-control.txt
packaging/control.env.example
packaging/systemd/nowframe-control.service
packaging/systemd/nowframe-usage.conf
packaging/helpers/nowframe-control-helper
packaging/sudoers/nowframe-control
"

for relative_path in $required_files; do
    if [ ! -f "$source_dir/$relative_path" ]; then
        echo "Missing required file: $relative_path" >&2
        exit 1
    fi
done

if [ ! -f "$spotify_env_source" ]; then
    echo "Spotify environment file not found: $spotify_env_source" >&2
    exit 1
fi

if [ ! -f "$spotify_cache_source" ]; then
    echo "Spotify token cache not found: $spotify_cache_source" >&2
    exit 1
fi

if ! getent passwd "$service_user" >/dev/null; then
    useradd \
        --system \
        --home-dir "$state_dir" \
        --create-home \
        --shell /usr/sbin/nologin \
        "$service_user"
fi

install -d \
    -m 755 \
    -o root \
    -g root \
    "$app_root" \
    "$app_dir" \
    "$app_dir/templates" \
    "$app_dir/static"

install \
    -m 644 \
    -o root \
    -g root \
    "$source_dir/control_core.py" \
    "$source_dir/control_panel.py" \
    "$source_dir/control_server.py" \
    "$app_dir/"

cp -a \
    "$source_dir/templates/." \
    "$app_dir/templates/"

cp -a \
    "$source_dir/static/." \
    "$app_dir/static/"

chown -R root:root "$app_dir"

find "$app_dir" \
    -type d \
    -exec chmod 755 {} \;

find "$app_dir" \
    -type f \
    -exec chmod 644 {} \;

if [ ! -x "$venv_dir/bin/python" ]; then
    /usr/bin/python3 -m venv "$venv_dir"
fi

"$venv_dir/bin/python" \
    -m pip install \
    --upgrade pip

"$venv_dir/bin/python" \
    -m pip install \
    -r "$source_dir/requirements-control.txt"

chown -R root:root "$venv_dir"

install -d \
    -m 2770 \
    -o root \
    -g "$service_group" \
    "$settings_dir"

install -d \
    -m 750 \
    -o "$service_user" \
    -g "$service_group" \
    "$state_dir"

install -d \
    -m 750 \
    -o root \
    -g "$service_group" \
    "$usage_dir"

if [ ! -f "$settings_dir/control.env" ]; then
    install \
        -m 660 \
        -o root \
        -g "$service_group" \
        "$source_dir/packaging/control.env.example" \
        "$settings_dir/control.env"
fi

if [ ! -f "$settings_dir/devices.json" ]; then
    printf '[]\n' >"$settings_dir/devices.json"
fi

chown \
    root:"$service_group" \
    "$settings_dir/control.env" \
    "$settings_dir/devices.json"

chmod 660 \
    "$settings_dir/control.env" \
    "$settings_dir/devices.json"

install \
    -m 640 \
    -o root \
    -g "$service_group" \
    "$spotify_env_source" \
    "$settings_dir/spotify.env"

install \
    -m 600 \
    -o "$service_user" \
    -g "$service_group" \
    "$spotify_cache_source" \
    "$state_dir/spotify-cache"

if [ ! -f "$usage_dir/spotify_api_usage.csv" ]; then
    if [ -f "$old_usage_source" ]; then
        install \
            -m 640 \
            -o root \
            -g "$service_group" \
            "$old_usage_source" \
            "$usage_dir/spotify_api_usage.csv"
    else
        install \
            -m 640 \
            -o root \
            -g "$service_group" \
            /dev/null \
            "$usage_dir/spotify_api_usage.csv"
    fi
fi

install \
    -m 750 \
    -o root \
    -g root \
    "$source_dir/packaging/helpers/nowframe-control-helper" \
    /usr/local/sbin/nowframe-control-helper

install \
    -m 440 \
    -o root \
    -g root \
    "$source_dir/packaging/sudoers/nowframe-control" \
    /etc/sudoers.d/nowframe-control

visudo -cf /etc/sudoers.d/nowframe-control

install \
    -m 644 \
    -o root \
    -g root \
    "$source_dir/packaging/systemd/nowframe-control.service" \
    /etc/systemd/system/nowframe-control.service

install -d \
    -m 755 \
    -o root \
    -g root \
    /etc/systemd/system/nowframe.service.d

install \
    -m 644 \
    -o root \
    -g root \
    "$source_dir/packaging/systemd/nowframe-usage.conf" \
    /etc/systemd/system/nowframe.service.d/usage.conf

systemd-analyze verify \
    /etc/systemd/system/nowframe-control.service

systemctl daemon-reload
systemctl enable nowframe-control.service
systemctl restart nowframe-control.service

echo
echo "NowFrame Control installed."
echo "Open: http://nowframe.local:8080/status"
