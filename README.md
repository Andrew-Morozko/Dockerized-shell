# Dockerized shell v2.0
System for creating fresh docker container for every ssh connection.

**WARNING**: Alpha version, do not use for production.

**WARNING**: Contains hardcoded passwords and private keys in `Dockerfile` and `rootfs/etc/ssh`.

## TODO:

* Add container server logic (create-attach) `main.py`
* Add container update logic (notify users about newer image versions / forcefully switch to newer container) `manage.py`
* Add pretty menues `main.py`
* Add logger between container and user and replay viewer `main.py`/`logger.py`
* Switch from threads to fun async framework (trio/curio). Right now `docker` package is syncronous, unfortunately

## Run:

1) Build server: `docker build . -t test`
2) Run server: `docker run -it -v /var/run/docker.sock:/var/run/docker.sock -p 2222:22 test`
3) Connect to shell: `ssh -p 2222 test@<server_ip>`


## Notes:

Uses platform specific networking code.

Works on:
* Debian 9 (stretch)
* alpine 3.8

Doesn't work on macOS.

