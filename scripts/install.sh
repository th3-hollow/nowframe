#!/bin/sh

set -eu

INSTALL_DIR="/opt/nowframe"
SERVICE_USER="nowframe"
SERVICE_HOME="/var/lib/nowframe"
ENV_FILE="/etc/nowframe.env"

SCRIPT_DIR="$(
    CDPATH= cd -- "$(dirname -- "$0")" &&
    pwd
)"

SOURCE_DIR="$(
    CDPATH= cd -- "${SCRIPT_DIR}/.." &&
    pwd
)"


if [ "$(id -u)" -ne 0 ]; then

    echo "Run this installer as root."
    exit 1

fi


echo "Installing operating-system dependencies..."

apt-get update

apt-get install -y \
    ca-certificates \
    fonts-dejavu-core \
    git \
    python3 \
    python3-pip \
    python3-venv \
    rsync


if ! id "${SERVICE_USER}" >/dev/null 2>&1; then

    echo "Creating service account..."

    useradd \
        --system \
        --create-home \
        --home-dir "${SERVICE_HOME}" \
        --shell /usr/sbin/nologin \
        --groups video \
        "${SERVICE_USER}"

else

    usermod \
        --append \
        --groups video \
        "${SERVICE_USER}"

fi


mkdir -p "${INSTALL_DIR}"

if [ "${SOURCE_DIR}" != "${INSTALL_DIR}" ]; then

    echo "Copying NowFrame to ${INSTALL_DIR}..."

    rsync -a \
        --exclude '.git/' \
        --exclude '.venv/' \
        --exclude '__pycache__/' \
        --exclude '*.pyc' \
        --exclude '*_test.png' \
        --exclude 'test_*.png' \
        --exclude '*_backup.py' \
        --exclude '*before*.py' \
        "${SOURCE_DIR}/" \
        "${INSTALL_DIR}/"

fi


chown -R \
    "${SERVICE_USER}:${SERVICE_USER}" \
    "${INSTALL_DIR}"


if [ ! -x "${INSTALL_DIR}/.venv/bin/python" ]; then

    echo "Creating Python virtual environment..."

    runuser \
        -u "${SERVICE_USER}" \
        -- \
        env HOME="${SERVICE_HOME}" \
        python3 -m venv \
        "${INSTALL_DIR}/.venv"

fi


echo "Installing Python dependencies..."

runuser \
    -u "${SERVICE_USER}" \
    -- \
    env HOME="${SERVICE_HOME}" \
    "${INSTALL_DIR}/.venv/bin/pip" \
    install \
    --requirement \
    "${INSTALL_DIR}/requirements.txt"


if [ ! -f "${ENV_FILE}" ]; then

    install \
        -o root \
        -g "${SERVICE_USER}" \
        -m 0640 \
        "${INSTALL_DIR}/nowframe.env.example" \
        "${ENV_FILE}"

    echo "Created ${ENV_FILE}"
    echo "Add your Spotify credentials before authorization."

else

    echo "Keeping existing ${ENV_FILE}"

fi


install \
    -o root \
    -g root \
    -m 0644 \
    "${INSTALL_DIR}/packaging/systemd/nowframe.service" \
    /etc/systemd/system/nowframe.service


systemctl daemon-reload


echo
echo "NowFrame installation complete."
echo
echo "Next steps:"
echo "  1. Edit ${ENV_FILE}"
echo "  2. Authorize Spotify"
echo "  3. Enable and start nowframe.service"
