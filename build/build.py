#!/usr/bin/env python3.6
import os
import re
import shutil
import subprocess
from time import sleep
from pathlib import Path
from tempfile import mkdtemp
from os import environ as env
from contextlib import contextmanager, suppress

import lockfile
import docker as dockerlib
docker = dockerlib.from_env()

tasks = {}
failed_to_build = []


def list_dir(cur_dir: Path):
    dirs = []
    files = []
    for item in sorted(cur_dir.iterdir()):
        if item.is_file():
            files.append(item)
        elif item.is_dir():
            dirs.append(item)
    return dirs, files


def build_image(path, tag_now=False):
    name = path.name

    build_args = {
        'decode': True,
        'path': str(path)
    }

    if tag_now:
        build_args['tag'] = name

    log = docker.api.build(
        **build_args
    )

    print(f'*** Building: {name}')

    image = False

    for line in log:
        with suppress(KeyError):
            print(line['stream'], end='')
        with suppress(KeyError):
            image = docker.images.get(line['aux']['ID'])

    if image:
        print('*** Build succeeded')
    else:
        print('*** Build failed')

    return name, image


def support_spider(cur_dir: Path):
    dirs, files = list_dir(cur_dir)
    for file in files:
        if file.name == 'Dockerfile':
            name, res = build_image(cur_dir, tag_now=True)
            if not res:
                failed_to_build.append(name)
            return

    for subdir in dirs:
        support_spider(subdir)


def task_spider(cur_dir: Path, dockerstart=None):
    task_name = None
    dirs, files = list_dir(cur_dir)

    for file in files:
        if file.name == 'Dockerfile':
            task_name = cur_dir.name
            if task_name in tasks:
                raise Exception(f'Two tasks share the same name: {task_name}')
        elif file.name == 'Dockerstart':
            dockerstart = file

    if task_name is None:
        # going deeper, untill we hit task or run out of dirs
        for subdir in dirs:
            task_spider(subdir, dockerstart)
    else: # found task
        if dockerstart is None:
            raise Exception(f"Can't determine Dockerstart for {task_name}")

        name, hsh = build_image(cur_dir)
        if not hsh:
            failed_to_build.append(name)
        else:
            tasks[name] = hsh
            os.link(dockerstart, DOCKERSTARTS_TMP_DIR / task_name)

        return


def own_files(*files, perm='750', recursive=True, owner=None, group=None):
    if owner is None:
        owner = ADMIN_USER
    if group is None:
        group = TASK_GROUP
    files = list(map(str, files))

    own_args = ['sudo', 'chown']
    mod_args = ['sudo', 'chmod']

    if recursive:
        own_args.append('-R')
        mod_args.append('-R')

    own_args.append(f'{owner}:{group}')
    own_args.extend(files)
    subprocess.run(own_args)

    mod_args.append(perm)
    mod_args.extend(files)
    subprocess.run(mod_args)


def executables_changed():
    return subprocess.run(
        ['diff', '-r', str(SHELL_SRC_DIR), str(SHELL_DST_DIR)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ).returncode != 0


def replace(src, dst):
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)


@contextmanager
def lock():
    if executables_changed():
        print('*** Acquired big lock (executables have changed)')
        lock_file = HARD_LOCK_FILE
        try:
            lock_file.touch(0o600)
            sleep(1)
            replace(SHELL_SRC_DIR, SHELL_DST_DIR)
            yield
        finally:
            lock_file.unlink()
            print('*** Released big lock')
    else:
        print('*** Acquired normal lock')
        lock_file = lockfile.Lock(LOCK_FILE)
        try:
            while True:
                try:
                    lock_file.acquire(exclusive=True, timeout=0.7)
                    break
                except lockfile.Timeout:
                    print('*** Wait a second, someone is loading task...')
            yield
        finally:
            lock_file.release()
            print('*** Released normal lock')


def main():
    support_spider(SUPPORT_SRC_DIR)
    task_spider(TASKS_SRC_DIR)
    if failed_to_build:
        print('*** Some images failed to build:')
        print('\n'.join(failed_to_build))
    else:
        print('*** All images sussesfully built!')

    with lock():
        # Apply tags
        for task_name, image in tasks.items():
            image.tag(task_name, force=True)

        replace(DOCKERSTARTS_TMP_DIR, DOCKERSTARTS_DST_DIR)

        own_files(TASKS_HOME)
        own_files(
            LOCK_FILE,
            TASKS_HOME / 'tmp',
            perm='770'
        )

    print('*** Docker Cleanup...')
    # This cleaner removes intermediate cache for all tasks probably
    # due to them being re-tagged and "torn away" from their stacks.
    # TODO: write something nicer
    # subprocess.run(
    #     'docker rmi $(docker images -q --no-trunc --filter "dangling=true")',
    #     shell=True,
    #     stdout=subprocess.DEVNULL,
    #     stderr=subprocess.DEVNULL
    # )
    subprocess.run(
        'docker rm $(docker ps -qa --no-trunc --filter "status=exited")',
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


if __name__ == '__main__':
    ADMIN_USER = env['ADMIN_USER']
    TASK_GROUP = env['TASK_GROUP']

    TASKS_HOME = Path(env['TASKS_HOME'])

    TASKS_SRC_DIR = Path(env['TASKS_SRC_DIR'])
    SHELL_SRC_DIR = Path(env['SHELL_SRC_DIR'])
    HARD_LOCK_FILE = Path(env['HARD_LOCK_FILE'])
    SUPPORT_SRC_DIR = Path(env['SUPPORT_SRC_DIR'])

    LOCK_FILE = Path(env['LOCK_FILE'])
    SHELL_DST_DIR = Path(env['SHELL_DST_DIR'])
    DOCKERSTARTS_DST_DIR = Path(env['DOCKERSTARTS_DST_DIR'])

    DOCKERSTARTS_TMP_DIR = None
    try:
        DOCKERSTARTS_TMP_DIR = Path(
            mkdtemp(
                dir=str(TASKS_HOME),
                prefix='Dockerstarts_Tmp_'
            )
        )
        main()
    finally:
        if DOCKERSTARTS_TMP_DIR:
            shutil.rmtree(DOCKERSTARTS_TMP_DIR, ignore_errors=True)
