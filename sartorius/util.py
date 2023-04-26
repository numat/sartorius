"""Base functionality for async TCP communication.

Distributed under the GNU General Public License v2
Copyright (C) 2019 NuMat Technologies
"""

import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger('sartorius')


class TcpClient():
    """A generic reconnecting asyncio TCP client.

    This base functionality can be used by any industrial control device
    communicating over TCP.
    """

    def __init__(self, ip: str, port: int, eol: str = '\r\n'):
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
        self.connection: Dict[str, Any] = {}
        self.lock: Optional[asyncio.Lock] = None

    async def __aenter__(self) -> Any:
        """Provide async entrance to context manager.

        Contrasting synchronous access, this will connect on initialization.
        """
        await self._handle_connection()
        return self

    def __exit__(self, *args: Any) -> None:
        """Provide exit to context manager."""
        self.close()

    async def __aexit__(self, *args: Any) -> None:
        """Provide async exit to context manager."""
        self.close()

    def close(self) -> None:
        """Close the TCP connection."""
        if self.open:
            self.connection['writer'].close()
        self.open = False

    async def _connect(self) -> None:
        """Asynchronously open a TCP connection with the server."""
        self.close()
        reader, writer = await asyncio.open_connection(self.ip, self.port)
        self.connection = {'reader': reader, 'writer': writer}
        self.open = True

    async def _write_and_read(self, command: str) -> Optional[str]:
        """Write a command and read a response.

        As industrial devices are commonly unplugged, this has been expanded to
        handle recovering from disconnects.  A lock is used to queue multiple requests.
        """
        if not self.lock:
            # lock initialized here so the loop exists.
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
            await self._handle_connection()
            if self.open:
                try:
                    response = await self._handle_communication(command)
                except asyncio.exceptions.IncompleteReadError:
                    logger.error('IncompleteReadError.  Are there multiple connections?')
                    return None
            else:
                response = None
        return response

    async def _handle_connection(self) -> None:
        """Automatically maintain TCP connection."""
        try:
            if not self.open:
                await asyncio.wait_for(self._connect(), timeout=0.5)
            self.reconnecting = False
        except (asyncio.TimeoutError, OSError):
            if not self.reconnecting:
                logger.error(f'Connecting to {self.ip} timed out.')
            self.reconnecting = True

    async def _handle_communication(self, command: str) -> Optional[str]:
        """Manage communication, including timeouts and logging."""
        try:
            self.connection['writer'].write(command.encode() + self.eol)
            future = self.connection['reader'].readuntil(self.eol)
            line = await asyncio.wait_for(future, timeout=0.5)
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
