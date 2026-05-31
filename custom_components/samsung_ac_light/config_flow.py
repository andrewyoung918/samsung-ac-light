"""Config flow for Samsung AC Light Control (SmartThings OAuth2)."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from pysmartthings import SmartThings

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_LOCATION_ID, DOMAIN, SCOPES

_LOGGER = logging.getLogger(__name__)


class SamsungACLightConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle a config flow for Samsung AC Light Control."""

    VERSION = 2
    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data appended to the authorize URL."""
        return {"scope": " ".join(SCOPES)}

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create or update an entry once OAuth2 authorization completes."""
        token_data = data[CONF_TOKEN]

        # Ensure all requested scopes were actually granted.
        granted = set(token_data.get("scope", "").split())
        if not granted >= set(SCOPES):
            return self.async_abort(reason="missing_scopes")

        client = SmartThings(session=async_get_clientsession(self.hass))
        client.authenticate(token_data[CONF_ACCESS_TOKEN])

        try:
            locations = await client.get_locations()
        except Exception:  # noqa: BLE001 - surface any auth/network error as a flow error
            _LOGGER.exception("Error fetching SmartThings locations")
            return self.async_abort(reason="cannot_connect")

        if not locations:
            return self.async_abort(reason="no_locations")

        # Use the first location, matching the previous behaviour.
        location = locations[0]
        await self.async_set_unique_id(location.location_id)

        if self.source != SOURCE_REAUTH:
            self._abort_if_unique_id_configured()
            _LOGGER.info(
                "Successfully authenticated with location: %s", location.name
            )
            return self.async_create_entry(
                title=f"Samsung AC ({location.name})",
                data={**data, CONF_LOCATION_ID: location.location_id},
            )

        # Reauth: keep the existing entry but refresh its credentials.
        self._abort_if_unique_id_mismatch(reason="reauth_account_mismatch")
        return self.async_update_reload_and_abort(
            self._get_reauth_entry(),
            data_updates={**data, CONF_LOCATION_ID: location.location_id},
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication (including migration from token-based setups)."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauthentication."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()
