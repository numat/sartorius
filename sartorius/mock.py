"""Contains mocks for driver objects for offline testing."""

import asyncio
from random import choice, random
from typing import Any
from unittest.mock import MagicMock


class Scale(MagicMock):
    """Mocks the Scale driver for offline testing."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Set up connection parameters with default scale port."""
        super().__init__(*args, **kwargs)
        self.info = {"model": "SIWADCP-1-",
                     "serial": "37454321",
                     "software": "00-37-09"}

    async def __aenter__(self, *args: Any) -> Any:
        """Set up connection."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Close connection."""
        pass

    async def get(self) -> dict:
        """Get scale reading."""
        await asyncio.sleep(random() * 0.25)
        return {'stable': True,
                'units': choice(['kg', 'lb']),
                'mass': random() * 100.0}

    async def get_info(self) -> dict:
        """Get scale model, serial, and software version numbers."""
        await asyncio.sleep(random() * 0.1)
        return self.info

    async def zero(self) -> None:
        """Tare and zero the scale."""
        await asyncio.sleep(random() * 0.1)
