import asyncio
from random import random, choice
from unittest.mock import MagicMock


class Scale(MagicMock):
    """Mocks the Sartorius Scale for offline testing."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.info = {"model": "SIWADCP-1-",
                     "serial": "37454321",
                     "software": "00-37-09"}

    async def __aenter__(self, *args):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self):
        await asyncio.sleep(random() * 0.25)
        return {'stable': True,
                'units': choice(['kg', 'lb']),
                'mass': random() * 100.0}

    async def get_info(self):
        await asyncio.sleep(random() * 0.1)
        return self.info

    async def zero(self):
        await asyncio.sleep(random() * 0.1)
