"""Samsung AC Light Control integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import aiohttp
from pysmartthings import SmartThings
from pysmartthings.device import Device

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client, device_registry as dr
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.typing import ConfigType

try:
    # Newer Home Assistant raises a dedicated error when no OAuth2
    # implementation is registered; older versions raise ValueError.
    from homeassistant.helpers.config_entry_oauth2_flow import (
        ImplementationUnavailableError,
    )
except ImportError:  # pragma: no cover - depends on HA version
    ImplementationUnavailableError = ValueError

from .const import (
    CAPABILITIES_AC,
    CONF_LOCATION_ID,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class SamsungACLightData:
    """Runtime data for Samsung AC Light Control."""

    client: SmartThings
    devices: list[Device]
    location_id: str
    oauth_session: OAuth2Session

    async def async_ensure_token_valid(self) -> None:
        """Refresh the OAuth2 access token if needed and apply it to the client.

        pysmartthings binds the bearer token to the shared API service used by
        every device entity, so updating it in place keeps all cached devices
        working without re-fetching them.
        """
        await self.oauth_session.async_ensure_token_valid()
        # ``_service`` is the shared API object every device command goes through.
        self.client._service.token = self.oauth_session.token[CONF_ACCESS_TOKEN]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Samsung AC Light Control component."""
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries.

    Version 1 used a SmartThings Personal Access Token. That cannot be
    converted to OAuth2 automatically, so we bump the version and let
    ``async_setup_entry`` trigger reauthentication.
    """
    if entry.version == 1:
        hass.config_entries.async_update_entry(entry, version=2)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Samsung AC Light Control from a config entry."""
    # Entries created before the OAuth2 migration have no token and must
    # re-authenticate via the SmartThings OAuth flow.
    if CONF_TOKEN not in entry.data:
        raise ConfigEntryAuthFailed(
            "This integration now uses SmartThings OAuth. Please re-authenticate."
        )

    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except (ValueError, ImplementationUnavailableError) as err:
        raise ConfigEntryNotReady(
            "OAuth2 implementation not available; ensure application "
            "credentials are configured"
        ) from err

    oauth_session = OAuth2Session(hass, entry, implementation)

    try:
        await oauth_session.async_ensure_token_valid()
    except aiohttp.ClientResponseError as err:
        if err.status in (400, 401, 403):
            raise ConfigEntryAuthFailed from err
        raise ConfigEntryNotReady from err
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady from err

    location_id = entry.data[CONF_LOCATION_ID]
    token = oauth_session.token[CONF_ACCESS_TOKEN]

    session = aiohttp_client.async_get_clientsession(hass)
    client = SmartThings(session, token)

    try:
        # Verify connection and get devices
        devices = await client.devices(location_ids=[location_id])
        _LOGGER.info(f"Found {len(devices)} devices in location {location_id}")

        # Filter to only AC devices
        ac_devices = []
        for device in devices:
            # Check if device has AC capabilities
            if any(cap in device.capabilities for cap in CAPABILITIES_AC):
                try:
                    # Refresh device status to get current state
                    await device.status.refresh()
                    ac_devices.append(device)
                    _LOGGER.info(
                        f"Found AC device: {device.label or device.name} "
                        f"(ID: {device.device_id})"
                    )
                    _LOGGER.debug(f"Device capabilities: {device.capabilities}")
                except Exception as err:
                    _LOGGER.warning(
                        f"Could not refresh status for device {device.device_id}: {err}"
                    )

        if not ac_devices:
            _LOGGER.warning("No AC devices found in this location")
        else:
            _LOGGER.info(f"Found {len(ac_devices)} AC devices")

        # Store runtime data
        runtime_data = SamsungACLightData(
            client=client,
            devices=ac_devices,
            location_id=location_id,
            oauth_session=oauth_session,
        )
        entry.runtime_data = runtime_data

        # Register devices in device registry
        device_registry = dr.async_get(hass)
        for device in ac_devices:
            device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, device.device_id)},
                manufacturer=getattr(device, "manufacturer_name", "Samsung"),
                model=getattr(device, "model", "AC Unit"),
                name=device.label or device.name,
                sw_version=getattr(device, "firmware_version", None),
            )

        # Set up platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    except ConfigEntryAuthFailed:
        raise
    except Exception as err:
        _LOGGER.error(f"Error setting up Samsung AC Light Control: {err}")
        raise ConfigEntryNotReady from err

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
