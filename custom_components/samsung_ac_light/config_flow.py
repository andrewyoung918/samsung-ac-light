"""Config flow for Samsung AC Light Control."""

from __future__ import annotations

import logging
from typing import Any

from pysmartthings import SmartThings

from homeassistant import config_entries
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.const import CONF_TOKEN
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow

from .const import (
    CONF_LOCATION_ID,
    DEFAULT_OAUTH2_CLIENT_ID,
    DEFAULT_OAUTH2_CLIENT_SECRET,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)

_LOGGER = logging.getLogger(__name__)


class SamsungACLightOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle Samsung AC Light Control OAuth2 config flow."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data to add to authorization request."""
        return {
            "scope": "r:devices:* w:devices:* x:devices:*",
        }

    async def async_step_import(self, data: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user()

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Create an entry for the flow."""
        token = data[CONF_TOKEN]

        # Get SmartThings client to verify and get location
        session = aiohttp_client.async_get_clientsession(self.hass)
        client = SmartThings(session, token["access_token"])

        try:
            # Get locations to verify token
            locations = await client.locations()
            if not locations:
                return self.async_abort(reason="no_locations")

            # Use first location
            location = locations[0]
            location_id = location.location_id

            _LOGGER.info(f"Successfully authenticated with location: {location.name}")

        except Exception as err:
            _LOGGER.error(f"Error validating token: {err}")
            return self.async_abort(reason="invalid_auth")

        # Check if this location is already configured
        await self.async_set_unique_id(location_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Samsung AC ({location.name})",
            data={
                **data,
                CONF_LOCATION_ID: location_id,
            },
        )


class SamsungACLightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Samsung AC Light Control."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        # Import client credentials if not already done
        if DOMAIN not in self.hass.data.get("application_credentials", {}):
            await async_import_client_credential(
                self.hass,
                DOMAIN,
                ClientCredential(
                    DEFAULT_OAUTH2_CLIENT_ID,
                    DEFAULT_OAUTH2_CLIENT_SECRET,
                ),
            )

        return await self.async_step_pick_implementation()

    async_step_pick_implementation = (
        config_entry_oauth2_flow.async_step_pick_implementation
    )