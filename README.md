# Samsung AC Light Control for Home Assistant

A custom Home Assistant integration that allows you to control the display light on Samsung AC units through the SmartThings API.

## Features

- Control Samsung AC display lights through Home Assistant
- Turn display lights on/off for automations and dashboards
- **Secure SmartThings OAuth2 authentication** with automatic token refresh (no more short-lived Personal Access Tokens to rotate)
- Automatic device discovery for all AC units in your SmartThings account
- HACS compatible for easy installation

## Prerequisites

1. Samsung AC units connected to SmartThings
2. SmartThings account with AC devices configured
3. Home Assistant instance with HACS installed
4. A SmartThings OAuth application (Client ID + Client Secret — see below)

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on the three dots menu in the top right
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/andrewyoung918/samsung-ac-light`
5. Select "Integration" as the category
6. Click "Add"
7. Search for "Samsung AC Light Control" in HACS
8. Click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/samsung_ac_light` folder from this repository
2. Copy it to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

This integration authenticates with SmartThings using **OAuth2**. Instead of pasting a
short-lived Personal Access Token, you register a SmartThings OAuth application once and
Home Assistant keeps the access token refreshed automatically.

### Step 1: Create a SmartThings OAuth application

You can use either the [SmartThings Developer Workspace](https://developer.smartthings.com/)
or the [SmartThings CLI](https://github.com/SmartThingsCommunity/smartthings-cli).

Using the CLI:

```bash
smartthings apps:create
```

When prompted:

1. Choose **OAuth-In SmartApp**.
2. Give it a display name (e.g. "Home Assistant AC Light").
3. Set the **redirect URI** to:
   ```
   https://my.home-assistant.io/redirect/oauth
   ```
4. Grant these **scopes**:
   - `r:locations:*`
   - `r:devices:*`
   - `x:devices:*`

After creation, copy the **Client ID** and **Client Secret** — the secret is shown only once.

> The redirect URI `https://my.home-assistant.io/redirect/oauth` works for any Home
> Assistant instance via [My Home Assistant](https://my.home-assistant.io/). Make sure
> the **My Home Assistant** redirect is enabled (it is by default with `default_config`).

### Step 2: Add the OAuth credentials to Home Assistant

When you add the integration for the first time, Home Assistant will ask for the
**Client ID** and **Client Secret** from Step 1. (These are stored under
**Settings → Devices & Services → ⋮ → Application Credentials** and can be reused/edited later.)

### Step 3: Add the Integration

1. In Home Assistant, go to **Settings → Devices & Services**
2. Click **"Add Integration"**
3. Search for **"Samsung AC Light Control"**
4. Enter your **Client ID** and **Client Secret** if prompted
5. You'll be redirected to SmartThings to **authorize** the application — sign in and approve
6. Your AC units will be automatically discovered

## Upgrading from the Personal Access Token version (v1.x)

Version 2.0 replaces the Personal Access Token with SmartThings OAuth2. After updating:

1. Create a SmartThings OAuth application (Step 1 above).
2. Home Assistant will flag the existing integration for **re-authentication** — follow the
   prompt to enter your Client ID/Secret and authorize. Your existing devices and entity IDs
   are preserved.
3. If you don't see a re-auth prompt, remove and re-add the integration.

Your old Personal Access Token is no longer used and can be deleted from the SmartThings token portal.

## Usage

Once configured, each Samsung AC unit will appear as a device with a light entity for the display control.

### Entity Naming

- Device: `Samsung AC (Room Name)`
- Light Entity: `light.samsung_ac_room_name_display_light`

### Automation Example

```yaml
automation:
  - alias: "Turn off AC display at night"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: light.turn_off
        target:
          entity_id: light.samsung_ac_bedroom_display_light
```

## Supported Devices

This integration works with Samsung AC units that:
- Are connected to SmartThings
- Support the `custom.disabledComponents` capability
- Have display light control functionality

## Troubleshooting

### Authentication fails / "missing_scopes"
- Ensure your OAuth application grants all three scopes: `r:locations:*`, `r:devices:*`, `x:devices:*`
- When authorizing, approve **all** requested permissions
- Verify the redirect URI on the SmartThings app is exactly `https://my.home-assistant.io/redirect/oauth`

### "Missing configuration" / can't start the flow
- Make sure you added the Application Credentials (Client ID + Secret) — Home Assistant prompts
  for these the first time you add the integration

### No devices found
- Ensure your AC units are properly connected to SmartThings
- Verify the AC units appear in the SmartThings mobile app
- Confirm the OAuth app has the `r:devices:*` scope

### Display light not responding
- Check the integration logs for error messages
- Ensure the AC unit supports display light control
- Try refreshing the device status in SmartThings app

### Token expired
- This should no longer happen — Home Assistant automatically refreshes the OAuth token.
  If you see persistent auth failures, use the **Reconfigure / Re-authenticate** option on
  the integration to re-link your SmartThings account.

## Development

### Project Structure
```
samsung-ac-light/
├── custom_components/
│   └── samsung_ac_light/
│       ├── __init__.py
│       ├── application_credentials.py
│       ├── config_flow.py
│       ├── const.py
│       ├── light.py
│       ├── manifest.json
│       └── strings.json
├── hacs.json
└── README.md
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Debugging

Enable debug logging by adding this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.samsung_ac_light: debug
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on the official Home Assistant SmartThings integration
- Uses the pysmartthings library for API communication

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/andrewyoung918/samsung-ac-light/issues).
