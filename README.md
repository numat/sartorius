sartorius
=========

Asynchronous python ethernet interface and command-line tool for Sartorius and
Minebea Intec scales.

![](https://www.dataweigh.com/media/11870/signum1.jpg)

Compatibility
=============

This driver should work for any ethernet scale that uses the standardized communications
protocol of the Scale Manufacturers Association. However, it has only been tested
on the following models:

 * Minebea Intec Signum
 * Sartorius Entris
 * Sartorius Miras

Installation
============

```
pip install sartorius
```

Scale Setup
===========

For Minebea scale setup, navigate to `SETUP` - `UNICOM` - `DATAPROT` - `ETHER`.

  * Make sure `SRC.IP` is set to a valid LAN address
  * Ensure `MODE` - `SBI-SRV` - `6.1.1` is set (manual says this should be default but it is not)
  * All other defaults are good

This driver is intended to be stable to disconnects, so operators should be
able to unplug and reposition the device without affecting any long polling.

Command Line
============

```
$ sartorius scale-ip.local
{
    "mass": 0.0,
    "units": "kg",
    "stable": true,
    "info": {
        "model": "SIWADCP-1-",
        "serial": "37454321",
        "software": "00-37-09"
    }
}
```
If using a port other than the default of 49155 e.g. for a MODBUS gateway, use `--port`
or a colon between the IP address and port.
`sartorius 192.168.1.1 --port 10000` or `sartorius 192.168.1.1:12345`

You can tare and zero with `--zero` and remove the info field with `--no-info`.
See `sartorius --help` for more.

To use in shell scripts, parse the json output with something like
[jq](https://stedolan.github.io/jq/). For example,
`sartorius scale-ip.local | jq .mass` will return the mass.

Python
======

If you'd like to link this to more complex behavior, consider using a Python
script. This driver exclusively supports asynchronous Python ≥3.7.

```python
import asyncio
import sartorius

async def get():
    async with sartorius.Scale('scale-ip.local') as scale:
        await scale.zero()             # Zero and tare the scale
        print(await scale.get())       # Get mass, units, stability
        print(await scale.get_info())  # Get model, serial, software version

asyncio.run(get())
```
