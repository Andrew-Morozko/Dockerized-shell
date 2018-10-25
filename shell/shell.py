#!/usr/bin/env python3.6
import shutil
import subprocess
from pathlib import Path
from os import environ as env
from contextlib import contextmanager

import lockfile


def die(message=None):
    if message:
        print(message, flush=True)
    exit(1)


@contextmanager
def chatty_lock(lock_file):
    lock = lockfile.Lock(lock_file)
    n = 0
    try:
        while True:
            try:
                lock.acquire(timeout=0.7)
                break
            except lockfile.Timeout:
                print(
                    f'Wait a second, tasks are being built'
                    f'{"."*n}{" "*(4-n)}',
                    flush=True,
                    end='\r',
                )
                n = (n + 1) % 4

        print(' ' * 80, flush=True, end='\r')
        yield

    finally:
        lock.release()


def main():
    try:
        TASKS_HOME = Path(env['TASKS_HOME'])
        TASK_NAME = env['TASK_NAME']
        TASK_TMP_DIR = Path(env['TASK_TMP_DIR'])
        IP = env['SSH_CONNECTION'].split(' ', maxsplit=1)[0]
    except KeyError:
        die('Failed to load environment variables')

    DOCKERSTART = TASKS_HOME / 'Dockerstarts' / TASK_NAME
    LOCK_FILE = TASKS_HOME / 'LockFile'
    CONTAINER_ID_FILE = TASK_TMP_DIR / 'ContainerID'

    # request to ip checker here

    with chatty_lock(LOCK_FILE):
        if not DOCKERSTART.exists():
            die("Task does not exist!")

        # Run dockerstart
        res = subprocess.run([
            str(DOCKERSTART),
            TASK_NAME,
            str(CONTAINER_ID_FILE)
        ])

    if res.returncode != 0:
        print(res)
        die('Failed to create container')


if __name__ == '__main__':
    main()
