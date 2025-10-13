"""Constants for Samsung AC Light Control."""

DOMAIN = "samsung_ac_light"
CONF_LOCATION_ID = "location_id"

PLATFORMS = ["light"]

# AC-related capabilities we're looking for
CAPABILITIES_AC = [
    "airConditionerMode",
    "airConditionerFanMode",
    "thermostatCoolingSetpoint",
    "thermostatHeatingSetpoint",
    "custom.airConditionerOptionalMode"
]

# Display light capabilities
CAPABILITIES_DISPLAY_LIGHT = [
    "custom.disabledComponents",
    "execute",
    "samsungce.deviceIdentification"
]