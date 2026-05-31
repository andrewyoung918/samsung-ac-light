"""Samsung AC Light Control integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import aiohttp
from pysmartthings import Device, SmartThings

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

from .const import (
    CAPABILITIES_AC,
    CONF_LOCATION_ID,
    DOMAIN,
    PLATFORMS,
)

try:
    # Newer Home Assistant raises a dedicated error when no OAuth2
    # implementation is registered; older versions raise ValueError.
    from homeassistant.helpers.config_entry_oauth2_flow import (
        ImplementationUnavailableError,
    )
except ImportError:  # pragma: no cover - depends on HA version
    ImplementationUnavailableError = ValueError

_LOGGER = logging.getLogger(__name__)

MAIN = "main"


@dataclass
class SamsungACLightData:
    """Runtime data for Samsung AC Light Control."""

    client: SmartThings
    devices: list[Device]
    location_id: str


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

    # Build the SmartThings client. ``refresh_token_function`` is invoked by
    # pysmartthings before every request, so the OAuth access token is always
    # kept valid (and refreshed) automatically.
    session = aiohttp_client.async_get_clientsession(hass)
    client = SmartThings(session=session)
    client.authenticate(oauth_session.token[CONF_ACCESS_TOKEN])

    async def _refresh_token() -> str:
        await oauth_session.async_ensure_token_valid()
        return oauth_session.token[CONF_ACCESS_TOKEN]

    client.refresh_token_function = _refresh_token

    try:
        devices = await client.get_devices(location_ids=[location_id])
    except aiohttp.ClientResponseError as err:
        if err.status in (401, 403):
            raise ConfigEntryAuthFailed from err
        raise ConfigEntryNotReady from err
    except (aiohttp.ClientError, TimeoutError) as err:
        raise ConfigEntryNotReady from err

    _LOGGER.info("Found %d devices in location %s", len(devices), location_id)

    # Filter to only AC devices based on their "main" component capabilities.
    ac_devices: list[Device] = []
    for device in devices:
        main_component = device.components.get(MAIN)
        if main_component is None:
            continue
        # Capability entries may be ``Capability`` (str-based) enums or plain
        # strings; both compare/hash as their string id, so a raw set works.
        capabilities = set(main_component.capabilities)
        if any(cap in capabilities for cap in CAPABILITIES_AC):
            ac_devices.append(device)
            _LOGGER.info(
                "Found AC device: %s (ID: %s)",
                device.label or device.name,
                device.device_id,
            )

    if not ac_devices:
        _LOGGER.warning("No AC devices found in this location")
    else:
        _LOGGER.info("Found %d AC devices", len(ac_devices))

    entry.runtime_data = SamsungACLightData(
        client=client,
        devices=ac_devices,
        location_id=location_id,
    )

    # Register devices in the device registry.
    device_registry = dr.async_get(hass)
    for device in ac_devices:
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, device.device_id)},
            manufacturer="Samsung",
            model="AC Unit",
            name=device.label or device.name,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
