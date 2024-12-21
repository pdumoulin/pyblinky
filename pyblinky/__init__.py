"""Interface for Belkin Wemo smart plugs."""

import re
import time
from abc import ABC

import httpx


class AbstractWemo(ABC):
    """Base abstract plug."""

    URL_TMPL = 'http://{ip}:{port}/upnp/control/basicevent1'
    HEADER_TMPL = '"urn:Belkin:service:basicevent:1#{method}{obj}"'
    BODY_TMPL = """
        <?xml version="1.0" encoding="utf-8"?>
        <s:Envelope
            xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
            s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">

            <s:Body>
                <u:{method}{obj} xmlns:u="urn:Belkin:service:basicevent:1">
                    <{obj}>{param}</{obj}>
                </u:{method}{obj}>
            </s:Body>

        </s:Envelope>
    """

    def __init__(self, ip: str, timeout: int = 3, name_cache_age: int = 0):
        """Create new plug instance.

        Args:
            ip (str): network location of plug
            timeout (int): seconds to abort request after
            name_cache_age (int): seconds to cache identify() results for
        """
        self.ip = ip
        self.timeout = timeout
        self.ports = [49153, 49152, 49154, 49151, 49155]

        self._name = ''
        self._name_cache_age = name_cache_age
        self._name_last_update = 0

    def _query_identify(self) -> bool:
        """Determine if cache should be read."""
        # caching is on and populated
        if self._name_cache_age and self._name:

            # cache value is not expired
            if time.time() - self._name_cache_age < self._name_last_update:
                return False

        return True

    def _cache_identify(self, name: str) -> None:
        self._name = name
        self._name_last_update = int(time.time())

    def _status(self, status: str) -> bool:
        if '|' in status:
            status = status.split('|')[0]
        if status in ['1', '8']:
            return True
        if status in ['0']:
            return False
        raise Exception('UnknownStatus "%s"' % status)

    def _request_params(self, method: str, obj: str, port: int, param: str) -> tuple:  # noqa:E501
        return (
            Wemo.URL_TMPL.format(ip=self.ip, port=port),
            {
                'Content-type': 'text/xml; charset="utf-8"',
                'SOAPACTION': Wemo.HEADER_TMPL.format(method=method, obj=obj)
            },
            Wemo.BODY_TMPL.format(method=method, obj=obj, param=param),
            self.timeout
        )

    def _handle_response(self, response: httpx.Response, obj: str) -> str:
        response.raise_for_status()
        match = re.search(
            f'<{obj}>(.*?)<\\/{obj}>',
            response.text
        )
        if match:
            port = int(str(response.url.port))

            # prioritize port that worked
            if self.ports[0] != port:
                self.ports.remove(port)
                self.ports.insert(0, port)
            return match.group(1)
        raise Exception('UnparsableResponse')


class Wemo(AbstractWemo):
    """Synchronous instance of plug."""

    def toggle(self) -> None:
        """Toggle plug status and return state."""
        if self.status():
            self.off()
        else:
            self.on()

    def burst(self, seconds: int) -> None:
        """Turn plug on, wait, turn off."""
        if not self.status():
            self.on()
            time.sleep(seconds)
            self.off()

    def on(self) -> bool:
        """Try turn plug on, return plug status."""
        try:
            return self._status(self._send('Set', 'BinaryState', '1'))
        except Exception:
            return self.status()

    def off(self) -> bool:
        """Try turn plug off, return plug status."""
        try:
            return self._status(self._send('Set', 'BinaryState', '0'))
        except Exception:
            return self.status()

    def status(self) -> bool:
        """Get plug status."""
        return self._status(self._send('Get', 'BinaryState'))

    def identify(self) -> str:
        """Get plug name."""
        if self._query_identify():
            self._cache_identify(self._send('Get', 'FriendlyName'))
        return self._name

    def rename(self, name: str) -> str:
        """Update plug name."""
        self._cache_identify(self._send('Change', 'FriendlyName', name))
        return self._name

    def _send(self, method: str, obj: str, param: str = '') -> str:
        for port in self.ports:
            try:
                response = self._make_request(
                    *self._request_params(
                        method,
                        obj,
                        port,
                        param
                    )
                )
            except (httpx.ConnectError, httpx.HTTPStatusError):
                pass
            else:
                return self._handle_response(response, obj)
        raise Exception('ConnectionErrorAllPorts')

    def _make_request(self, url: str, headers: dict, data: str, timeout: int) -> httpx.Response:  # noqa:E501
        return httpx.post(
            url,
            headers=headers,
            content=data,
            timeout=timeout
        )


class AsyncWemo(AbstractWemo):
    """Asyncio compatible instance of plug."""

    async def toggle(self) -> None:
        """Toggle plug status and return state."""
        if await self.status():
            await self.off()
        else:
            await self.on()

    async def burst(self, seconds: int) -> None:
        """Turn plug on, wait, turn off."""
        if not await self.status():
            await self.on()
            time.sleep(seconds)
            await self.off()

    async def on(self) -> bool:
        """Try turn plug on, return plug status."""
        try:
            return self._status(await self._send('Set', 'BinaryState', '1'))
        except Exception:
            return await self.status()

    async def off(self):
        """Try turn plug off, return plug status."""
        try:
            self._status(await self._send('Set', 'BinaryState', 0))
        except Exception:
            return await self.status()

    async def status(self) -> bool:
        """Get plug status."""
        return self._status(await self._send('Get', 'BinaryState'))

    async def identify(self) -> str:
        """Get plug name."""
        if self._query_identify():
            self._cache_identify(await self._send('Get', 'FriendlyName'))
        return self._name

    async def rename(self, name: str) -> str:
        """Update plug name."""
        self._cache_identify(await self._send('Change', 'FriendlyName', name))
        return self._name

    async def _send(self, method: str, obj: str, param: str = '') -> str:
        for port in self.ports:
            try:
                response = await self._make_request(
                    *self._request_params(
                        method,
                        obj,
                        port,
                        param
                    )
                )
            except (httpx.ConnectError, httpx.HTTPStatusError):
                pass
            else:
                return self._handle_response(response, obj)
        raise Exception('ConnectionErrorAllPorts')

    async def _make_request(self, url, headers, data, timeout):
        async with httpx.AsyncClient() as client:
            return await client.post(
                url,
                headers=headers,
                data=data,
                timeout=timeout
            )
