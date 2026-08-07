from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=10)


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

    def _url(self, query: str) -> str:
        return f"http://{self.host}:{self.port}/backend.njs?{query}"

    async def _async_update_data(self) -> dict:
        try:
            async with self._session.get(
                self._url("data=values"), timeout=_TIMEOUT
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
        try:
            async with self._session.get(
                self._url(f"cmd={cmd}"), timeout=_TIMEOUT
            ) as resp:
                resp.raise_for_status()
        except aiohttp.ClientError as err:
            _LOGGER.error("Command '%s' failed: %s", cmd, err)
