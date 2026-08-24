from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=10)

# The device's embedded backend.njs endpoint is a minimal reverse-engineered
# HTTP server with no known support for concurrent connections or HTTP
# keep-alive; force a full close per request and never let two requests
# overlap, to avoid leaving unread/lingering connections on its side.
_HEADERS = {"Connection": "close"}


class StrainriteCoordinator(DataUpdateCoordinator[dict]):
    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._session = session
        self.host = host
        self.port = port
        self._request_lock = asyncio.Lock()

    def _url(self, query: str) -> str:
        return f"http://{self.host}:{self.port}/backend.njs?{query}"

    async def _async_update_data(self) -> dict:
        async with self._request_lock:
            try:
                async with self._session.get(
                    self._url("data=values"), timeout=_TIMEOUT, headers=_HEADERS
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
            except aiohttp.ClientError as err:
                raise UpdateFailed(f"Cannot reach Strainrite at {self.host}: {err}") from err
            except ValueError as err:
                raise UpdateFailed(
                    f"Strainrite at {self.host} returned unparseable data: {err}"
                ) from err

        if not data or not data.get("armed"):
            raise UpdateFailed(
                f"Strainrite at {self.host} returned incomplete data (missing 'armed' field)"
            )
        return data

    async def async_send_command(self, cmd: str) -> None:
        async with self._request_lock:
            try:
                async with self._session.get(
                    self._url(f"cmd={cmd}"), timeout=_TIMEOUT, headers=_HEADERS
                ) as resp:
                    resp.raise_for_status()
                    await resp.read()
            except aiohttp.ClientError as err:
                _LOGGER.error("Command '%s' failed: %s", cmd, err)
