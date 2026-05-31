"""Application credentials platform for Samsung AC Light Control."""

from __future__ import annotations

from json import JSONDecodeError
import logging
from typing import cast

from aiohttp import BasicAuth, ClientError

from homeassistant.components.application_credentials import (
    AuthImplementation,
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import AbstractOAuth2Implementation

from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN

_LOGGER = logging.getLogger(__name__)


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> AbstractOAuth2Implementation:
    """Return the SmartThings OAuth2 auth implementation."""
    return SmartThingsOAuth2Implementation(
        hass,
        DOMAIN,
        credential,
        authorization_server=AuthorizationServer(
            authorize_url=OAUTH2_AUTHORIZE,
            token_url=OAUTH2_TOKEN,
        ),
    )


async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Return description placeholders for the credentials dialog."""
    return {
        "developer_console_url": "https://developer.smartthings.com/",
        "redirect_url": "https://my.home-assistant.io/redirect/oauth",
        "more_info_url": (
            "https://github.com/andrewyoung918/samsung-ac-light#configuration"
        ),
    }


class SmartThingsOAuth2Implementation(AuthImplementation):
    """OAuth2 implementation that authenticates the token request with Basic auth.

    SmartThings requires the OAuth client credentials to be sent as an HTTP
    Basic ``Authorization`` header on the token endpoint rather than in the
    request body, so the default Home Assistant implementation cannot be used
    unchanged.
    """

    async def _token_request(self, data: dict) -> dict:
        """Make a token request."""
        session = async_get_clientsession(self.hass)

        resp = await session.post(
            self.token_url,
            data=data,
            auth=BasicAuth(self.client_id, self.client_secret),
        )
        if resp.status >= 400:
            try:
                error_response = await resp.json()
            except (ClientError, JSONDecodeError):
                error_response = {}
            error_code = error_response.get("error", "unknown")
            error_description = error_response.get("error_description", "unknown error")
            _LOGGER.error(
                "Token request for %s failed (%s): %s",
                self.domain,
                error_code,
                error_description,
            )
        resp.raise_for_status()
        return cast(dict, await resp.json())
