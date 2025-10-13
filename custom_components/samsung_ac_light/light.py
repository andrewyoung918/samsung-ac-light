"""Light platform for Samsung AC Light Control."""

from __future__ import annotations

import logging
from typing import Any

from pysmartthings import Device

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SamsungACLightData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Samsung AC Light Control light platform."""
    data: SamsungACLightData = entry.runtime_data

    entities = []
    for device in data.devices:
        # Create a light entity for each AC device
        entities.append(SamsungACDisplayLight(device, entry.entry_id))
        _LOGGER.info(
            f"Creating light entity for AC: {device.label or device.name} "
            f"(ID: {device.device_id})"
        )

    if entities:
        async_add_entities(entities)
    else:
        _LOGGER.warning("No light entities created - no AC devices found")


class SamsungACDisplayLight(LightEntity):
    """Representation of a Samsung AC display light."""

    _attr_has_entity_name = True
    _attr_name = "Display Light"
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, device: Device, entry_id: str) -> None:
        """Initialize the light."""
        self._device = device
        self._entry_id = entry_id

        # Set unique ID based on device ID
        self._attr_unique_id = f"{device.device_id}_display_light"

        # Set device info for grouping
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.label or device.name,
            manufacturer=getattr(device, "manufacturer_name", "Samsung"),
            model=getattr(device, "model", "AC Unit"),
            sw_version=getattr(device, "firmware_version", None),
        )

        # Initialize state - assume display is on by default
        self._attr_is_on = True
        self._update_state_from_device()

    @callback
    def _update_state_from_device(self) -> None:
        """Update entity state from device status."""
        # Samsung AC display light state is not directly readable via status
        # We maintain the state based on commands sent
        # Default to assuming the light is on unless we've turned it off
        _LOGGER.debug(
            f"Display light for {self._device.device_id}: "
            f"{'ON' if self._attr_is_on else 'OFF'}"
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the display light."""
        _LOGGER.info(f"Turning on display light for {self._device.device_id}")

        try:
            # Note: "Light_Off" actually turns the display ON (inverted logic from Samsung)
            result = await self._device.command(
                component_id="main",
                capability="execute",
                command="execute",
                args=[
                    "mode/vs/0",
                    {"x.com.samsung.da.options": ["Light_Off"]}
                ],
            )

            if result:
                self._attr_is_on = True
                self.async_write_ha_state()
                _LOGGER.debug(f"Successfully turned on display light for {self._device.device_id}")
            else:
                _LOGGER.error(f"Failed to turn on display light for {self._device.device_id}")

        except Exception as err:
            _LOGGER.error(
                f"Error turning on display light for {self._device.device_id}: {err}"
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the display light."""
        _LOGGER.info(f"Turning off display light for {self._device.device_id}")

        try:
            # Note: "Light_On" actually turns the display OFF (inverted logic from Samsung)
            result = await self._device.command(
                component_id="main",
                capability="execute",
                command="execute",
                args=[
                    "mode/vs/0",
                    {"x.com.samsung.da.options": ["Light_On"]}
                ],
            )

            if result:
                self._attr_is_on = False
                self.async_write_ha_state()
                _LOGGER.debug(f"Successfully turned off display light for {self._device.device_id}")
            else:
                _LOGGER.error(f"Failed to turn off display light for {self._device.device_id}")

        except Exception as err:
            _LOGGER.error(
                f"Error turning off display light for {self._device.device_id}: {err}"
            )

    async def async_update(self) -> None:
        """Update the entity."""
        try:
            await self._device.status.refresh()
            self._update_state_from_device()
            _LOGGER.debug(f"Updated status for {self._device.device_id}")
        except Exception as err:
            _LOGGER.error(f"Error updating {self._device.device_id}: {err}")