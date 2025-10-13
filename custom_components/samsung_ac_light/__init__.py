"""Samsung AC Light Control integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp
from pysmartthings import SmartThings
from pysmartthings.device import Device

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client, device_registry as dr
from homeassistant.helpers.typing import ConfigType

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


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Samsung AC Light Control component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Samsung AC Light Control from a config entry."""
    from homeassistant.const import CONF_ACCESS_TOKEN

    token = entry.data.get(CONF_ACCESS_TOKEN)
    if not token:
        _LOGGER.error("No access token found in config entry")
        return False

    location_id = entry.data[CONF_LOCATION_ID]

    session = aiohttp_client.async_get_clientsession(hass)
    client = SmartThings(session, token)

    try:
        # Verify connection and get devices
        devices = await client.devices(location_id=location_id)
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
        )
        entry.runtime_data = runtime_data

        # Register devices in device registry
        device_registry = dr.async_get(hass)
        for device in ac_devices:
            device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, device.device_id)},
                manufacturer=device.device_manufacturer or "Samsung",
                model=device.device_model or "AC Unit",
                name=device.label or device.name,
                sw_version=device.ocf_firmware_version,
            )

        # Set up platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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