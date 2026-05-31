"""Constants for Samsung AC Light Control."""

DOMAIN = "samsung_ac_light"
CONF_LOCATION_ID = "location_id"

PLATFORMS = ["light"]

# SmartThings OAuth2 endpoints.
# Authorization happens on the regional API host while tokens are issued by the
# global auth host. Both are required by SmartThings' OAuth implementation.
OAUTH2_AUTHORIZE = "https://api.smartthings.com/oauth/authorize"
OAUTH2_TOKEN = "https://auth-global.api.smartthings.com/oauth/token"

# Scopes required to discover locations/devices and send display-light commands.
SCOPES = [
    "r:locations:*",
    "r:devices:*",
    "x:devices:*",
]

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