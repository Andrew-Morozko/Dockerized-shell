# Dockerized shell
System for creating fresh docker container for every ssh connection.

Currently operational, but quite admin-hostile, working on it...

## Main files
* `shell/shell.sh` - login shell, setup, signal handling, cleanup
* `shell/shell.py` - high level logic, launch of Dockerstart file
* `mod_user.sh` - script for creating/changing passwords for task-users
* `/etc/dockerized-shell-config.sh` - config file

## Tutorial
### Prerequisites
Install docker, python3.6 and python package "docker". This tutorial is for debian, but this should work with most linuxes.

### Setup
1. Change `config.sh` to your liking and move it to `/etc/dockerized-shell-config.sh`, source it:
```bash
mv ./config.sh /etc/dockerized-shell-config.sh
. /etc/dockerized-shell-config.sh
```
2. Launch `install.sh` s
3. Add `$DOCKER_SHELL` to `/etc/shells`: `echo "$DOCKER_SHELL" >> /etc/shells`
4. Add to `/etc/ssh/sshd_config`:
```
Match Group <name of your $TASK_GROUP here>
    PasswordAuthentication yes
```
5. Reload sshd:
```bash
/usr/sbin/sshd -t # test config is OK (empty output = OK)
systemctl reload sshd
```
6. Create test users, for example:
```bash
for i in `seq 0 11`; do
    ./mod_user.sh "task$i";
done
```
7. Build tasks: `./build.sh`

### Usage
Tasks are located in `$TASKS_SRC_DIR`, and are comprised of arbitrary directory structure. `Dockerstart` file determines, how tasks (docker containers) are launched. It affects current directory and all its subdirectories. You can override higher-level `Dockerstart` file by creating another `Dockerstart` file in some subdirectory.

`Dockerstart` file receives name of the image as first argument  and path to `ContainerID` file as a second argument. Result of `Dockerstart`s execution - running container id - must be written to `ContainerID` file.

You can rebuild the tasks at any time without disrupting clients. All new clients will be connected to new container images, no old clients will be affected in any way.
