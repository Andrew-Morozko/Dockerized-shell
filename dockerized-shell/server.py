import socket
import sys
import os
import signal
import array
import subprocess
from struct import Struct


# NOTE: docker run -tid for correct behaviour
CONTAINER_ID = '2f66'

SOCKET_ADDRESS = './unix_socket'
DOCKER = '/usr/bin/docker'
FDS_STRUCTURE = Struct('i' * 3)  # stdin, stdout, stderr
CREDS_STRUCTURE = Struct('i' * 3)  # pid, uid, gid
MAX_ENV_LEN = 4096  # Random big number
ANC_BUF_SIZE = (
    socket.CMSG_SPACE(FDS_STRUCTURE.size) +
    socket.CMSG_SPACE(CREDS_STRUCTURE.size)
)


def main():
    try:
        os.unlink(SOCKET_ADDRESS)
    except OSError:
        if os.path.exists(SOCKET_ADDRESS):
            raise

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)

    print(f'Creating socket {SOCKET_ADDRESS}')
    sock.bind(SOCKET_ADDRESS)

    # TODO: build multi-user server around here

    msg, ancdata, flags, addr = sock.recvmsg(MAX_ENV_LEN, ANC_BUF_SIZE)
    # msg - plain udp message
    # ancdata - creds and fds
    # flags - useless
    # addr - empty

    # parsing env from the msg
    env = {
        name: val
        for name, val in (
            name_val.split('=', maxsplit=1)
            for name_val in msg.decode('ascii').strip('\0').split('\0')
        )
    }
    # print(env)

    # Just to be safe
    stdin, stdout, stderr, pid, uid, gid = [None] * 6
    print(ancdata)

    # Parse ancdata
    for cmsg_level, cmsg_type, cmsg_data in ancdata:
        if cmsg_level == socket.SOL_SOCKET:
            if cmsg_type == socket.SCM_RIGHTS:
                stdin, stdout, stderr = FDS_STRUCTURE.unpack(cmsg_data)
            elif cmsg_type == socket.SCM_CREDENTIALS:
                pid, uid, gid = CREDS_STRUCTURE.unpack(cmsg_data)

    print('Got env, creds and fds from shell:')
    print(f'pid={pid}, uid={uid}, gid={gid}')
    print(f'stdin={stdin}, stdout={stdout}, stderr={stderr}')
    print(f'env["SOME_VAR"]={env.get("SOME_VAR")}')

    # Create python io objects around descriptors
    stdout_obj = os.fdopen(stdout, 'w')
    stdin_obj = os.fdopen(stdin, 'r')
    stderr_obj = os.fdopen(stderr, 'r')

    print('This came from server. Put some menues here\nCool? [yes/no]: ', file=stdout_obj, end='')
    usr_input = stdin_obj.readline().strip().lower()
    if usr_input == 'yes':
        print("That's what i'm talking about!", file=stdout_obj)
    else:
        print(":(", file=stdout_obj)

    print('Attaching shell to docker...')
    print('Attaching to docker:', file=stdout_obj)

    p = subprocess.Popen(
        [DOCKER, 'attach', CONTAINER_ID],
        stdin=stdin, stdout=stdout, stderr=stderr,
        env=env,
        start_new_session=False,
    )

    # start_new_session=True - ?? if there are bugs - change this, works ok now

    print('Waiting while container is working', flush=True)
    try:
        p.wait(20)  # wait() - to wait forever
    except subprocess.TimeoutExpired:
        print('Timeout')
        print('\r\nThis is from server again, timeout!\r', file=stdout_obj, flush=True)
    else:
        print('\r\nThis is from server again, you have logged out\r', file=stdout_obj, flush=True)
    finally:
        print('Work done')

        p.kill()  # kills subprocess of docker attach. TODO: Also kill container
        os.kill(pid, signal.SIGKILL)  # Kills shell in pause loop


if __name__ == '__main__':
    main()
