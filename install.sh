#!/bin/bash
. /etc/dockerized-shell-config.sh
cd "$( dirname "${BASH_SOURCE[0]}" )"

usermod -a -G docker "$ADMIN_USER"
groupadd "$TASK_GROUP"
mkdir "$TASKS_HOME"
touch "$TASKS_HOME/.hushlogin"
touch "$LOCK_FILE"

chown "$ADMIN_USER:$TASK_GROUP" "$TASKS_HOME"

mkdir "$TMP_DIR"
echo "tmpfs $TMP_DIR tmpfs rw,nosuid,nodev,relatime,mode=770,uid=$ADMIN_USER,gid=$TASK_GROUP,size=100m 0 0" >>/etc/fstab
mount -a

mv ./build/lockfile.py /usr/local/lib/python3.6/

ln -s "$SHELL_DST_DIR/shell.sh" "$DOCKER_SHELL"
