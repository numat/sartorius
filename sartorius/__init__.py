"""
Python driver for Sartorius and Minebea Intec scales.

Distributed under the GNU General Public License v2
Copyright (C) 2019 NuMat Technologies
"""
from typing import Any

from sartorius.driver import Scale


def command_line(args: Any = None) -> None:
    """Command line tool exposed through package install."""
    import argparse
    import asyncio
    import json

    parser = argparse.ArgumentParser(description="Read scale status.")
    parser.add_argument('address', help="The serial or IP address of the scale.")
    parser.add_argument('-n', '--no-info', action='store_true', help="Exclude "
                        "scale information. Reduces communication overhead.")
    parser.add_argument('-z', '--zero', action='store_true', help="Tares and "
                        "zeroes the scale.")
    args = parser.parse_args(args)

    async def get() -> None:
        async with Scale(address=args.address) as scale:
            if args.zero:
                await scale.zero()
            d = await scale.get()
            if not args.no_info and d.get('on', True):
                d['info'] = await scale.get_info()
            print(json.dumps(d, indent=4))
    asyncio.run(get())


if __name__ == '__main__':
    command_line()
