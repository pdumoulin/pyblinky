# pyblinky

Control Belkin brand Wemo smart plugs synchronously or asynchronously.

## Install

Install from [pypi.org](https://pypi.org/project/pyblinky/)

```bash
pip install pyblinky
```


## Options

| Parameter | Default | Description |
| --- | --- | --- |
| ip | _Required_ | Network location of plug[^1] |
| timeout | 3 | Seconds to wait for response |
| name_cache_age | 0 | Seconds to store plug name before re-querying it |

## Actions

| Action | Parameters | Description |
| --- | --- | --- |
| on | _None_ | Turn plug on |
| off | _None_ | Turn plug off |
| toggle | _None_ | Change plug status |
| burst | seconds | Turn on plug, wait num seconds, then turn off |
| status | _None_ | Get status of plug as (bool) |
| identify | _None_ | Get name of plug (str) |
| rename | name | Rename plug |

A more thorough list of available actions on the plug is documented [here](https://gist.github.com/nstarke/018cd98d862afe0a7cda17bc20f31a1e) and some may be implemented here in the future.

## Examples

### Synchronous

```python
from pyblinky import Wemo

plug = Wemo('192.168.1.87')
print(plug.status())
print(plug.identify())
plug.on()
```


### Asynchronous

```python
import asyncio

from pyblinky import AsyncWemo

plugs = [
	AsyncWemo('192.168.1.87'),
	AsyncWemo('192.168.1.88'),
	AsyncWemo('192.168.1.89')
]

async def main():
    result = await asyncio.gather(
        *(
            [
                x.status()
                for x in plugs
            ] +
            [
                y.identify()
                for y in plugs
            ]
        )
    )
    print(result)

if __name__ == '__main__':
    asyncio.run(main())
```

[^1]: This project does not implement [UPnP](https://en.wikipedia.org/wiki/Universal_Plug_and_Play) interface for device discovery, instead talking to plugs directly by IP address. It is highly recommended to set static IPs for plugs. Discovery may be added at a later date if a suitable library can be found.
