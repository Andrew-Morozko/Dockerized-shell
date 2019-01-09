#!/bin/sh

# do not detach (-D), log to stderr (-e), passthrough other arguments
# /usr/sbin/sshd -D -e "$@"
/usr/sbin/sshd
cd /server/
pipenv run python3 main.py
