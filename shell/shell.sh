#!/bin/bash
#
# This script is the main login shell.
# It sets up environment and executes shell.py - that's where all the action
# is happenning. After this it attempts to attach to docker container.
# AFAIK this is safe, if user drops connection at any point everything will
# be cleaned and abandoned docker containers will be deleted.

. /etc/dockerized-shell-config.sh

###############################################################################

# This is block-file for new connections, useful, if you want to modify
# actual system code. Task modification uses more granular lock and is done
# by build.py
if [ -f "$HARD_LOCK_FILE" ] ; then
    while [ -f "$HARD_LOCK_FILE" ] ; do
        echo "Please wait, tasks are being updated..."
        sleep 3
    done
    # Restart shell
    exec "$0"
fi

###############################################################################

. "$SHELL_DST_DIR/shell_lib.sh"

# TASK_NAME is login in ssh
export TASK_NAME="$USER"
export TASK_TMP_DIR=""

function clean_exit {
    hide_output
    CONT_ID=$(<"$TASK_TMP_DIR/ContainerID")
    if [ ! -z "$CONT_ID" ] ; then # container launched
        # shell.py (or, to be exact, Dockerstart) could've created Dockerstop
        # file with special instructions for deleting container.
        # If it successfully executes - this script will not
        # delete the docker container.

        if [ -f "$TASK_TMP_DIR/Dockerstop" ] ; then
            with_stdout "$TASK_TMP_DIR/Dockerstop"
        else
            false # exits with error
        fi
        if [ $? -ne 0 ] ; then
            docker rm -f "$CONT_ID"
        fi
    fi
    # Finally - remove tmp dir
    if [ ! -z "$TASK_TMP_DIR" ] ; then
        rm -rf "$TASK_TMP_DIR"
    fi
    exit 0
}

trap 'clean_exit' SIGPIPE SIGQUIT SIGINT SIGHUP EXIT

# TASK_TMP_DIR is tmp dir for this connection/instance
export TASK_TMP_DIR=$(mktemp -d -p "$TMP_DIR" "$(date +%y%m%d.%H%M%S).$TASK_NAME.XXXXXXXXXX")
cd "$TASK_TMP_DIR"

# Execute main python script
with_stdout "$SHELL_DST_DIR/shell.py"
if [ $? -ne 0 ] ; then
    clean_exit
fi

# shell.py (or, to be exact, Dockerstart) should've created ContainerID
# file containing container id (duh)
CONT_ID=$(<"$TASK_TMP_DIR/ContainerID")
if [ -z "$CONT_ID" ] ; then # container failed to launch
    clean_exit
fi

# shell.py (or, to be exact, Dockerstart) can override standard TIMEOUT
# by specifying some other value (or turn it off with empty value)
if [ -f "$TASK_TMP_DIR/Timeout" ] ; then
    TIMEOUT=$(<"$TASK_TMP_DIR/Timeout")
fi

if [ -z "$TIMEOUT" ] ; then
    with_output docker attach "$CONT_ID"
else
    with_output timeout --foreground "$TIMEOUT" docker attach "$CONT_ID"
fi

clean_exit
