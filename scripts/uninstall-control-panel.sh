#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this uninstaller as root." >&2
    exit 1
fi

app_root="${NOWFRAME_CONTROL_INSTALL_DIR:-/opt/nowframe-control}"
state_dir="${NOWFRAME_CONTROL_STATE_DIR:-/var/lib/nowframe-control}"
usage_dir="${NOWFRAME_USAGE_DIR:-/var/lib/nowframe}"
settings_dir="${NOWFRAME_SETTINGS_DIR:-/etc/nowframe}"
service_user="${NOWFRAME_CONTROL_USER:-nowframe-control}"

systemctl disable \
    --now \
    nowframe-control.service \
    2>/dev/null \
    || true

rm -f \
    /etc/systemd/system/nowframe-control.service \
    /etc/systemd/system/nowframe.service.d/usage.conf \
    /etc/sudoers.d/nowframe-control \
    /usr/local/sbin/nowframe-control-helper

for dropin in \
    server.conf \
    spotify.conf \
    zz-production.conf
do
    rm -f \
        "/etc/systemd/system/nowframe-control.service.d/$dropin"
done

rmdir \
    /etc/systemd/system/nowframe-control.service.d \
    2>/dev/null \
    || true

systemctl daemon-reload
systemctl reset-failed \
    nowframe-control.service \
    2>/dev/null \
    || true

if [ -d "$app_root" ]; then
    rm -rf -- "$app_root"
fi

if [ "${PURGE:-0}" = "1" ]; then
    rm -rf -- \
        "$state_dir" \
        "$usage_dir"

    rm -f \
        "$settings_dir/control.env" \
        "$settings_dir/devices.json" \
        "$settings_dir/spotify.env"

    rmdir \
        "$settings_dir" \
        2>/dev/null \
        || true

    if getent passwd "$service_user" >/dev/null; then
        userdel "$service_user"
    fi

    echo "NowFrame Control and its saved data were removed."
else
    echo "NowFrame Control was removed."
    echo "Settings and statistics were preserved."
    echo "Run with PURGE=1 only if saved data should also be removed."
fi
