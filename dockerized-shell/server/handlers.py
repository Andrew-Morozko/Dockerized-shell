"""I/O and concurrency dependant code"""

import os
import shutil
import socket
import signal
from threading import Thread
from itertools import count
from contextlib import contextmanager


import parser


@contextmanager
def server_socket(addr, mode, user, group):
    """Creates and configures server socket.

    Includes potentially blocking unlink and os.path.exists.
    """
    try:
        os.unlink(addr)
    except OSError as e:
        if os.path.exists(addr):
            raise RuntimeError('Failed to create socket') from e

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    sock.bind(addr)
    shutil.chown(addr, user, group)
    os.chmod(addr, mode)

    try:
        yield sock
    finally:
        try:
            os.unlink(addr)
        except OSError:
            pass


_connection_no = count()


class ThreadedHandler(Thread):
    """Represents syncronous, thread-based handler"""

    def __init__(self, data, ancdata):
        creds, fds = parser.parse_ancdata(ancdata)

        # sets pid, uid, gid
        self.__dict__.update(creds._asdict())

        self.stdin = os.fdopen(fds.stdin, 'r')
        self.stdout = os.fdopen(fds.stdout, 'w')
        self.stderr = os.fdopen(fds.stderr, 'w')

        self.env = parser.parse_data(data)

        user = self.env.get('USER', 'unknown_user')
        rip, lport, lip, mport = self.env.get(
            'SSH_CONNECTION', '0.0.0.0 0 0.0.0.0 0'
        ).split()

        con_n = next(_connection_no)

        super().__init__(
            name=(
                f'Connection #{con_n}, pid {self.pid} '
                f'({rip} -> {user}@{lip}:{mport}:{lport})'
            )
        )

        self.start()

    def print(self, *args, sep=' ', end='\n', flush=False, to_stderr=False):
        return print(
            *args,
            sep=sep, end=end, flush=flush,
            file=self.stderr if to_stderr else self.stdout
        )

    def input(self, prompt):
        self.print(prompt, end='', flush=True)
        return self.stdin.readline()

    def kill(self):
        os.kill(self.pid, signal.SIGTERM)

    def run(self):
        try:
            self.handle()
        finally:
            self.stdin.close()
            self.stdout.close()
            self.stderr.close()
            self.kill()

    def handle(self):
        raise NotImplementedError()
