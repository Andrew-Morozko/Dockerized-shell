import os
from handlers import ThreadedHandler, server_socket
from parser import MAX_DATA_SIZE, ANCDATA_SIZE


class Handler(ThreadedHandler):
    def handle(self):
        print(self.name)

        print('Got env, creds and fds from shell:')
        print(f'pid={self.pid}, uid={self.uid}, gid={self.gid}')
        print(
            f'stdin={self.stdin.fileno()}, '
            f'stdout={self.stdout.fileno()}, '
            f'stderr={self.stderr.fileno()}'
        )
        print('env:')
        print(self.env)

        self.print('This came from server. Put some menues here')
        usr_input = self.input('Cool? [yes/no]: ').strip().lower()

        if usr_input == 'yes':
            self.print("That's what i'm talking about!")
        else:
            self.print(":(")

        print('Attaching shell to docker...')  # TODO: connect to docker, attach container

        self.print("Disconnecting")


def main():
    with server_socket('/home/test/unix_socket', 0o770, 'root', 'test') as sock:
        print('Server initialized, waiting for connections...')
        while True:
            data, ancdata, _, _ = sock.recvmsg(MAX_DATA_SIZE, ANCDATA_SIZE)
            Handler(data, ancdata)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Server exiting...')
