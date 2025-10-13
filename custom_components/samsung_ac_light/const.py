"""Constants for Samsung AC Light Control."""

DOMAIN = "samsung_ac_light"
CONF_APP_ID = "app_id"
CONF_INSTALLED_APP_ID = "installed_app_id"
CONF_LOCATION_ID = "location_id"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_CLIENT_SECRET = "client_secret"
CONF_CLIENT_ID = "client_id"

STORAGE_KEY = f"{DOMAIN}.oauth"
STORAGE_VERSION = 1

OAUTH2_AUTHORIZE = "https://api.smartthings.com/oauth/authorize"
OAUTH2_TOKEN = "https://auth-global.api.smartthings.com/oauth/token"

DEFAULT_OAUTH2_CLIENT_ID = "your_client_id_here"
DEFAULT_OAUTH2_CLIENT_SECRET = "your_client_secret_here"

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