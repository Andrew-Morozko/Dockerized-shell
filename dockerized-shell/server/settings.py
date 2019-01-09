import os


class SOCK():
    """docstring for SOCK"""
    USER = os.geteuid()  # socket owner
    GROUP = os.environ['SOCKET_GROUP']  # group that is allowed to connect to socket
    PERM = 0o770  # socket's permissions
    PATH = os.environ['SOCKET_PATH']
