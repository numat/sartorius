"""Base functionality for async TCP communication.

Distributed under the GNU General Public License v2
Copyright (C) 2019 NuMat Technologies
"""
try:
    import asyncio
except ImportError:
    raise ImportError("TCP connections require python >=3.5.")
import logging

logger = logging.getLogger('sartorius')


class TcpClient():
    """A generic reconnecting asyncio TCP client.

    This base functionality can be used by any industrial control device
    communicating over TCP.
    """

    def __init__(self, ip, port, eol='\r\n'):
        """Set connection parameters.

        Connection is handled asynchronously, either using `async with` or
        behind the scenes on the first `await` call.
        """
        self.ip = ip
        self.port = port
        self.eol = eol.encode()
        self.open = False
        self.reconnecting = False
        self.timeouts = 0
        self.max_timeouts = 10
        self.connection = None
        self.lock = asyncio.Lock()

    def __enter__(self):
        """Provide entrance to context manager."""
        return self

    async def __aenter__(self):
        """Provide async entrance to context manager.

        Contrasting synchronous access, this will connect on initialization.
        """
        await self._connect()
        return self

    def __exit__(self, *args):
        """Provide exit to context manager."""
        self.close()

    async def __aexit__(self, *args):
        """Provide async exit to context manager."""
        self.close()

    def close(self):
        """Close the TCP connection."""
        if self.open:
            self.connection['writer'].close()
        self.open = False

    async def _connect(self):
        """Asynchronously open a TCP connection with the server."""
        self.close()
        reader, writer = await asyncio.open_connection(self.ip, self.port)
        self.connection = {'reader': reader, 'writer': writer}
        self.open = True

    async def _write_and_read(self, command):
        """Write a command and read a response.

        As industrial devices are commonly unplugged, this has been expanded to
        handle recovering from disconnects.  A lock is used to queue multiple requests.
        """
        async with self.lock:  # lock releases on CancelledError
            await self._handle_connection()
            if self.open:
                response = await self._handle_communication(command)
            else:
                response = None
        return response

    async def _handle_connection(self):
        """Automatically maintain TCP connection."""
        try:
            if not self.open:
                await asyncio.wait_for(self._connect(), timeout=0.25)
            self.reconnecting = False
        except (asyncio.TimeoutError, OSError):
            if not self.reconnecting:
                logger.error(f'Connecting to {self.ip} timed out.')
            self.reconnecting = True

    async def _handle_communication(self, command):
        """Manage communication, including timeouts and logging."""
        try:
            self.connection['writer'].write(command.encode() + self.eol)
            future = self.connection['reader'].readuntil(self.eol)
            line = await asyncio.wait_for(future, timeout=0.25)
            result = line.decode()
            self.timeouts = 0
        except (asyncio.TimeoutError, TypeError, OSError):
            self.timeouts += 1
            if self.timeouts == self.max_timeouts:
                logger.error(f'Reading from {self.ip} timed out '
                             f'{self.timeouts} times.')
                self.close()
            result = None
        return result
