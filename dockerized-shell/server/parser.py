"""Sans-io parser for received message form console"""

import os
import socket
import signal
from struct import Struct
from collections import namedtuple

Fds = namedtuple('Fds', 'stdin stdout stderr')
_FDS_STRUCTURE = Struct('i' * 3)
Creds = namedtuple('Creds', 'pid uid gid')
_CREDS_STRUCTURE = Struct('i' * 3)

ANCDATA_SIZE = (
    socket.CMSG_SPACE(_FDS_STRUCTURE.size) +
    socket.CMSG_SPACE(_CREDS_STRUCTURE.size)
)
MAX_DATA_SIZE = 8192  # Arbitrary chosen big number


class ParsingError(Exception):
    pass


def parse_data(data):
    data = data.decode('ascii')
    if data[-1] != '\0':
        raise ParsingError(
            'Unexpected env ending, check that whole message was received'
        )

    env = {}
    try:
        for name_val in data[:-1].split('\0'):
            name, val = name_val.split('=', maxsplit=1)
            env[name] = val
    except ValueError:
        # Unpacking failed, split didn't happen
        raise ParsingError(
            f'"=" not found in environment variable: {name_val!r}'
        )

    return env


def parse_ancdata(ancdata):
    righs, creds = None, None
    for cmsg_level, cmsg_type, cmsg_data in ancdata:
        if cmsg_level == socket.SOL_SOCKET:
            if cmsg_type == socket.SCM_RIGHTS:
                righs = _FDS_STRUCTURE.unpack(cmsg_data)
            elif cmsg_type == socket.SCM_CREDENTIALS:
                creds = _CREDS_STRUCTURE.unpack(cmsg_data)
    if not (righs and creds):
        raise ParsingError(
            f'Ancdata parsing failed, '
            f'file descriptors: {"parsed" if righs else "not parsed"}, '
            f'pid, uid, gid: {"parsed" if creds else "not parsed"}'
        )

    return Creds(*creds), Fds(*righs)
