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
            manufacturer=device.device_manufacturer or "Samsung",
            model=device.device_model or "AC Unit",
            sw_version=device.ocf_firmware_version,
        )

        # Initialize state
        self._attr_is_on = False
        self._update_state_from_device()

    @callback
    def _update_state_from_device(self) -> None:
        """Update entity state from device status."""
        # Check for display light control in custom.disabledComponents
        if "custom.disabledComponents" in self._device.status.attributes:
            disabled = self._device.status.attributes.get("custom.disabledComponents", {})
            components = disabled.get("disabledComponents", {}).get("value", [])
            # If "display" is in disabled components, the light is off
            self._attr_is_on = "display" not in components
            _LOGGER.debug(
                f"Display light for {self._device.device_id}: "
                f"{'ON' if self._attr_is_on else 'OFF'} "
                f"(disabled components: {components})"
            )
        else:
            # Fallback: Check if the device has any display-related capability
            # This might need adjustment based on your specific AC model
            _LOGGER.debug(
                f"No custom.disabledComponents found for {self._device.device_id}, "
                f"checking other capabilities"
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the display light."""
        _LOGGER.info(f"Turning on display light for {self._device.device_id}")

        try:
            # Remove "display" from disabled components to turn on the light
            result = await self._device.command(
                component_id="main",
                capability="custom.disabledComponents",
                command="setDisabledComponents",
                args=[[]],  # Empty array means no components are disabled
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
            # Add "display" to disabled components to turn off the light
            result = await self._device.command(
                component_id="main",
                capability="custom.disabledComponents",
                command="setDisabledComponents",
                args=[["display"]],  # Disable the display component
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