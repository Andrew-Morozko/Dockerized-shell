#!/bin/bash
cd "$( dirname "${BASH_SOURCE[0]}" )"
. /etc/dockerized-shell-config.sh


if [ $# -eq 1 ] ; then
    PASSWORD="$1"
elif [ $# -eq 2 ] ; then
    PASSWORD="$2"
else
    cat <<EOF
Usage: $(basename "$0") USERNAME [PASSWORD]

Change USERNAME's password. Creates user if USERNAME doesn't exsist.
If PASSWORD wasn't supplied - PASSWORD is equal to USERNAME.

EOF
    exit 1
fi

USERNAME="$1"

id -u "$USERNAME" >/dev/null 2>&1
if [ $? -ne 0 ] ; then # create user
    sudo useradd -d "$TASKS_HOME" -g "$TASK_GROUP" -G docker -s "$DOCKER_SHELL" "$USERNAME" >/dev/null 2>&1
fi
sudo chpasswd <<<"$USERNAME:$PASSWORD" >/dev/null 2>&1

if [ ! -d "$PASSWORDS_DIR" ]; then
    mkdir -m 700 "$PASSWORDS_DIR"
fi

rm -f "$PASSWORDS_DIR/$USERNAME"
echo "$PASSWORD">"$PASSWORDS_DIR/$USERNAME"
chmod 400 "$PASSWORDS_DIR/$USERNAME"
