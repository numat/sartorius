"""
A Python driver for Sartorius and Minebea Intec ethernet scales.

Distributed under the GNU General Public License v2
Copyright (C) 2019 NuMat Technologies
"""
import logging
from typing import Any

from sartorius.util import Client, SerialClient, TcpClient

logger = logging.getLogger('sartorius')


class Scale:
    """Driver for Sartorius and Minebea Intec ethernet scales.

    This implements a version of the Scale Manufacturers Association
    standardized communications protocol.
    """

    def __init__(self, address: str = '', ip: str = '', port: int = 49155,
                 **kwargs: Any) -> None:
        """Set up connection parameters, IP address and port.

        Accepts either an address string (TCP or serial), or combination
        of port & ip (TCP, backwards compatible)
        """
        if ip != '':
            if ":" in ip:
                port = int(ip.split(":")[1])
                ip = ip.split(':')[0]
                address = ip
            address = f'{ip}:{port}'
        self.units: str = ""
        if address.startswith('/dev') or address.startswith('COM'):  # serial
            self.hw: Client = SerialClient(address=address, **kwargs)
        else:
            if ':' not in address:
                address = f'{address}:{port}'
            self.hw = TcpClient(address=address, **kwargs)

    async def __aenter__(self, *args: Any) -> 'Scale':
        """Provide async enter to context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Provide async exit to context manager."""
        return

    async def get(self) -> dict:
        """Get scale reading."""
        response = await self.hw._write_and_read('\x1bP')
        if not response:
            raise OSError("Unable to get reading from scale.")
        return self._parse(response)

    async def get_info(self) -> dict:
        """Get scale model, serial, and software version numbers."""
        model = await self.hw._write_and_read('\x1bx1_')
        serial = await self.hw._write_and_read('\x1bx2_')
        software = await self.hw._write_and_read('\x1bx3_')
        if not (model and serial and software):
            raise OSError("Unable to get information from scale.")
        response = {
            'model': model.strip(),
            'serial': serial.strip(),
            'software': software.strip(),
        }
        for item in response.values():
            if (' + ' in item or ' kg' in item):
                logger.error(f"Received malformed data: {response}")
                return {}
        return response

    async def zero(self) -> None:
        """Tare and zero the scale."""
        await self.hw._write_and_read('\x1bT')

    def _parse(self, response: str) -> dict:
        """Parse a scale response.

        Scale weight is returned according to the SMA communication standard:
            K K K K K K + * A A A A A A A A * E E E CR LF
        K: ID code character
        +: plus or minus
        *: space
        A: Digit or letter
        E: unit symbol

        Errors are similar:
            S t a t * * * * * E r r * * # # * * * * CR LF
        #: Error code number
        The most common is "Stat       OFF", indicating the unit is plugged in
        but the face plate is off.

        One weird behavior is in the units field. This field is empty when the
        scale is unstable (weight shifting) but filled in when the reading is
        stable. This implementation converts that to a "stable" boolean.
        """
        if response is None:
            return {'on': False}
        elif len(response) != 22:
            logger.error(f"Received malformed data: {response}")
            return {'on': False}
        id = response[:6].strip()
        if id == 'Stat':
            error = response[9:14].strip()
            logger.warning(f'Could not read: {error}')
            return {'on': False}
        elif id == 'N':
            measurement = 'net'
        elif id == 'G':
            measurement = 'gross'
        else:
            raise ValueError("This driver only supports net/gross weight.")
        mass = float(response[6:16].replace(' ', ''))
        units = response[17:20].strip()
        if units:
            self.units = units
            stable = True
        else:
            units = self.units
            stable = False
        return {
            'mass': mass,
            'units': units,
            'stable': stable,
            'measurement': measurement,
        }
