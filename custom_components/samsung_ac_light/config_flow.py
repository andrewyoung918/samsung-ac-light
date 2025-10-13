"""Config flow for Samsung AC Light Control."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from pysmartthings import SmartThings

from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client

from .const import CONF_LOCATION_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SamsungACLightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Samsung AC Light Control."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            token = user_input[CONF_ACCESS_TOKEN]

            # Validate the token by trying to get locations
            session = aiohttp_client.async_get_clientsession(self.hass)
            client = SmartThings(session, token)

            try:
                locations = await client.locations()
                if not locations:
                    errors["base"] = "no_locations"
                else:
                    # Use first location
                    location = locations[0]
                    location_id = location.location_id

                    # Check if this location is already configured
                    await self.async_set_unique_id(location_id)
                    self._abort_if_unique_id_configured()

                    _LOGGER.info(
                        f"Successfully authenticated with location: {location.name}"
                    )

                    return self.async_create_entry(
                        title=f"Samsung AC ({location.name})",
                        data={
                            CONF_ACCESS_TOKEN: token,
                            CONF_LOCATION_ID: location_id,
                        },
                    )

            except Exception as err:
                _LOGGER.error(f"Error validating token: {err}")
                errors["base"] = "invalid_auth"

        # Show the form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCESS_TOKEN): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "token_url": "https://account.smartthings.com/tokens"
            },
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_data)
