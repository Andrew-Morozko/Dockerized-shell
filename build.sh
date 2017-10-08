#!/bin/bash
. /etc/dockerized-shell-config.sh
cd "$( dirname "${BASH_SOURCE[0]}" )"

python3.6 ./build/build.py
