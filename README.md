# Dockerized shell v2.0
System for creating fresh docker container for every ssh connection.

Full rewrite in progress, prototype is ready (did not test as a login shell yet).

1) Build shell: `g++ -Wall shell.cpp -o shell`
2) Run server: `pyhton3 ./server.py`
3) Run shell: `./shell`

Uses platform specific code, works on Debian 9 (stretch), doesn't work on macOS.
