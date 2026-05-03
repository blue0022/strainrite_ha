from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN

_TIMEOUT = aiohttp.ClientTimeout(total=10)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.0.74"): str,
    }
)


class StrainriteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            session = async_get_clientsession(self.hass)

            try:
                async with session.get(
                    f"http://{host}:{port}/backend.njs?data=values",
                    timeout=_TIMEOUT,
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                serial = data.get("serial", "")
                model = data.get("model", "Energizer")

                await self.async_set_unique_id(serial or host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Strainrite {model}",
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
