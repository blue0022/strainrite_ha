from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

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

        # Diagnostics for the recurring device-side lockup: fixed-size, in-memory
        # only (cleared on HA restart, never persisted), so this can't grow over
        # time no matter how long the integration runs.
        self._was_ok = True
        self._success_count = 0
        self._recovered_at: datetime = datetime.now(timezone.utc)
        self._last_success_kind: str | None = None
        self._last_success_body: str | None = None

    def _url(self, query: str) -> str:
        return f"http://{self.host}:{self.port}/backend.njs?{query}"

    def _note_success(self, kind: str, body: str) -> None:
        if not self._was_ok:
            self._recovered_at = datetime.now(timezone.utc)
            self._success_count = 0
            self._was_ok = True
        self._success_count += 1
        self._last_success_kind = kind
        self._last_success_body = body[:200]

    def _note_failure(self) -> None:
        if self._was_ok:
            elapsed = datetime.now(timezone.utc) - self._recovered_at
            _LOGGER.warning(
                "Strainrite at %s stopped responding after %d successful requests "
                "over %s (last recovered %s). Last successful request was %r -> %r",
                self.host,
                self._success_count,
                elapsed,
                self._recovered_at.isoformat(),
                self._last_success_kind,
                self._last_success_body,
            )
        self._was_ok = False

    async def _async_update_data(self) -> dict:
        async with self._request_lock:
            try:
                async with self._session.get(
                    self._url("data=values"), timeout=_TIMEOUT, headers=_HEADERS
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
            except aiohttp.ClientError as err:
                self._note_failure()
                raise UpdateFailed(f"Cannot reach Strainrite at {self.host}: {err}") from err
            except ValueError as err:
                self._note_failure()
                raise UpdateFailed(
                    f"Strainrite at {self.host} returned unparseable data: {err}"
                ) from err

        if not data or not data.get("armed"):
            self._note_failure()
            raise UpdateFailed(
                f"Strainrite at {self.host} returned incomplete data (missing 'armed' field)"
            )
        self._note_success("poll data=values", str(data))
        return data

    async def async_send_command(self, cmd: str) -> None:
        async with self._request_lock:
            try:
                async with self._session.get(
                    self._url(f"cmd={cmd}"), timeout=_TIMEOUT, headers=_HEADERS
                ) as resp:
                    resp.raise_for_status()
                    body = await resp.read()
            except aiohttp.ClientError as err:
                self._note_failure()
                _LOGGER.error("Command '%s' failed: %s", cmd, err)
            else:
                self._note_success(f"cmd={cmd}", body.decode(errors="replace"))
