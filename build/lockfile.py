"""
Heavily modified Py-FileLock. No longer cross platform (Unix Only),
but able to create exclusive and non-exclusive locks.
"""
# copy this to /usr/local/lib/python3.6/
import fcntl
import os
import time


class Timeout(TimeoutError):
    """
    Raised when the lock could not be acquired in *timeout*
    seconds.
    """

    def __init__(self, lock_file):
        self.lock_file = lock_file
        super().__init__(
            f'File lock for "{self.lock_file}" could not be acquired.'
        )


class Lock(object):
    OPEN_MODE = os.O_RDWR | os.O_CREAT | os.O_TRUNC
    POLL_INTERVALL = 0.05

    def __init__(self, lock_file):
        self._lock_file = lock_file
        self._lock_file_fd = None
        self.is_locked = False
        self.is_exclusive = None

    def acquire(self, *, exclusive=False, timeout=-1):
        start_time = time.time()

        kind = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        operation = kind | fcntl.LOCK_NB

        while not self._acquire(operation):
            if timeout >= 0 and time.time() - start_time > timeout:
                # Timed out
                raise Timeout(self._lock_file)
            else:
                # Not acquired, sleep a bit
                time.sleep(self.POLL_INTERVALL)

        self.is_locked = True
        self.is_exclusive = exclusive

    def _acquire(self, operation):
        try:
            fd = os.open(self._lock_file, self.OPEN_MODE)
            fcntl.flock(fd, operation)
        except Exception:
            try:
                os.close(fd)
            except Exception:
                pass
            return False
        else:
            self._lock_file_fd = fd
            return True

    def release(self):
        if self.is_locked:
            fcntl.flock(self._lock_file_fd, fcntl.LOCK_UN)
            os.close(self._lock_file_fd)
            self._lock_file_fd = None
            self.is_locked = False
            self.is_exclusive = None

    def __enter__(self, *, exclusive=False, timeout=-1):
        if self.is_locked and exclusive != self.is_exclusive:
            self.release()
        if not self.is_locked:
            self.acquire(exclusive=exclusive, timeout=timeout)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def __del__(self):
        self.release()
