# Samsung AC Light Control for Home Assistant

A custom Home Assistant integration that allows you to control the display light on Samsung AC units through SmartThings API.

## Features

- Control Samsung AC display lights through Home Assistant
- Turn display lights on/off for automations and dashboards
- OAuth2 authentication with SmartThings
- Automatic device discovery for all AC units in your SmartThings account
- HACS compatible for easy installation

## Prerequisites

1. Samsung AC units connected to SmartThings
2. SmartThings account with AC devices configured
3. Home Assistant instance with HACS installed
4. SmartThings Developer Account for OAuth credentials

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on the three dots menu in the top right
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/andrewyoung/samsung-ac-light`
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

### Setting up SmartThings OAuth Application

1. Go to [SmartThings Developer Workspace](https://smartthings.developer.samsung.com/workspace)
2. Create a new project or select an existing one
3. Create a new OAuth2 app with these settings:
   - App Name: Samsung AC Light Control
   - Redirect URIs: `https://YOUR_HOME_ASSISTANT_URL/auth/external/callback`
   - Scopes: Select device read, write, and execute permissions
4. Note down your Client ID and Client Secret

### Adding the Integration

1. In Home Assistant, go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Samsung AC Light Control"
4. Follow the OAuth flow to authenticate with SmartThings
5. Your AC units will be automatically discovered

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

### No devices found
- Ensure your AC units are properly connected to SmartThings
- Check that your OAuth app has the correct permissions
- Verify the AC units appear in the SmartThings mobile app

### Display light not responding
- Check the integration logs for error messages
- Ensure the AC unit supports display light control
- Try refreshing the device status in SmartThings app

### OAuth authentication fails
- Verify your redirect URI matches exactly (including https://)
- Ensure your Home Assistant instance is accessible via HTTPS
- Check that Client ID and Secret are correct

## Development

### Project Structure
```
samsung-ac-light/
├── custom_components/
│   └── samsung_ac_light/
│       ├── __init__.py
│       ├── config_flow.py
│       ├── const.py
│       ├── light.py
│       ├── manifest.json
│       ├── strings.json
│       └── application_credentials.py
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

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/andrewyoung/samsung-ac-light/issues).