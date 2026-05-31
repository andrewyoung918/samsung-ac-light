"""Light platform for Samsung AC Light Control."""

from __future__ import annotations

import logging
from typing import Any

from pysmartthings import Capability, Command, Device

from homeassistant.components.light import (
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SamsungACLightData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Samsung's display-light control uses the raw "execute" capability against the
# vendor data path. Note the inverted semantics: "Light_Off" turns the physical
# display ON, and "Light_On" turns it OFF.
EXECUTE_PATH = "mode/vs/0"
DISPLAY_ON_ARGUMENT = [EXECUTE_PATH, {"x.com.samsung.da.options": ["Light_Off"]}]
DISPLAY_OFF_ARGUMENT = [EXECUTE_PATH, {"x.com.samsung.da.options": ["Light_On"]}]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Samsung AC Light Control light platform."""
    data: SamsungACLightData = entry.runtime_data

    entities = []
    for device in data.devices:
        entities.append(SamsungACDisplayLight(data, device, entry.entry_id))
        _LOGGER.info(
            "Creating light entity for AC: %s (ID: %s)",
            device.label or device.name,
            device.device_id,
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
    # The display-light state cannot be read back from SmartThings, so we track
    # it locally based on the commands we send rather than polling.
    _attr_should_poll = False

    def __init__(
        self, data: SamsungACLightData, device: Device, entry_id: str
    ) -> None:
        """Initialize the light."""
        self._data = data
        self._device = device
        self._entry_id = entry_id

        self._attr_unique_id = f"{device.device_id}_display_light"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.label or device.name,
            manufacturer="Samsung",
            model="AC Unit",
        )

        # Assume the display is on until we turn it off.
        self._attr_is_on = True

    @property
    def _client(self):
        """Return the shared SmartThings client."""
        return self._data.client

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the display light."""
        _LOGGER.info("Turning on display light for %s", self._device.device_id)
        try:
            await self._client.execute_device_command(
                self._device.device_id,
                Capability.EXECUTE,
                Command.EXECUTE,
                argument=DISPLAY_ON_ARGUMENT,
            )
        except Exception as err:  # noqa: BLE001 - surface any command failure
            _LOGGER.error(
                "Error turning on display light for %s: %s",
                self._device.device_id,
                err,
            )
            return

        self._attr_is_on = True
        self.async_write_ha_state()
        _LOGGER.debug(
            "Successfully turned on display light for %s", self._device.device_id
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the display light."""
        _LOGGER.info("Turning off display light for %s", self._device.device_id)
        try:
            await self._client.execute_device_command(
                self._device.device_id,
                Capability.EXECUTE,
                Command.EXECUTE,
                argument=DISPLAY_OFF_ARGUMENT,
            )
        except Exception as err:  # noqa: BLE001 - surface any command failure
            _LOGGER.error(
                "Error turning off display light for %s: %s",
                self._device.device_id,
                err,
            )
            return

        self._attr_is_on = False
        self.async_write_ha_state()
        _LOGGER.debug(
            "Successfully turned off display light for %s", self._device.device_id
        )
