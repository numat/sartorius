"""Base functionality for async communication.

Distributed under the GNU General Public License v2
Copyright (C) 2019 NuMat Technologies
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

import serial

logger = logging.getLogger('sartorius')


class Client(ABC):
    """Base class for a generic reconnecting client."""

    def __init__(self, timeout: float) -> None:
        """Initialize the client."""
        self.eol = b'\r\n'
        self.open = False
        self.timeout = timeout
        self.max_timeouts = 10
        self.lock: Optional[asyncio.Lock] = None

    def close(self) -> None:
        """Close the connection."""
        self.open = False

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

    @abstractmethod
    async def _handle_connection(self) -> None:
        """Automatically maintain the connection."""
        ...

    @abstractmethod
    async def _handle_communication(self, command: str) -> Optional[str]:
        """Manage communication, including timeouts and logging."""
        ...


class SerialClient(Client):
    """Client using a directly-connected RS232 serial device."""

    def __init__(self, address: str, baudrate: int = 9600, timeout: float = .15,
                 bytesize: int = serial.EIGHTBITS,
                 stopbits: Union[float, int] = serial.STOPBITS_ONE,
                 parity: str = serial.PARITY_ODD):
        """Initialize serial port."""
        super().__init__(timeout)
        self.address = address
        assert type(self.address) == str
        self.serial_details = {'baudrate': baudrate,
                               'bytesize': bytesize,
                               'stopbits': stopbits,
                               'parity': parity,
                               'timeout': timeout}
        self.ser = serial.Serial(self.address, **self.serial_details)  # type: ignore [arg-type]

    def close(self) -> None:
        """Close the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()

    async def _handle_connection(self) -> None:
        """Handle the serial connection status."""
        self.open = True

    async def _handle_communication(self, command: str) -> Optional[str]:
        """Manage communication, including timeouts and logging."""
        try:
            self.ser.write(command.encode())
            # don't strip() to keep the line length == 22
            response = self.ser.readline().decode()
            self.timeouts = 0
        except (serial.SerialTimeoutException, serial.SerialException):
            self.timeouts += 1
            if self.timeouts == self.max_timeouts:
                print(f'Reading from {self.address} timed out {self.timeouts} times.')
                self.close()
            response = None
        return response


class TcpClient(Client):
    """A generic reconnecting asyncio TCP client.

    This base functionality can be used by any industrial control device
    communicating over TCP.
    """

    def __init__(self, address: str, timeout: float = 1.0):
        """Set connection parameters.

        Connection is handled asynchronously, either using `async with` or
        behind the scenes on the first `await` call.
        """
        super().__init__(timeout)
        try:
            self.address, self.port = address.split(':')
        except ValueError as e:
            raise ValueError('address must be hostname:port') from e
        self.reconnecting = False
        self.timeouts = 0
        self.connection: Dict[str, Any] = {}

    def close(self) -> None:
        """Close the TCP connection."""
        if self.open:
            self.connection['writer'].close()
        self.open = False

    async def _connect(self) -> None:
        """Asynchronously open a TCP connection with the server."""
        self.close()
        reader, writer = await asyncio.open_connection(self.address, self.port)
        self.connection = {'reader': reader, 'writer': writer}
        self.open = True

    async def _handle_connection(self) -> None:
        """Automatically maintain TCP connection."""
        try:
            if not self.open:
                await asyncio.wait_for(self._connect(), timeout=0.5)
            self.reconnecting = False
        except (asyncio.TimeoutError, OSError):
            if not self.reconnecting:
                logger.error(f'Connecting to {self.address} timed out.')
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
                logger.error(f'Reading from {self.address} timed out '
                             f'{self.timeouts} times.')
                self.close()
            result = None
        return result
